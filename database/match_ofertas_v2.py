# -*- coding: utf-8 -*-
"""
Matching ESCO v2.1.1 - Pipeline en cascada con BGE-M3 Semantico
================================================================

Combina:
- Filtros v2.0 (area_funcional, seniority, sector, bypass diccionario)
- Scoring BGE-M3 semantico (como v8.3)

VERSION: v2.1.1 (2025-12-10)
- Fix: Corregida lógica de filtros ISCO para usar prefijos correctamente
- Fix: area_funcional excluye ISCO según config (ej: Ventas excluye "2")
- Fix: tiene_gente_cargo=True agrega códigos de directivos si no los tiene

Autor: MOL Team
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

import numpy as np

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
EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"


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
# BGE-M3 SEMANTIC MATCHER
# ============================================================================

class SemanticMatcher:
    """Matcher semantico usando BGE-M3 y embeddings pre-calculados."""

    def __init__(self):
        self.model = None
        self.esco_embeddings = None
        self.esco_metadata = None
        self._loaded = False

    def load(self):
        """Carga modelo y embeddings."""
        if self._loaded:
            return

        logger.info("Cargando modelo BGE-M3...")
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('BAAI/bge-m3')

        # Cargar embeddings pre-calculados
        occ_emb_path = EMBEDDINGS_DIR / "esco_occupations_embeddings.npy"
        occ_meta_path = EMBEDDINGS_DIR / "esco_occupations_metadata.json"

        if occ_emb_path.exists() and occ_meta_path.exists():
            self.esco_embeddings = np.load(occ_emb_path)
            with open(occ_meta_path, 'r', encoding='utf-8') as f:
                self.esco_metadata = json.load(f)
            logger.info(f"Cargados {len(self.esco_embeddings)} embeddings ESCO")
        else:
            raise FileNotFoundError(f"Embeddings no encontrados en {occ_emb_path}")

        self._loaded = True

    def encode(self, text: str) -> np.ndarray:
        """Genera embedding para un texto."""
        if not self._loaded:
            self.load()
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        # Normalizar
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def search(self, query: str, top_k: int = 10, isco_filter: List[str] = None) -> List[Dict]:
        """
        Busca ocupaciones ESCO similares usando cosine similarity.

        Args:
            query: Texto de busqueda (titulo + tareas + skills)
            top_k: Numero de resultados
            isco_filter: Lista de prefijos ISCO permitidos (opcional)

        Returns:
            Lista de (metadata, score)
        """
        if not self._loaded:
            self.load()

        # Generar embedding de la query
        query_emb = self.encode(query)

        # Calcular similitud coseno con todos los ESCO
        # Los embeddings ya estan normalizados, asi que dot product = cosine
        similarities = np.dot(self.esco_embeddings, query_emb)

        # Crear lista de (indice, score) con filtro ISCO
        resultados = []
        for idx, score in enumerate(similarities):
            if idx < len(self.esco_metadata):
                meta = self.esco_metadata[idx]
                isco = meta.get("isco_code", "")

                # Aplicar filtro ISCO si existe
                if isco_filter:
                    # Los códigos ISCO en metadata pueden tener prefijo 'C'
                    isco_num = isco.lstrip('C') if isco else ''
                    if not any(isco_num.startswith(prefix) for prefix in isco_filter):
                        continue

                # Normalizar código ISCO (quitar prefijo 'C' si existe)
                isco_normalizado = isco.lstrip('C') if isco else ''
                resultados.append({
                    "esco_uri": meta.get("uri"),
                    "label": meta.get("label"),
                    "isco_code": isco_normalizado,
                    "score": float(score)
                })

        # Ordenar por score y retornar top_k
        resultados.sort(key=lambda x: x["score"], reverse=True)
        return resultados[:top_k]


# Singleton global
_semantic_matcher = None

def get_semantic_matcher() -> SemanticMatcher:
    """Obtiene instancia singleton del matcher semantico."""
    global _semantic_matcher
    if _semantic_matcher is None:
        _semantic_matcher = SemanticMatcher()
    return _semantic_matcher


# ============================================================================
# NIVEL 0: FILTRO DE VALIDEZ (igual que v2.0)
# ============================================================================

def nivel_0_filtro_validez(oferta_nlp: Dict, config: Dict) -> Tuple[bool, str]:
    """Verifica si la oferta es valida para matching."""
    filtros = config.get("matching", {}).get("filtros", {})

    tipo_oferta = oferta_nlp.get("tipo_oferta")
    tipos_validos = filtros.get("tipo_oferta_validos", ["demanda_real"])

    if tipo_oferta and tipo_oferta not in tipos_validos:
        return False, f"tipo_oferta_invalido: {tipo_oferta}"

    calidad = oferta_nlp.get("calidad_texto")
    if calidad and calidad == "muy_baja":
        return False, f"calidad_texto_baja: {calidad}"

    return True, ""


# ============================================================================
# NIVEL 1: BYPASS DICCIONARIO ARGENTINO (igual que v2.0)
# ============================================================================

def nivel_1_bypass_diccionario(
    titulo_limpio: str,
    config: Dict,
    db_conn: sqlite3.Connection
) -> Optional[Dict]:
    """Busca match directo en diccionario argentino."""
    bypass_config = config.get("matching", {}).get("bypass_diccionario", {})

    if not bypass_config.get("habilitado", True):
        return None

    if not titulo_limpio:
        return None

    tabla = bypass_config.get("tabla", "diccionario_arg_esco")
    cursor = db_conn.cursor()

    # Verificar si la tabla existe
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (tabla,))

    if not cursor.fetchone():
        return None

    # Busqueda exacta
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

    # Busqueda fuzzy
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
            pass
        except Exception as e:
            logger.debug(f"Error en fuzzy: {e}")

    return None


# ============================================================================
# NIVEL 2: OBTENER FILTROS ISCO (CORREGIDO v2.1.1)
# ============================================================================

def _isco_coincide_prefijo(isco_code: str, prefijos: set) -> bool:
    """Verifica si un código ISCO coincide con alguno de los prefijos."""
    for prefijo in prefijos:
        if isco_code.startswith(prefijo):
            return True
    return False


def _filtrar_por_prefijos(isco_set: set, permitir: set, excluir: set) -> set:
    """
    Filtra un set de códigos ISCO según prefijos permitidos/excluidos.

    - permitir: prefijos de 1-2 dígitos que deben coincidir
    - excluir: prefijos de 1-2 dígitos que no pueden coincidir
    """
    resultado = set()
    for isco in isco_set:
        # Verificar si está permitido (si hay lista de permitidos)
        if permitir:
            if not _isco_coincide_prefijo(isco, permitir):
                continue
        # Verificar que no esté excluido
        if excluir:
            if _isco_coincide_prefijo(isco, excluir):
                continue
        resultado.add(isco)
    return resultado


def obtener_filtros_isco(oferta_nlp: Dict, config: Dict) -> Optional[List[str]]:
    """
    Determina filtros ISCO basados en contexto NLP.

    Lógica corregida v2.1.1:
    - area_funcional define códigos específicos (3 dígitos: "122", "332")
    - nivel_seniority define prefijos de nivel (1 dígito: "1", "2", "3")
    - Los prefijos se aplican sobre los códigos de área

    Returns:
        Lista de prefijos ISCO permitidos, o None si no hay filtro.
    """
    area_map = config.get("area_map", {}).get("mappings", {})
    seniority_map = config.get("seniority_map", {}).get("mappings", {})
    filtros = config.get("matching", {}).get("filtros", {})

    isco_validos = set()

    # Por area_funcional (códigos específicos de 3 dígitos)
    if filtros.get("usar_filtro_area", True):
        area = oferta_nlp.get("area_funcional")
        if area and area in area_map:
            mapeo = area_map[area]
            primarios = set(mapeo.get("isco_primarios", []))
            secundarios = set(mapeo.get("isco_secundarios", []))
            area_excluir = set(mapeo.get("excluir", []))

            # Combinar primarios y secundarios
            isco_validos = primarios | secundarios

            # Aplicar exclusiones del área (son prefijos de 1 dígito)
            if area_excluir:
                isco_validos = _filtrar_por_prefijos(isco_validos, set(), area_excluir)

    # Por seniority (prefijos de 1 dígito)
    if filtros.get("usar_filtro_seniority", True):
        seniority = oferta_nlp.get("nivel_seniority")
        if seniority and seniority in seniority_map:
            mapeo = seniority_map[seniority]
            permitir = set(mapeo.get("permitir", []))
            excluir = set(mapeo.get("excluir", []))

            if isco_validos:
                # Filtrar los códigos de área según prefijos de seniority
                isco_validos = _filtrar_por_prefijos(isco_validos, permitir, excluir)
            else:
                # Sin filtro de área, usar solo prefijos de seniority
                if permitir:
                    isco_validos = permitir - excluir

    # Por tiene_gente_cargo
    if filtros.get("usar_filtro_supervision", True):
        tiene_gente = oferta_nlp.get("tiene_gente_cargo")
        if tiene_gente is True:
            # Para roles con gente a cargo, priorizar directivos
            # Agregar prefijo "1" si hay filtro de área pero no incluye directivos
            if isco_validos:
                tiene_directivo = any(i.startswith("1") for i in isco_validos)
                if not tiene_directivo:
                    # Agregar ISCOs de directivos relevantes
                    isco_validos.add("12")  # Directores de administración y servicios
                    isco_validos.add("122")  # Directores de ventas y comercialización
        elif tiene_gente is False:
            # Excluir alta dirección
            if isco_validos:
                isco_validos = _filtrar_por_prefijos(isco_validos, set(), {"11", "12"})

    return list(isco_validos) if isco_validos else None


# ============================================================================
# NIVEL 3: SCORING BGE-M3 SEMANTICO (NUEVO!)
# ============================================================================

def construir_query_semantica(oferta_nlp: Dict) -> str:
    """
    Construye texto rico para busqueda semantica.

    Incluye: titulo + tareas + skills + tecnologias
    """
    partes = []

    # Titulo (principal)
    titulo = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo") or ""
    if titulo:
        partes.append(titulo)

    # Tareas explicitas
    tareas = oferta_nlp.get("tareas_explicitas") or []
    if isinstance(tareas, str):
        try:
            tareas = json.loads(tareas)
        except:
            tareas = []
    if tareas:
        # Manejar caso donde tareas es lista de dicts o lista de strings
        tareas_str = []
        for t in tareas[:5]:
            if isinstance(t, dict):
                tareas_str.append(str(t.get('tarea', t.get('descripcion', str(t)))))
            else:
                tareas_str.append(str(t))
        if tareas_str:
            partes.append("Tareas: " + ", ".join(tareas_str))

    # Skills tecnicas
    skills = oferta_nlp.get("skills_tecnicas_list") or []
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except:
            skills = []
    if skills:
        partes.append("Skills: " + ", ".join(skills[:5]))

    # Tecnologias
    tecno = oferta_nlp.get("tecnologias_list") or []
    if isinstance(tecno, str):
        try:
            tecno = json.loads(tecno)
        except:
            tecno = []
    if tecno:
        partes.append("Tecnologias: " + ", ".join(tecno[:5]))

    # Mision del rol
    mision = oferta_nlp.get("mision_rol") or ""
    if mision and len(mision) > 20:
        partes.append(mision[:200])

    return ". ".join(partes)


def nivel_3_scoring_bge(
    oferta_nlp: Dict,
    config: Dict,
    isco_filter: List[str] = None
) -> List[Tuple[Dict, float, Dict]]:
    """
    Scoring semantico usando BGE-M3.

    Returns:
        Lista de (candidato, score_total, score_components)
    """
    matcher = get_semantic_matcher()

    # Construir query rica
    query = construir_query_semantica(oferta_nlp)

    if not query.strip():
        logger.warning("Query vacia, usando titulo crudo")
        query = oferta_nlp.get("titulo", "")

    # Buscar con BGE-M3
    top_k = config.get("matching", {}).get("busqueda", {}).get("top_k_candidatos", 10)
    resultados = matcher.search(query, top_k=top_k, isco_filter=isco_filter)

    # Formatear como tuplas (candidato, score, components)
    formatted = []
    for r in resultados:
        components = {
            "titulo_semantico": round(r["score"], 4),
            "query_usada": query[:100] + "..." if len(query) > 100 else query,
            "metodo": "bge_m3_cosine"
        }
        formatted.append((r, r["score"], components))

    return formatted


# ============================================================================
# NIVEL 4: AJUSTES FINALES (igual que v2.0)
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

    resultados_ajustados.sort(key=lambda x: x[1], reverse=True)
    return resultados_ajustados


# ============================================================================
# FUNCION PRINCIPAL DE MATCHING
# ============================================================================

def match_oferta_v2_bge(
    oferta_nlp: Dict,
    db_conn: sqlite3.Connection,
    config: Dict = None
) -> MatchResult:
    """
    Pipeline completo de matching v2.1 con BGE-M3.
    """
    if config is None:
        config = load_all_configs()

    # NIVEL 0: Filtro de validez
    es_valida, razon = nivel_0_filtro_validez(oferta_nlp, config)
    if not es_valida:
        return MatchResult(
            status=MatchStatus.FILTERED.value,
            esco_uri=None, esco_label=None, isco_code=None,
            score=0.0, score_components={},
            nivel_match=0, metodo="filtrado",
            candidatos_considerados=0, alternativas=[],
            metadata={"razon_filtrado": razon}
        )

    # NIVEL 1: Bypass diccionario
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
            nivel_match=1, metodo=bypass["metodo"],
            candidatos_considerados=1, alternativas=[],
            metadata={"titulo_buscado": titulo_limpio}
        )

    # NIVEL 2: Obtener filtros ISCO
    isco_filter = obtener_filtros_isco(oferta_nlp, config)

    # NIVEL 3: Scoring BGE-M3
    top_candidatos = nivel_3_scoring_bge(oferta_nlp, config, isco_filter)

    if not top_candidatos:
        return MatchResult(
            status=MatchStatus.NO_MATCH.value,
            esco_uri=None, esco_label=None, isco_code=None,
            score=0.0, score_components={},
            nivel_match=3, metodo="sin_candidatos",
            candidatos_considerados=0, alternativas=[],
            metadata={"isco_filter": isco_filter}
        )

    # NIVEL 4: Ajustes finales
    top_ajustados = nivel_4_ajustes(top_candidatos, oferta_nlp, config)

    mejor = top_ajustados[0]
    candidato, score_final, components = mejor

    # NIVEL 5: Decision final
    score_minimo = config.get("matching", {}).get("filtros", {}).get("score_minimo_final", 0.50)

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
            nivel_match=5, metodo="score_bajo",
            candidatos_considerados=len(top_candidatos),
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
        nivel_match=5, metodo="bge_m3_semantico",
        candidatos_considerados=len(top_candidatos),
        alternativas=alternativas,
        metadata={
            "filtros_aplicados": {
                "area_funcional": oferta_nlp.get("area_funcional"),
                "nivel_seniority": oferta_nlp.get("nivel_seniority"),
                "isco_filter": isco_filter
            }
        }
    )


# ============================================================================
# PROCESAR OFERTAS
# ============================================================================

def obtener_ofertas_nlp(
    db_conn: sqlite3.Connection,
    ids: List[str] = None,
    limit: int = None
) -> List[Dict]:
    """Obtiene ofertas con datos NLP de la BD."""
    cursor = db_conn.cursor()

    # Buscar cualquier version NLP disponible
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
            n.licencia_conducir,
            n.nlp_version
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE 1=1
    """

    params = []

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


def procesar_ofertas_v2_bge(
    db_path: str = None,
    ids: List[str] = None,
    limit: int = None,
    test_mode: bool = False,
    verbose: bool = False
) -> List[Dict]:
    """
    Procesa ofertas con el matcher v2.1 BGE-M3.
    """
    if db_path is None:
        db_path = str(DB_PATH)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Pre-cargar modelo BGE-M3
    logger.info("Inicializando matcher semantico BGE-M3...")
    matcher = get_semantic_matcher()
    matcher.load()

    # Cargar config
    config = load_all_configs()

    # Obtener ofertas
    ofertas = obtener_ofertas_nlp(conn, ids, limit)
    logger.info(f"Ofertas a procesar: {len(ofertas)}")

    if not ofertas:
        logger.warning("No hay ofertas para procesar")
        conn.close()
        return []

    resultados = []
    stats = {"success": 0, "filtered": 0, "no_match": 0, "bypass": 0}

    for i, oferta in enumerate(ofertas):
        result = match_oferta_v2_bge(oferta, conn, config)
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
    total = len(ofertas)
    print("\n" + "="*60)
    print("RESUMEN MATCHING V2.1 BGE-M3")
    print("="*60)
    print(f"Total procesadas: {total}")
    print(f"  - Success:   {stats['success']} ({stats['success']/total*100:.1f}%)")
    print(f"  - No Match:  {stats['no_match']} ({stats['no_match']/total*100:.1f}%)")
    print(f"  - Bypass:    {stats['bypass']} ({stats['bypass']/total*100:.1f}%)")
    print(f"  - Filtered:  {stats['filtered']} ({stats['filtered']/total*100:.1f}%)")

    conn.close()
    return resultados


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI para matching v2.1 BGE-M3."""
    parser = argparse.ArgumentParser(
        description="Matching ESCO v2.1 - Pipeline con BGE-M3 Semantico"
    )

    parser.add_argument("--ids", nargs="+", help="IDs especificos a procesar")
    parser.add_argument("--limit", type=int, help="Limite de ofertas a procesar")
    parser.add_argument("--test", action="store_true", help="Modo test")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar detalles")
    parser.add_argument("--db", help="Path a la base de datos")

    args = parser.parse_args()

    resultados = procesar_ofertas_v2_bge(
        db_path=args.db,
        ids=args.ids,
        limit=args.limit,
        test_mode=args.test,
        verbose=args.verbose
    )

    return resultados


if __name__ == "__main__":
    main()
