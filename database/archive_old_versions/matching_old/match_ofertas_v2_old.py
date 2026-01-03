# -*- coding: utf-8 -*-
"""
Matching ESCO v2.0 - Pipeline en cascada con variables NLP v10
==============================================================

Usa todas las variables del NLP Schema v5 para matching preciso.
Configuracion 100% en JSON, sin hardcodeado.

Autor: MOL Team
Fecha: 2025-12-10
"""

import json
import sqlite3
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"


# ============================================================================
# ESTRUCTURAS DE DATOS
# ============================================================================

class MatchStatus(Enum):
    SUCCESS = "success"
    FILTERED = "filtered"
    NO_MATCH = "no_match"
    BYPASS = "bypass"


@dataclass
class MatchResult:
    """Resultado estructurado del matching."""
    status: str
    esco_uri: Optional[str]
    esco_label: Optional[str]
    isco_code: Optional[str]
    score: float
    score_components: Dict[str, Any]
    nivel_match: int
    metodo: str
    candidatos_considerados: int
    alternativas: List[Dict]
    metadata: Dict

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# CARGA DE CONFIGURACION
# ============================================================================

def load_json_config(filepath: Path) -> Dict:
    """Carga un archivo JSON de configuracion."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config no encontrado: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando {filepath}: {e}")
        return {}


def load_all_configs() -> Dict:
    """Carga todos los archivos de configuracion."""
    return {
        "matching": load_json_config(CONFIG_DIR / "matching_config.json"),
        "area_map": load_json_config(CONFIG_DIR / "area_funcional_esco_map.json"),
        "seniority_map": load_json_config(CONFIG_DIR / "nivel_seniority_esco_map.json"),
        "sector_compat": load_json_config(CONFIG_DIR / "sector_isco_compatibilidad.json")
    }


# ============================================================================
# NIVEL 0: FILTRO DE VALIDEZ
# ============================================================================

def nivel_0_filtro_validez(oferta_nlp: Dict, config: Dict) -> Tuple[bool, str]:
    """
    Verifica si la oferta es valida para matching.

    Returns:
        (es_valida, razon_rechazo)
    """
    filtros = config.get("matching", {}).get("filtros", {})

    # Verificar tipo_oferta
    tipo_oferta = oferta_nlp.get("tipo_oferta")
    tipos_validos = filtros.get("tipo_oferta_validos", ["demanda_real"])

    if tipo_oferta and tipo_oferta not in tipos_validos:
        return False, f"tipo_oferta_invalido: {tipo_oferta}"

    # Verificar calidad_texto
    calidad = oferta_nlp.get("calidad_texto")
    calidades_validas = filtros.get("calidad_texto_minima", ["alta", "media", "baja"])

    if calidad and calidad == "muy_baja":
        return False, f"calidad_texto_baja: {calidad}"

    return True, ""


# ============================================================================
# NIVEL 1: BYPASS DICCIONARIO ARGENTINO
# ============================================================================

def nivel_1_bypass_diccionario(
    titulo_limpio: str,
    config: Dict,
    db_conn: sqlite3.Connection
) -> Optional[Dict]:
    """
    Busca match directo en diccionario argentino.

    Returns:
        Dict con esco_uri y score si hay match, None si no.
    """
    bypass_config = config.get("matching", {}).get("bypass_diccionario", {})

    if not bypass_config.get("habilitado", True):
        return None

    if not titulo_limpio:
        return None

    tabla = bypass_config.get("tabla", "diccionario_arg_esco")

    # Verificar si la tabla existe
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (tabla,))

    if not cursor.fetchone():
        logger.debug(f"Tabla {tabla} no existe, saltando bypass")
        return None

    # Busqueda exacta - usar columnas reales de diccionario_arg_esco
    try:
        cursor.execute(f"""
            SELECT isco_target, esco_preferred_label
            FROM {tabla}
            WHERE LOWER(termino_argentino) = LOWER(?)
        """, (titulo_limpio,))

        row = cursor.fetchone()
        if row:
            isco_code = row[0]
            esco_label = row[1]
            # Buscar URI de la ocupacion en esco_occupations
            cursor.execute("""
                SELECT occupation_uri FROM esco_occupations
                WHERE isco_code = ? LIMIT 1
            """, (isco_code,))
            uri_row = cursor.fetchone()
            esco_uri = uri_row[0] if uri_row else None

            return {
                "esco_uri": esco_uri,
                "esco_label": esco_label,
                "isco_code": isco_code,
                "score": bypass_config.get("score_asignado", 0.99),
                "metodo": "diccionario_exacto"
            }
    except sqlite3.OperationalError as e:
        logger.debug(f"Error en busqueda diccionario: {e}")

    # Busqueda fuzzy si esta habilitada
    if bypass_config.get("usar_fuzzy", True):
        try:
            from rapidfuzz import fuzz

            cursor.execute(f"SELECT termino_argentino, isco_target, esco_preferred_label FROM {tabla}")

            mejor_match = None
            mejor_score = 0
            umbral = bypass_config.get("umbral_fuzzy", 0.85)

            for row in cursor:
                termino, isco, label = row
                ratio = fuzz.ratio(titulo_limpio.lower(), termino.lower()) / 100
                if ratio > mejor_score and ratio >= umbral:
                    mejor_score = ratio
                    mejor_match = {"isco": isco, "label": label}

            if mejor_match:
                # Buscar URI de la ocupacion en esco_occupations
                cursor.execute("""
                    SELECT occupation_uri FROM esco_occupations
                    WHERE isco_code = ? LIMIT 1
                """, (mejor_match["isco"],))
                uri_row = cursor.fetchone()
                esco_uri = uri_row[0] if uri_row else None

                return {
                    "esco_uri": esco_uri,
                    "esco_label": mejor_match["label"],
                    "isco_code": mejor_match["isco"],
                    "score": bypass_config.get("score_asignado", 0.99) * mejor_score,
                    "metodo": "diccionario_fuzzy"
                }
        except ImportError:
            logger.debug("rapidfuzz no disponible, saltando fuzzy")
        except Exception as e:
            logger.debug(f"Error en fuzzy: {e}")

    return None


# ============================================================================
# NIVEL 2: FILTRADO POR CONTEXTO
# ============================================================================

def nivel_2_filtrar_por_contexto(
    candidatos: List[Dict],
    oferta_nlp: Dict,
    config: Dict
) -> List[Dict]:
    """
    Filtra candidatos ESCO basandose en contexto NLP.
    """
    filtros = config.get("matching", {}).get("filtros", {})
    area_map = config.get("area_map", {}).get("mappings", {})
    seniority_map = config.get("seniority_map", {}).get("mappings", {})

    resultado = candidatos.copy()

    # Filtrar por area_funcional
    if filtros.get("usar_filtro_area", True):
        area = oferta_nlp.get("area_funcional")
        if area and area in area_map:
            mapeo = area_map[area]
            isco_primarios = set(mapeo.get("isco_primarios", []))
            isco_secundarios = set(mapeo.get("isco_secundarios", []))
            isco_validos = isco_primarios | isco_secundarios
            isco_excluir = set(mapeo.get("excluir", []))

            if isco_validos:
                resultado_filtrado = []
                for c in resultado:
                    isco = c.get("isco_code", "")
                    # Verificar si coincide con alguno de los ISCO validos
                    coincide = any(isco.startswith(i) for i in isco_validos)
                    excluido = any(isco.startswith(ex) for ex in isco_excluir)
                    if coincide and not excluido:
                        resultado_filtrado.append(c)

                # Solo usar filtro si no deja vacio
                if resultado_filtrado:
                    resultado = resultado_filtrado

    # Filtrar por nivel_seniority
    if filtros.get("usar_filtro_seniority", True):
        seniority = oferta_nlp.get("nivel_seniority")
        if seniority and seniority in seniority_map:
            mapeo = seniority_map[seniority]
            isco_permitir = set(mapeo.get("permitir", []))
            isco_excluir = set(mapeo.get("excluir", []))

            resultado_filtrado = []
            for c in resultado:
                isco = c.get("isco_code", "")
                permitido = any(isco.startswith(p) for p in isco_permitir) if isco_permitir else True
                excluido = any(isco.startswith(ex) for ex in isco_excluir)
                if permitido and not excluido:
                    resultado_filtrado.append(c)

            if resultado_filtrado:
                resultado = resultado_filtrado

    # Filtrar por tiene_gente_cargo
    if filtros.get("usar_filtro_supervision", True):
        tiene_gente = oferta_nlp.get("tiene_gente_cargo")
        if tiene_gente is False:
            # Excluir alta direccion
            resultado_filtrado = [
                c for c in resultado
                if not c.get("isco_code", "").startswith("11")
                and not c.get("isco_code", "").startswith("12")
            ]
            if resultado_filtrado:
                resultado = resultado_filtrado

    return resultado


# ============================================================================
# NIVEL 3: SCORING MULTICRITERIO
# ============================================================================

def calcular_pesos_dinamicos(oferta_nlp: Dict, config: Dict) -> Dict[str, float]:
    """Calcula pesos dinamicos segun riqueza de datos."""
    pesos_base = config.get("matching", {}).get("pesos_base", {
        "titulo": 0.40, "tareas": 0.30, "skills": 0.20, "descripcion": 0.10
    })
    pesos_dinamicos = config.get("matching", {}).get("pesos_dinamicos", {})

    # Parse JSON lists
    tareas = oferta_nlp.get("tareas_explicitas") or []
    if isinstance(tareas, str):
        try:
            tareas = json.loads(tareas)
        except:
            tareas = []

    tecnologias = oferta_nlp.get("tecnologias_list") or []
    if isinstance(tecnologias, str):
        try:
            tecnologias = json.loads(tecnologias)
        except:
            tecnologias = []

    skills_tec = oferta_nlp.get("skills_tecnicas_list") or []
    if isinstance(skills_tec, str):
        try:
            skills_tec = json.loads(skills_tec)
        except:
            skills_tec = []

    # Evaluar condiciones en orden de prioridad
    if len(tareas) >= 3 and len(tecnologias) + len(skills_tec) >= 3:
        return pesos_dinamicos.get("datos_completos", {}).get("pesos", pesos_base)

    if len(tareas) >= 3:
        return pesos_dinamicos.get("tareas_ricas", {}).get("pesos", pesos_base)

    if len(tecnologias) + len(skills_tec) >= 5:
        return pesos_dinamicos.get("skills_ricas", {}).get("pesos", pesos_base)

    if len(tareas) == 0 and len(skills_tec) == 0:
        return pesos_dinamicos.get("solo_titulo", {}).get("pesos", pesos_base)

    return pesos_base


def calcular_similitud_titulo(titulo_oferta: str, esco_label: str) -> float:
    """Calcula similitud entre titulo de oferta y label ESCO."""
    if not titulo_oferta or not esco_label:
        return 0.0

    try:
        from rapidfuzz import fuzz
        return fuzz.ratio(titulo_oferta.lower(), esco_label.lower()) / 100
    except ImportError:
        # Fallback simple
        words_oferta = set(titulo_oferta.lower().split())
        words_esco = set(esco_label.lower().split())
        if not words_oferta or not words_esco:
            return 0.0
        interseccion = len(words_oferta & words_esco)
        union = len(words_oferta | words_esco)
        return interseccion / union if union > 0 else 0.0


def calcular_overlap_listas(lista_a: List[str], lista_b: List[str]) -> float:
    """Calcula Jaccard overlap entre dos listas."""
    if not lista_a or not lista_b:
        return 0.0

    # Parse si son strings JSON
    if isinstance(lista_a, str):
        try:
            lista_a = json.loads(lista_a)
        except:
            lista_a = []

    if isinstance(lista_b, str):
        try:
            lista_b = json.loads(lista_b)
        except:
            lista_b = []

    if not lista_a or not lista_b:
        return 0.0

    set_a = set(item.lower() for item in lista_a if item)
    set_b = set(item.lower() for item in lista_b if item)

    interseccion = len(set_a & set_b)
    union = len(set_a | set_b)

    return interseccion / union if union > 0 else 0.0


def nivel_3_scoring(
    candidatos: List[Dict],
    oferta_nlp: Dict,
    config: Dict
) -> List[Tuple[Dict, float, Dict]]:
    """
    Calcula scores para cada candidato.

    Returns:
        Lista de (candidato, score_total, score_components)
    """
    pesos = calcular_pesos_dinamicos(oferta_nlp, config)

    titulo = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo") or ""

    # Parse listas
    tareas = oferta_nlp.get("tareas_explicitas") or []
    if isinstance(tareas, str):
        try:
            tareas = json.loads(tareas)
        except:
            tareas = []

    tecnologias = oferta_nlp.get("tecnologias_list") or []
    if isinstance(tecnologias, str):
        try:
            tecnologias = json.loads(tecnologias)
        except:
            tecnologias = []

    skills_tec = oferta_nlp.get("skills_tecnicas_list") or []
    if isinstance(skills_tec, str):
        try:
            skills_tec = json.loads(skills_tec)
        except:
            skills_tec = []

    skills = tecnologias + skills_tec
    mision = oferta_nlp.get("mision_rol") or ""

    resultados = []

    for candidato in candidatos:
        # Score por titulo
        esco_label = candidato.get("label") or candidato.get("esco_label") or ""
        score_titulo = calcular_similitud_titulo(titulo, esco_label)

        # Score por tareas
        esco_tasks = candidato.get("tasks") or []
        if isinstance(esco_tasks, str):
            try:
                esco_tasks = json.loads(esco_tasks)
            except:
                esco_tasks = []
        score_tareas = calcular_overlap_listas(tareas, esco_tasks)

        # Score por skills
        esco_skills = candidato.get("skills") or []
        if isinstance(esco_skills, str):
            try:
                esco_skills = json.loads(esco_skills)
            except:
                esco_skills = []
        score_skills = calcular_overlap_listas(skills, esco_skills)

        # Score por descripcion
        esco_desc = candidato.get("description") or ""
        score_desc = calcular_similitud_titulo(mision, esco_desc) if mision else 0.0

        # Score total ponderado
        peso_titulo = pesos.get("titulo", 0.40)
        peso_tareas = pesos.get("tareas", 0.30)
        peso_skills = pesos.get("skills", 0.20)
        peso_desc = pesos.get("descripcion", 0.10)

        score_total = (
            peso_titulo * score_titulo +
            peso_tareas * score_tareas +
            peso_skills * score_skills +
            peso_desc * score_desc
        )

        score_components = {
            "titulo": round(score_titulo, 4),
            "tareas": round(score_tareas, 4),
            "skills": round(score_skills, 4),
            "descripcion": round(score_desc, 4),
            "pesos_usados": pesos
        }

        resultados.append((candidato, score_total, score_components))

    # Ordenar por score descendente
    resultados.sort(key=lambda x: x[1], reverse=True)

    return resultados[:5]  # Top 5


# ============================================================================
# NIVEL 4: AJUSTES FINALES
# ============================================================================

def nivel_4_ajustes(
    top_candidatos: List[Tuple[Dict, float, Dict]],
    oferta_nlp: Dict,
    config: Dict
) -> List[Tuple[Dict, float, Dict]]:
    """Aplica penalizaciones y boosts al score."""
    penalizaciones = config.get("matching", {}).get("penalizaciones", {})
    boosts = config.get("matching", {}).get("boosts", {})
    seniority_map = config.get("seniority_map", {})
    sector_compat = config.get("sector_compat", {})

    seniority = oferta_nlp.get("nivel_seniority")
    tiene_gente = oferta_nlp.get("tiene_gente_cargo")
    sector = oferta_nlp.get("sector_empresa")

    resultados_ajustados = []

    for candidato, score, components in top_candidatos:
        ajuste = 0.0
        ajustes_aplicados = []

        isco = candidato.get("isco_code", "")

        # Penalizacion por seniority mismatch
        if seniority:
            matriz = seniority_map.get("matriz_penalizacion", {}).get("pares", {})
            for nombre, regla in matriz.items():
                if seniority in regla.get("seniority", []):
                    if any(isco.startswith(i) for i in regla.get("isco", [])):
                        pen = regla.get("penalizacion", 0)
                        ajuste += pen
                        ajustes_aplicados.append(f"penalizacion_{nombre}: {pen}")

        # Penalizacion por tiene_gente_cargo mismatch
        if tiene_gente is False and isco.startswith(("11", "12")):
            pen = penalizaciones.get("gente_cargo_mismatch", {}).get("valor", -0.10)
            ajuste += pen
            ajustes_aplicados.append(f"gente_cargo_mismatch: {pen}")

        # Penalizacion por sector cruzado
        if sector and sector in sector_compat.get("sectores", {}):
            sector_info = sector_compat["sectores"][sector]
            if any(isco.startswith(i) for i in sector_info.get("isco_incompatibles", [])):
                pen = sector_info.get("penalizacion_cruzado", -0.25)
                ajuste += pen
                ajustes_aplicados.append(f"sector_cruzado: {pen}")

        # Boost por sector exacto
        if sector and sector in sector_compat.get("sectores", {}):
            sector_info = sector_compat["sectores"][sector]
            if any(isco.startswith(i) for i in sector_info.get("isco_compatibles", [])):
                boost_val = boosts.get("sector_exacto", {}).get("valor", 0.10)
                ajuste += boost_val
                ajustes_aplicados.append(f"sector_exacto: +{boost_val}")

        # Boost por tiene_gente_cargo match
        if tiene_gente is True and isco.startswith("1"):
            boost_val = boosts.get("gente_cargo_match", {}).get("valor", 0.05)
            ajuste += boost_val
            ajustes_aplicados.append(f"gente_cargo_match: +{boost_val}")

        score_final = max(0.0, min(1.0, score + ajuste))

        components["ajustes"] = ajustes_aplicados
        components["score_base"] = round(score, 4)
        components["score_ajustado"] = round(score_final, 4)

        resultados_ajustados.append((candidato, score_final, components))

    # Reordenar por score ajustado
    resultados_ajustados.sort(key=lambda x: x[1], reverse=True)

    return resultados_ajustados


# ============================================================================
# CARGAR OCUPACIONES ESCO
# ============================================================================

def cargar_ocupaciones_esco(db_conn: sqlite3.Connection) -> List[Dict]:
    """Carga todas las ocupaciones ESCO de la BD."""
    cursor = db_conn.cursor()

    # Intentar diferentes nombres de tabla
    tablas_posibles = ["esco_occupations", "esco_ocupaciones", "ocupaciones_esco"]
    tabla_encontrada = None

    for tabla in tablas_posibles:
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (tabla,))
        if cursor.fetchone():
            tabla_encontrada = tabla
            break

    if not tabla_encontrada:
        logger.warning("No se encontro tabla de ocupaciones ESCO")
        return []

    # Obtener columnas disponibles
    cursor.execute(f"PRAGMA table_info({tabla_encontrada})")
    columnas = {row[1] for row in cursor.fetchall()}

    # Construir query segun columnas disponibles
    cols = []

    # URI de la ocupacion
    if "occupation_uri" in columnas:
        cols.append("occupation_uri as esco_uri")
    elif "uri" in columnas:
        cols.append("uri as esco_uri")
    elif "esco_uri" in columnas:
        cols.append("esco_uri")

    # Label/nombre de la ocupacion
    if "preferred_label_es" in columnas:
        cols.append("preferred_label_es as label")
    elif "label" in columnas:
        cols.append("label")
    elif "esco_label" in columnas:
        cols.append("esco_label as label")
    elif "preferred_label" in columnas:
        cols.append("preferred_label as label")

    # Codigo ISCO
    if "isco_code" in columnas:
        cols.append("isco_code")
    elif "isco" in columnas:
        cols.append("isco as isco_code")

    # Descripcion
    if "description_es" in columnas:
        cols.append("description_es as description")
    elif "description" in columnas:
        cols.append("description")

    # Tareas y skills (si existen)
    if "tasks" in columnas:
        cols.append("tasks")

    if "skills" in columnas:
        cols.append("skills")

    if not cols:
        logger.warning(f"Tabla {tabla_encontrada} no tiene columnas esperadas")
        return []

    query = f"SELECT {', '.join(cols)} FROM {tabla_encontrada}"
    cursor.execute(query)

    ocupaciones = []
    for row in cursor:
        ocp = {}
        for i, col in enumerate(cols):
            col_name = col.split(" as ")[-1] if " as " in col else col
            ocp[col_name] = row[i]
        ocupaciones.append(ocp)

    return ocupaciones


# ============================================================================
# FUNCION PRINCIPAL DE MATCHING
# ============================================================================

def match_oferta_v2(
    oferta_nlp: Dict,
    db_conn: sqlite3.Connection,
    config: Dict = None,
    ocupaciones_cache: List[Dict] = None
) -> MatchResult:
    """
    Pipeline completo de matching v2.

    Args:
        oferta_nlp: Diccionario con todos los campos NLP v10
        db_conn: Conexion a la base de datos
        config: Configuracion (se carga automaticamente si es None)
        ocupaciones_cache: Cache de ocupaciones ESCO (opcional)

    Returns:
        MatchResult con todos los detalles del matching
    """
    if config is None:
        config = load_all_configs()

    # -------------------------------------------------------------------------
    # NIVEL 0: Filtro de validez
    # -------------------------------------------------------------------------
    es_valida, razon = nivel_0_filtro_validez(oferta_nlp, config)
    if not es_valida:
        return MatchResult(
            status=MatchStatus.FILTERED.value,
            esco_uri=None,
            esco_label=None,
            isco_code=None,
            score=0.0,
            score_components={},
            nivel_match=0,
            metodo="filtrado",
            candidatos_considerados=0,
            alternativas=[],
            metadata={"razon_filtrado": razon}
        )

    # -------------------------------------------------------------------------
    # NIVEL 1: Bypass diccionario
    # -------------------------------------------------------------------------
    titulo_limpio = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo")
    bypass = nivel_1_bypass_diccionario(titulo_limpio, config, db_conn)

    if bypass:
        return MatchResult(
            status=MatchStatus.BYPASS.value,
            esco_uri=bypass["esco_uri"],
            esco_label=bypass["esco_label"],
            isco_code=bypass["isco_code"],
            score=bypass["score"],
            score_components={"bypass": 1.0},
            nivel_match=1,
            metodo=bypass["metodo"],
            candidatos_considerados=1,
            alternativas=[],
            metadata={"titulo_buscado": titulo_limpio}
        )

    # -------------------------------------------------------------------------
    # NIVEL 2: Filtrar candidatos
    # -------------------------------------------------------------------------
    if ocupaciones_cache:
        todos_candidatos = ocupaciones_cache
    else:
        todos_candidatos = cargar_ocupaciones_esco(db_conn)

    if not todos_candidatos:
        return MatchResult(
            status=MatchStatus.NO_MATCH.value,
            esco_uri=None,
            esco_label=None,
            isco_code=None,
            score=0.0,
            score_components={},
            nivel_match=2,
            metodo="sin_ocupaciones_esco",
            candidatos_considerados=0,
            alternativas=[],
            metadata={"error": "No hay ocupaciones ESCO cargadas"}
        )

    candidatos_filtrados = nivel_2_filtrar_por_contexto(todos_candidatos, oferta_nlp, config)

    if not candidatos_filtrados:
        candidatos_filtrados = todos_candidatos

    # -------------------------------------------------------------------------
    # NIVEL 3: Scoring
    # -------------------------------------------------------------------------
    top_5 = nivel_3_scoring(candidatos_filtrados, oferta_nlp, config)

    if not top_5:
        return MatchResult(
            status=MatchStatus.NO_MATCH.value,
            esco_uri=None,
            esco_label=None,
            isco_code=None,
            score=0.0,
            score_components={},
            nivel_match=3,
            metodo="sin_candidatos",
            candidatos_considerados=len(candidatos_filtrados),
            alternativas=[],
            metadata={}
        )

    # -------------------------------------------------------------------------
    # NIVEL 4: Ajustes finales
    # -------------------------------------------------------------------------
    top_ajustados = nivel_4_ajustes(top_5, oferta_nlp, config)

    mejor = top_ajustados[0]
    candidato, score_final, components = mejor

    # -------------------------------------------------------------------------
    # NIVEL 5: Decision final
    # -------------------------------------------------------------------------
    score_minimo = config.get("matching", {}).get("filtros", {}).get("score_minimo_final", 0.45)

    alternativas = [
        {
            "esco_uri": c.get("esco_uri"),
            "label": c.get("label"),
            "isco_code": c.get("isco_code"),
            "score": round(s, 4)
        }
        for c, s, _ in top_ajustados[1:4]
    ]

    if score_final < score_minimo:
        return MatchResult(
            status=MatchStatus.NO_MATCH.value,
            esco_uri=candidato.get("esco_uri"),
            esco_label=candidato.get("label"),
            isco_code=candidato.get("isco_code"),
            score=round(score_final, 4),
            score_components=components,
            nivel_match=5,
            metodo="score_bajo",
            candidatos_considerados=len(candidatos_filtrados),
            alternativas=alternativas,
            metadata={"score_minimo_requerido": score_minimo}
        )

    return MatchResult(
        status=MatchStatus.SUCCESS.value,
        esco_uri=candidato.get("esco_uri"),
        esco_label=candidato.get("label"),
        isco_code=candidato.get("isco_code"),
        score=round(score_final, 4),
        score_components=components,
        nivel_match=5,
        metodo="cascada_v2",
        candidatos_considerados=len(candidatos_filtrados),
        alternativas=alternativas,
        metadata={
            "filtros_aplicados": {
                "area_funcional": oferta_nlp.get("area_funcional"),
                "nivel_seniority": oferta_nlp.get("nivel_seniority"),
                "tiene_gente_cargo": oferta_nlp.get("tiene_gente_cargo")
            }
        }
    )


# ============================================================================
# PROCESAR OFERTAS
# ============================================================================

def obtener_ofertas_nlp(
    db_conn: sqlite3.Connection,
    ids: List[str] = None,
    limit: int = None,
    nlp_version: str = "10.0.0"
) -> List[Dict]:
    """Obtiene ofertas con datos NLP de la BD."""
    cursor = db_conn.cursor()

    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            n.titulo_limpio,
            n.area_funcional,
            n.nivel_seniority,
            n.modalidad,
            n.tipo_oferta,
            n.tiene_gente_cargo,
            n.sector_empresa,
            n.calidad_texto,
            n.tareas_explicitas,
            n.tareas_inferidas,
            n.skills_tecnicas_list,
            n.tecnologias_list,
            n.conocimientos_especificos_list,
            n.mision_rol,
            n.licencia_conducir
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE n.nlp_version = ?
    """

    params = [nlp_version]

    if ids:
        placeholders = ','.join(['?' for _ in ids])
        query += f" AND o.id_oferta IN ({placeholders})"
        params.extend(ids)

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, params)

    columnas = [desc[0] for desc in cursor.description]
    ofertas = []

    for row in cursor.fetchall():
        oferta = dict(zip(columnas, row))
        ofertas.append(oferta)

    return ofertas


def procesar_ofertas_v2(
    db_path: str = None,
    ids: List[str] = None,
    limit: int = None,
    nlp_version: str = "10.0.0",
    test_mode: bool = False,
    verbose: bool = False
) -> List[Dict]:
    """
    Procesa ofertas con el matcher v2.

    Args:
        db_path: Path a la BD (usa default si None)
        ids: Lista de IDs especificos a procesar
        limit: Limite de ofertas
        nlp_version: Version NLP a usar
        test_mode: Si True, no guarda resultados
        verbose: Si True, muestra detalles

    Returns:
        Lista de resultados de matching
    """
    if db_path is None:
        db_path = str(DB_PATH)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Cargar config y ocupaciones una vez
    config = load_all_configs()
    ocupaciones = cargar_ocupaciones_esco(conn)

    logger.info(f"Ocupaciones ESCO cargadas: {len(ocupaciones)}")

    # Obtener ofertas
    ofertas = obtener_ofertas_nlp(conn, ids, limit, nlp_version)
    logger.info(f"Ofertas a procesar: {len(ofertas)}")

    resultados = []
    stats = {"success": 0, "filtered": 0, "no_match": 0, "bypass": 0}

    for i, oferta in enumerate(ofertas):
        result = match_oferta_v2(oferta, conn, config, ocupaciones)
        resultados.append({
            "id_oferta": oferta["id_oferta"],
            "titulo": oferta["titulo"],
            **result.to_dict()
        })

        stats[result.status] = stats.get(result.status, 0) + 1

        if verbose:
            print(f"\n[{i+1}/{len(ofertas)}] ID: {oferta['id_oferta']}")
            print(f"  Titulo: {oferta['titulo'][:60]}...")
            print(f"  Status: {result.status}")
            print(f"  ESCO: {result.esco_label}")
            print(f"  Score: {result.score}")
            print(f"  Metodo: {result.metodo}")

    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN MATCHING V2")
    print("="*60)
    print(f"Total procesadas: {len(ofertas)}")
    print(f"  - Success:   {stats['success']} ({stats['success']/len(ofertas)*100:.1f}%)")
    print(f"  - No Match:  {stats['no_match']} ({stats['no_match']/len(ofertas)*100:.1f}%)")
    print(f"  - Bypass:    {stats['bypass']} ({stats['bypass']/len(ofertas)*100:.1f}%)")
    print(f"  - Filtered:  {stats['filtered']} ({stats['filtered']/len(ofertas)*100:.1f}%)")

    if not test_mode:
        # TODO: Guardar resultados en BD
        logger.info("Modo produccion - guardando resultados...")
    else:
        logger.info("Modo test - resultados NO guardados")

    conn.close()
    return resultados


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI para matching v2."""
    parser = argparse.ArgumentParser(
        description="Matching ESCO v2.0 - Pipeline en cascada"
    )

    parser.add_argument(
        "--ids",
        nargs="+",
        help="IDs especificos a procesar"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limite de ofertas a procesar"
    )

    parser.add_argument(
        "--nlp-version",
        default="10.0.0",
        help="Version NLP a usar (default: 10.0.0)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo test (no guarda resultados)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mostrar detalles de cada oferta"
    )

    parser.add_argument(
        "--db",
        help="Path a la base de datos"
    )

    args = parser.parse_args()

    resultados = procesar_ofertas_v2(
        db_path=args.db,
        ids=args.ids,
        limit=args.limit,
        nlp_version=args.nlp_version,
        test_mode=args.test,
        verbose=args.verbose
    )

    return resultados


if __name__ == "__main__":
    main()
