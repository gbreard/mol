#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
limpiar_titulos.py v2.2
========================
Limpia titulos de ofertas eliminando ruido empresarial/geografico.
Lee patrones desde config/nlp_titulo_limpieza.json

v2.2 (2026-01-13): Agregados patrones FASE 1 optimizacion
- codigos_final: "DevOps - Remoto - 1729" -> "DevOps"
- modalidad_guion: "Java - Mix (On Site & Remoto)" -> "Java"
- requisitos_edad: "Vendedor +45 años" -> "Vendedor"
- ubicacion_guion_extendido: "Analista - Retiro" -> "Analista"

Patrones de ruido:
- Ubicaciones: "- Roque Perez - BA", "Z/Escobar", "zona CABA"
- Empresas/sectores: "(Consumo Masivo)", "para Maderera (PYME)"
- Codigos: "(req199380)", "(Eventual)", "- 1729"
- Modalidad: "- Remoto -", "- Mix (On Site & Remoto)"
- Contexto excesivo: "importante Concesionario Oficial..."
"""

import re
import sqlite3
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

base = Path(__file__).parent
config_dir = base.parent / "config"


def cargar_config() -> Dict[str, Any]:
    """Carga configuracion desde JSON"""
    config_path = config_dir / "nlp_titulo_limpieza.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# Cargar config una vez al importar
_CONFIG = cargar_config()


def limpiar_titulo(titulo: str, config: Dict[str, Any] = None) -> str:
    """
    Limpia un titulo de oferta eliminando ruido.

    Args:
        titulo: Titulo original de la oferta
        config: Config opcional (usa _CONFIG global si no se pasa)

    Returns:
        Titulo limpio, solo con la ocupacion

    Ejemplos:
        "Gerente de Operaciones - Gastronomia corporativa" -> "Gerente de Operaciones"
        "Analista de Cultivo - Roque Perez - BA" -> "Analista de Cultivo"
        "Representante Comercial (Consumo Masivo)" -> "Representante Comercial"
        "Venado Tuerto -Gerente de Ventas importante Concesionario" -> "Gerente de Ventas"
        "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10..." -> "Operarios industria Alimenticia"
    """
    if not titulo:
        return titulo

    if config is None:
        config = _CONFIG

    original = titulo

    # 0a. Eliminar codigos alfanumericos AL INICIO (671SI, ABC123, REF-12345)
    for patron_info in config.get("codigos_inicio", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo)

    # 0a2. Eliminar prefijos genericos (Busqueda Laboral:, Se busca:, etc)
    for patron_info in config.get("prefijos_genericos", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo)

    # 0b. Eliminar ubicaciones AL INICIO del titulo
    ciudades = config.get("ciudades_inicio", {}).get("lista", [])
    for ciudad in ciudades:
        titulo = re.sub(rf'^{re.escape(ciudad)}\s*[-–]\s*', '', titulo, flags=re.IGNORECASE)

    # 0c. Eliminar info administrativa (fechas, presentaciones, sucursales)
    for patron_info in config.get("info_administrativa", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 1. Eliminar codigos de referencia
    for patron_info in config.get("codigos_referencia", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 2. Eliminar palabras de modalidad al final
    modalidades = config.get("modalidad_final", {}).get("palabras", [])
    if modalidades:
        modalidad_pattern = '|'.join(re.escape(m) for m in modalidades)
        titulo = re.sub(rf'\s*\(?\s*({modalidad_pattern})\s*\)?$', '', titulo, flags=re.IGNORECASE)

    # 3. Eliminar zonas/ubicaciones al final
    for patron_info in config.get("zonas_ubicaciones", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 3b. Eliminar localidades especificas al final (- Caballito, - Belgrano, etc)
    localidades = config.get("localidades_final", {}).get("lista", [])
    for localidad in localidades:
        # Patron: " - Localidad" al final del titulo (con guion normal o largo)
        titulo = re.sub(rf'\s*[-–—]\s*{re.escape(localidad)}$', '', titulo, flags=re.IGNORECASE)

    # 4. Eliminar ubicacion con guion (– Vicente López)
    for patron_info in config.get("ubicacion_con_guion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo)

    # 4b. Eliminar contexto + ubicacion (para farmacias en Rio Cuarto)
    for patron_info in config.get("contexto_ubicacion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 5. Eliminar parentesis especificos
    for patron_info in config.get("parentesis_eliminar", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6. Eliminar texto despues de guion que sea contexto empresarial
    palabras_contexto = config.get("contexto_empresarial", {}).get("palabras", [])
    for palabra in palabras_contexto:
        # Solo con guion - evitar eliminar contenido valido
        titulo = re.sub(rf'\s*-\s*[^-]*{re.escape(palabra)}[^-]*$', '', titulo, flags=re.IGNORECASE)

    # 6c. [v2.2] Eliminar codigos numericos al FINAL (- 1729, - 4521)
    for patron_info in config.get("codigos_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6d. [v2.2] Eliminar modalidad con guion (- Remoto - CABA, - Mix (On Site & Remoto))
    for patron_info in config.get("modalidad_guion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6e. [v2.2] Eliminar requisitos de edad (+45 años, 25-35 años)
    for patron_info in config.get("requisitos_edad", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6f. [v2.2] Eliminar ubicaciones con guion - extendido
    for patron_info in config.get("ubicacion_guion_extendido", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6b. Eliminar preposiciones sueltas al final
    preposiciones = config.get("preposiciones_final", {}).get("palabras", [])
    if preposiciones:
        prep_pattern = '|'.join(re.escape(p) for p in preposiciones)
        titulo = re.sub(rf'\s+({prep_pattern})\s*$', '', titulo, flags=re.IGNORECASE)

    # 7. Expandir/eliminar abreviaturas (al final para que no interfiera con contexto_empresarial)
    for patron_info in config.get("abreviaturas_expandir", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        reemplazo = patron_info.get("reemplazo", "")
        if patron:
            titulo = re.sub(patron, reemplazo, titulo, flags=re.IGNORECASE)

    # 8. Limpieza final
    for patron_info in config.get("limpieza_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        reemplazo = patron_info.get("reemplazo", "")
        if patron:
            titulo = re.sub(patron, reemplazo, titulo)

    titulo = titulo.strip()

    return titulo


def detectar_multi_perfil(titulo: str, config: Dict[str, Any] = None) -> List[str]:
    """
    Detecta si un titulo tiene multiples perfiles y los separa.

    Args:
        titulo: Titulo (ya limpio) de la oferta
        config: Config opcional

    Returns:
        Lista de perfiles si es multi-perfil, lista con titulo original si no

    Ejemplos:
        "CAJEROS, BARISTAS, COCINEROS" -> ["CAJEROS", "BARISTAS", "COCINEROS"]
        "Desarrollador Python" -> ["Desarrollador Python"]
        "AUTOS OKM, USADOS" -> ["AUTOS OKM, USADOS"] (no es multi-perfil)
        "Cajero/a" -> ["Cajero/a"] (género inclusivo, NO es multi-perfil)
        "CAJERO/ENCARGADO" -> ["CAJERO", "ENCARGADO"] (candidato a multi-perfil)
    """
    if not titulo:
        return [titulo] if titulo else []

    if config is None:
        config = _CONFIG

    multi_config = config.get("multi_perfil", {})
    separadores = multi_config.get("separadores", [", "])
    min_perfiles = multi_config.get("min_perfiles", 2)
    min_largo_perfil = multi_config.get("min_largo_perfil", 5)
    no_ocupacion = multi_config.get("no_ocupacion", [])

    # Patrones de género inclusivo que NO son multi-perfil
    # Ej: "Vendedor/a", "Cajeros/as", "Operario/a"
    patrones_genero = [
        r'/a\b', r'/as\b', r'/o\b', r'/os\b',  # Vendedor/a, Cajeros/as
        r'o/a\b', r'os/as\b', r'a/o\b', r'as/os\b',  # Vendedor o/a
        r'\(a\)', r'\(o\)', r'\(as\)', r'\(os\)',  # Vendedor(a)
    ]

    # Verificar si es patrón de género inclusivo
    import re
    for patron in patrones_genero:
        if re.search(patron, titulo, re.IGNORECASE):
            # Es género inclusivo, no multi-perfil
            return [titulo]

    # Probar cada separador en orden de prioridad
    for sep in separadores:
        if sep not in titulo:
            continue

        perfiles = [p.strip() for p in titulo.split(sep)]
        # Filtrar perfiles vacíos o muy cortos
        perfiles = [p for p in perfiles if len(p) >= 3]

        if len(perfiles) < min_perfiles:
            continue

        # Verificar que los items parezcan ocupaciones
        perfiles_validos = []
        for perfil in perfiles:
            perfil_lower = perfil.lower()
            # Excluir si contiene palabras que no son ocupaciones
            es_ocupacion = True
            for palabra in no_ocupacion:
                if palabra in perfil_lower:
                    es_ocupacion = False
                    break
            # Excluir si es muy corto y no es mayúsculas
            if len(perfil) < min_largo_perfil and not perfil.isupper():
                es_ocupacion = False
            if es_ocupacion:
                perfiles_validos.append(perfil)

        # Solo es multi-perfil si al menos min_perfiles son válidos
        if len(perfiles_validos) >= min_perfiles:
            return perfiles_validos

    # Ningún separador funcionó, devolver titulo original
    return [titulo]


# Configuración LLM para validación multi-perfil
OLLAMA_URL = "http://localhost:11434/api/generate"
# Modelo optimizado: 7b es suficiente para extracción JSON (3x más rápido que 14b)
OLLAMA_MODEL = "qwen2.5:7b"


def validar_multi_perfil_con_llm(
    titulo: str,
    descripcion: str,
    perfiles_candidatos: List[str],
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Valida con LLM si un título realmente representa múltiples perfiles.

    Analiza el título + descripción para determinar si la empresa busca:
    - MÚLTIPLES PERFILES: personas para posiciones DIFERENTES
    - UN SOLO PERFIL: una persona polivalente con múltiples habilidades

    Args:
        titulo: Título de la oferta
        descripcion: Descripción completa de la oferta
        perfiles_candidatos: Lista de perfiles detectados por regex
        timeout: Timeout en segundos para la llamada LLM

    Returns:
        {
            "es_multiple_perfil": bool,
            "perfiles_confirmados": List[str],
            "razon": str,
            "confianza": float
        }
    """
    prompt = f"""Analiza esta oferta laboral y determina si busca MÚLTIPLES PERFILES DISTINTOS
o UN SOLO PERFIL con múltiples habilidades/tareas.

TÍTULO: {titulo}
PERFILES DETECTADOS POR REGEX: {perfiles_candidatos}

DESCRIPCIÓN (extracto):
{descripcion[:1500] if descripcion else "(sin descripción)"}

---

CRITERIOS:
1. ES MÚLTIPLE PERFIL (es_multiple_perfil=true) si:
   - Buscan personas para POSICIONES/PUESTOS DIFERENTES
   - Mencionan vacantes separadas ("cajero y encargado para diferentes turnos")
   - Hay referencias a múltiples roles independientes

2. NO ES MÚLTIPLE PERFIL (es_multiple_perfil=false) si:
   - Buscan UNA persona que haga varias tareas
   - Es un perfil "polivalente", "multitarea", "integral"
   - Las palabras separadas son especializaciones del mismo rol
   - Ejemplo: "Vendedor Electrónica y Electrodomésticos" = 1 vendedor con 2 rubros
   - Ejemplo: "Desarrollador Python y Java" = 1 desarrollador que sepa ambos

Responde SOLO con JSON válido (sin texto adicional):
{{
    "es_multiple_perfil": true o false,
    "perfiles_confirmados": ["Perfil1", "Perfil2"] si es múltiple, o ["{titulo}"] si es uno solo,
    "razon": "explicación breve de 1 línea",
    "confianza": 0.0 a 1.0
}}"""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Bajo para respuestas consistentes
                "num_predict": 256,
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        text = result.get("response", "").strip()

        # Parsear JSON de la respuesta
        # Buscar el JSON en la respuesta (puede tener texto antes/después)
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "es_multiple_perfil": parsed.get("es_multiple_perfil", False),
                "perfiles_confirmados": parsed.get("perfiles_confirmados", [titulo]),
                "razon": parsed.get("razon", ""),
                "confianza": float(parsed.get("confianza", 0.5))
            }
        else:
            print(f"[WARN] No se encontró JSON en respuesta LLM: {text[:200]}")
            # Fallback: asumir que NO es múltiple (más conservador)
            return {
                "es_multiple_perfil": False,
                "perfiles_confirmados": [titulo],
                "razon": "No se pudo parsear respuesta LLM",
                "confianza": 0.0
            }

    except requests.exceptions.Timeout:
        print(f"[WARN] Timeout validando multi-perfil para: {titulo[:50]}")
        return {
            "es_multiple_perfil": False,
            "perfiles_confirmados": [titulo],
            "razon": "Timeout LLM",
            "confianza": 0.0
        }
    except Exception as e:
        print(f"[ERROR] Error validando multi-perfil: {e}")
        return {
            "es_multiple_perfil": False,
            "perfiles_confirmados": [titulo],
            "razon": f"Error: {str(e)}",
            "confianza": 0.0
        }


def expandir_ofertas_multi_perfil(ids: List[str] = None, dry_run: bool = True, usar_llm: bool = True):
    """
    Expande ofertas con multiples perfiles en registros separados.

    Cada perfil genera un nuevo registro con id_oferta derivado:
    - Original: 2123908
    - Expandidos: 2123908_1, 2123908_2, etc.

    Args:
        ids: Lista de IDs a procesar (None = Gold Set)
        dry_run: Si True, solo muestra qué haría sin modificar BD
        usar_llm: Si True, valida con LLM antes de expandir (usa descripción)

    Returns:
        Dict con estadísticas
    """
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Cargar IDs
    if ids is None:
        gold_set_100 = base / 'gold_set_nlp_100_ids.json'
        gold_set_49 = base / 'gold_set_manual_v2.json'

        if gold_set_100.exists():
            with open(gold_set_100, 'r', encoding='utf-8') as f:
                ids = json.load(f)
        else:
            with open(gold_set_49, 'r', encoding='utf-8') as f:
                gold_set = json.load(f)
            ids = [str(x['id_oferta']) for x in gold_set]

    print(f"Buscando ofertas multi-perfil en {len(ids)} ofertas...")
    print(f"Validación LLM: {'ACTIVADA' if usar_llm else 'DESACTIVADA'}")
    print("-" * 70)

    # Obtener datos de ofertas_nlp
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT n.*
        FROM ofertas_nlp n
        WHERE n.id_oferta IN ({placeholders})
    """, ids)

    rows = c.fetchall()
    columnas = [desc[0] for desc in c.description]

    # Si usar_llm, obtener descripciones de tabla ofertas
    descripciones = {}
    if usar_llm:
        c.execute(f"""
            SELECT id_oferta, descripcion
            FROM ofertas
            WHERE id_oferta IN ({placeholders})
        """, ids)
        for row in c.fetchall():
            descripciones[str(row[0])] = row[1] or ""

    ofertas_expandir = []
    ofertas_rechazadas_llm = []
    total_nuevos = 0

    for row in rows:
        row_dict = dict(zip(columnas, row))
        id_oferta = row_dict['id_oferta']
        titulo_limpio = row_dict.get('titulo_limpio') or ''

        # Paso 1: Detectar candidatos por regex
        perfiles_candidatos = detectar_multi_perfil(titulo_limpio)

        if len(perfiles_candidatos) > 1:
            # Paso 2: Validar con LLM si está activado
            if usar_llm:
                descripcion = descripciones.get(str(id_oferta), "")
                resultado_llm = validar_multi_perfil_con_llm(
                    titulo_limpio, descripcion, perfiles_candidatos
                )

                if resultado_llm["es_multiple_perfil"]:
                    perfiles_finales = resultado_llm["perfiles_confirmados"]
                    print(f"  {id_oferta}: {len(perfiles_finales)} perfiles [LLM: CONFIRMADO]")
                    print(f"    Razón: {resultado_llm['razon']}")
                else:
                    # LLM dice que NO es multi-perfil
                    perfiles_finales = [titulo_limpio]
                    ofertas_rechazadas_llm.append({
                        'id': id_oferta,
                        'titulo': titulo_limpio,
                        'candidatos': perfiles_candidatos,
                        'razon': resultado_llm['razon']
                    })
                    print(f"  {id_oferta}: RECHAZADO por LLM (era candidato: {perfiles_candidatos})")
                    print(f"    Razón: {resultado_llm['razon']}")
                    continue  # No expandir
            else:
                perfiles_finales = perfiles_candidatos
                print(f"  {id_oferta}: {len(perfiles_finales)} perfiles [REGEX]")

            ofertas_expandir.append({
                'id_original': id_oferta,
                'perfiles': perfiles_finales,
                'row_dict': row_dict
            })
            total_nuevos += len(perfiles_finales) - 1  # -1 porque el original ya existe
            for i, p in enumerate(perfiles_finales, 1):
                print(f"    {id_oferta}_{i}: {p}")
            print()

    print(f"\nResumen:")
    print(f"  Ofertas multi-perfil confirmadas: {len(ofertas_expandir)}")
    print(f"  Rechazadas por LLM: {len(ofertas_rechazadas_llm)}")
    print(f"  Registros nuevos a crear: {total_nuevos}")

    if ofertas_rechazadas_llm:
        print(f"\n  Rechazos LLM (NO son multi-perfil):")
        for r in ofertas_rechazadas_llm[:5]:
            print(f"    - {r['id']}: {r['titulo'][:40]}... -> {r['razon']}")
        if len(ofertas_rechazadas_llm) > 5:
            print(f"    ... y {len(ofertas_rechazadas_llm) - 5} más")

    if dry_run:
        print(f"\n[DRY RUN] No se modificó la BD. Usar dry_run=False para aplicar.")
        conn.close()
        return {
            'multi_perfil': len(ofertas_expandir),
            'rechazados_llm': len(ofertas_rechazadas_llm),
            'nuevos': total_nuevos,
            'aplicado': False,
            'rechazos_detalle': ofertas_rechazadas_llm
        }

    # Aplicar cambios
    print(f"\nAplicando cambios...")

    for oferta in ofertas_expandir:
        id_original = oferta['id_original']
        perfiles = oferta['perfiles']
        row_dict = oferta['row_dict']

        # Actualizar registro original con primer perfil
        c.execute("""
            UPDATE ofertas_nlp SET titulo_limpio = ? WHERE id_oferta = ?
        """, (perfiles[0], id_original))

        # Crear registros nuevos para perfiles adicionales
        for i, perfil in enumerate(perfiles[1:], 2):
            nuevo_id = f"{id_original}_{i}"

            # Copiar todos los campos del original
            campos = [col for col in columnas]
            valores = [row_dict[col] if col != 'id_oferta' else nuevo_id for col in campos]

            # Actualizar titulo_limpio con el perfil específico
            idx_titulo = campos.index('titulo_limpio')
            valores[idx_titulo] = perfil

            placeholders_insert = ','.join(['?' for _ in campos])
            campos_str = ','.join(campos)

            try:
                c.execute(f"INSERT INTO ofertas_nlp ({campos_str}) VALUES ({placeholders_insert})", valores)
            except sqlite3.IntegrityError:
                # Ya existe, actualizar
                c.execute("UPDATE ofertas_nlp SET titulo_limpio = ? WHERE id_oferta = ?", (perfil, nuevo_id))

    conn.commit()
    print(f"[OK] Expandidas {len(ofertas_expandir)} ofertas, creados {total_nuevos} registros nuevos")
    conn.close()

    return {'multi_perfil': len(ofertas_expandir), 'nuevos': total_nuevos, 'aplicado': True}


def agregar_columna_titulo_limpio():
    """Agrega columna titulo_limpio a ofertas_nlp si no existe"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    c = conn.cursor()

    c.execute("PRAGMA table_info(ofertas_nlp)")
    columnas = [col[1] for col in c.fetchall()]

    if 'titulo_limpio' not in columnas:
        print("Agregando columna titulo_limpio a ofertas_nlp...")
        c.execute("ALTER TABLE ofertas_nlp ADD COLUMN titulo_limpio TEXT")
        conn.commit()
        print("  [OK] Columna agregada")
    else:
        print("  [OK] Columna titulo_limpio ya existe")

    conn.close()


def procesar_gold_set():
    """Procesa titulos del Gold Set y guarda titulo_limpio"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Cargar IDs del Gold Set (usar expandido si existe)
    gold_set_100 = base / 'gold_set_nlp_100_ids.json'
    gold_set_49 = base / 'gold_set_manual_v2.json'

    if gold_set_100.exists():
        with open(gold_set_100, 'r', encoding='utf-8') as f:
            ids = json.load(f)
        print(f"Usando Gold Set expandido: {len(ids)} ofertas")
    else:
        with open(gold_set_49, 'r', encoding='utf-8') as f:
            gold_set = json.load(f)
        ids = [str(x['id_oferta']) for x in gold_set]
        print(f"Usando Gold Set original: {len(ids)} ofertas")

    print(f"\nProcesando {len(ids)} titulos...")
    print("-" * 70)

    # Obtener titulos
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT o.id_oferta, o.titulo
        FROM ofertas o
        WHERE o.id_oferta IN ({placeholders})
    """, ids)

    resultados = []
    cambios = 0

    for row in c.fetchall():
        id_oferta = row['id_oferta']
        titulo_original = row['titulo'] or ''
        titulo_limpio = limpiar_titulo(titulo_original)

        # Mostrar cambios
        if titulo_limpio != titulo_original:
            cambios += 1
            if cambios <= 10:  # Solo mostrar primeros 10
                print(f"  {id_oferta}:")
                print(f"    ANTES:  {titulo_original[:60]}")
                print(f"    DESPUES:{titulo_limpio[:60]}")
                print()

        resultados.append((titulo_limpio, str(id_oferta)))

    # Actualizar BD
    print(f"\nActualizando {len(resultados)} registros en ofertas_nlp...")
    c.executemany("""
        UPDATE ofertas_nlp
        SET titulo_limpio = ?
        WHERE id_oferta = ?
    """, resultados)
    conn.commit()

    print(f"\n[OK] {cambios}/{len(resultados)} titulos modificados")
    conn.close()

    return cambios


# Test standalone
if __name__ == '__main__':
    print("=" * 70)
    print("LIMPIEZA DE TITULOS v2.0 - Config desde JSON")
    print("=" * 70)

    # Mostrar config cargada
    print(f"\nConfig cargada: {len(_CONFIG)} secciones")
    for key in _CONFIG:
        if not key.startswith('_'):
            print(f"  - {key}")

    # Tests unitarios
    print("\nTESTS UNITARIOS:")
    print("-" * 70)
    tests = [
        ("Gerente de Operaciones - Gastronomia corporativa y Facility management", "Gerente de Operaciones"),
        ("Analista de Cultivo - Roque Perez - BA", "Analista de Cultivo - Roque Perez"),
        ("Representante Comercial (Consumo Masivo / Grandes Cuentas)", "Representante Comercial"),
        ("Operario de Almacen/Logistica Z/Escobar", "Operario de Almacen/Logistica"),
        ("Repositor/a Externo/a (Eventual) Moreno", "Repositor/a Externo/a"),
        ("Administrativa Comercio Exterior (req199380) Eventual", "Administrativa Comercio Exterior"),
        ("Venado Tuerto -Gerente de Ventas importante Concesionario Oficial Maquinaria Agricola", "Gerente de Ventas"),
        ("Gerente General para Maderera (PYME)", "Gerente General para Maderera"),
        ("Vendedor con Experiencia (Corredor)", "Vendedor con Experiencia"),
        ("Asistente Compliance (part time)", "Asistente Compliance"),
        ("Chofer - Repartidor", "Chofer - Repartidor"),
        ("Mozo/Moza", "Mozo/Moza"),
        # Nuevos casos v2.0
        ("671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10 de 10 a 1130 NUEVA Suc. SAN ISIDRO", "Operarios industria ALIMENTICIA"),
        ("ABC123 Vendedor Jr", "Vendedor Jr"),
        ("12345 Analista Contable", "Analista Contable"),
        ("REF-9876 Cajero/a - Suc. Palermo", "Cajero/a"),
        ("Recepcionista - presentarse lunes 9hs", "Recepcionista"),
        # Casos v2.1 - prefijos y ubicaciones
        ("Búsqueda Laboral: Modelista – Vicente López (Florida Oeste)", "Modelista"),
        ("Se busca: Contador Junior", "Contador Junior"),
        ("Buscamos Desarrollador Python", "Desarrollador Python"),
        ("Farmacéutico/a para farmacias en Rio Cuarto", "Farmacéutico/a"),
        ("Vendedor en Mar del Plata", "Vendedor"),
        # Casos v2.1 - localidades con guion normal
        ("Personal de limpieza - Caballito", "Personal de limpieza"),
        ("Analista de Cuentas a Pagar - GBA Norte", "Analista de Cuentas a Pagar"),
        ("Vendedor - Zona Rosario", "Vendedor"),
        ("Arquitecto - Belgrano", "Arquitecto"),
        ("Contador - Roque Perez", "Contador"),
        # NO eliminar - son especializaciones, no ubicaciones
        ("Chofer - Repartidor", "Chofer - Repartidor"),
        ("Abogado/a - Impuestos", "Abogado/a - Impuestos"),
    ]

    ok = 0
    for original, esperado in tests:
        resultado = limpiar_titulo(original)
        status = "OK" if resultado == esperado else "FAIL"
        if status == "OK":
            ok += 1
        print(f"  [{status}] {original[:50]}...")
        if status == "FAIL":
            print(f"       Esperado: {esperado}")
            print(f"       Obtenido: {resultado}")

    print(f"\nTests: {ok}/{len(tests)} OK")

    # Agregar columna y procesar
    print("\n" + "=" * 70)
    agregar_columna_titulo_limpio()
    procesar_gold_set()
