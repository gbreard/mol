"""
Sincronizador automático de .ai/learnings.yaml + Reporte de 3 Fases + Supabase

Actualiza métricas desde BD/configs hacia:
- learnings.yaml (local)
- Supabase tabla sistema_estado (colaboración)

Se ejecuta:
- Al iniciar sesión Claude Code (SessionStart hook)
- Al final del pipeline de matching

Fuentes de datos:
- config/matching_rules_business.json → reglas_negocio
- config/validation_rules.json → reglas_validacion
- config/sinonimos_argentinos_esco.json → sinonimos_argentinos
- BD pipeline_runs → ultimo_run, ofertas procesadas
- BD ofertas_esco_matching → ofertas_con_matching
- BD learning_history → eventos recientes

Version: 2.1
Fecha: 2026-01-17
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import re


# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
LEARNINGS_PATH = BASE_DIR / ".ai" / "learnings.yaml"
CONFIG_DIR = BASE_DIR / "config"
SUPABASE_CONFIG_PATH = CONFIG_DIR / "supabase_config.json"


def load_config_counts() -> Dict[str, int]:
    """
    Lee conteos desde archivos de configuración JSON.

    Returns:
        Dict con conteos: reglas_negocio, reglas_validacion, sinonimos_argentinos, etc.
    """
    counts = {
        "reglas_negocio": 0,
        "reglas_validacion": 0,
        "sinonimos_argentinos": 0,
        "empresas_catalogo": 0,
    }

    # Reglas de negocio
    rules_path = CONFIG_DIR / "matching_rules_business.json"
    if rules_path.exists():
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Las reglas están en reglas_forzar_isco que es un dict
            rules = data.get("reglas_forzar_isco", {})
            # Contar solo las reglas activas
            counts["reglas_negocio"] = sum(
                1 for r in rules.values()
                if isinstance(r, dict) and r.get("activa", True)
            )

    # Reglas de validación
    val_path = CONFIG_DIR / "validation_rules.json"
    if val_path.exists():
        with open(val_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            rules = data.get("reglas_validacion", [])
            counts["reglas_validacion"] = len([r for r in rules if r.get("activa", True)])

    # Sinónimos argentinos
    sin_path = CONFIG_DIR / "sinonimos_argentinos_esco.json"
    if sin_path.exists():
        with open(sin_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Estructura: { "ocupaciones_titulo": { ... } }
            ocupaciones = data.get("ocupaciones_titulo", {})
            counts["sinonimos_argentinos"] = len(ocupaciones)

    # Catálogo de empresas
    emp_path = CONFIG_DIR / "empresas_catalogo.json"
    if emp_path.exists():
        with open(emp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            empleadores = len(data.get("empleadores", {}))
            intermediarios = len(data.get("intermediarios", {}))
            counts["empresas_catalogo"] = empleadores + intermediarios

    return counts


def load_db_metrics() -> Dict[str, Any]:
    """
    Lee métricas desde la base de datos.

    Returns:
        Dict con métricas de BD
    """
    metrics = {
        "total_runs": 0,
        "ofertas_con_matching": 0,
        "ultimo_run_id": None,
        "ultimo_run_fecha": None,
        "ultimo_run_ofertas": 0,
        "ultimo_run_metodo": {},
        "ofertas_validadas": 0,
        "ofertas_pendientes": 0,
        "learning_events": []
    }

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Total runs
        cur.execute("SELECT COUNT(*) FROM pipeline_runs")
        metrics["total_runs"] = cur.fetchone()[0]

        # Ofertas con matching (distintas)
        cur.execute("SELECT COUNT(DISTINCT id_oferta) FROM ofertas_esco_matching")
        metrics["ofertas_con_matching"] = cur.fetchone()[0]

        # Último run
        cur.execute("""
            SELECT run_id, timestamp, ofertas_count, metricas_detalle
            FROM pipeline_runs
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            metrics["ultimo_run_id"] = row["run_id"]
            metrics["ultimo_run_fecha"] = row["timestamp"]
            metrics["ultimo_run_ofertas"] = row["ofertas_count"] or 0
            if row["metricas_detalle"]:
                metrics["ultimo_run_metodo"] = json.loads(row["metricas_detalle"])

        # Ofertas validadas vs pendientes
        cur.execute("""
            SELECT estado_validacion, COUNT(*) as cnt
            FROM ofertas_esco_matching
            GROUP BY estado_validacion
        """)
        for row in cur.fetchall():
            estado = row["estado_validacion"] or "pendiente"
            if estado == "validado":
                metrics["ofertas_validadas"] = row["cnt"]
            else:
                metrics["ofertas_pendientes"] = row["cnt"]

        # Últimos eventos de aprendizaje
        cur.execute("""
            SELECT evento_tipo, config_modificado, descripcion, delta, timestamp
            FROM learning_history
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        metrics["learning_events"] = [
            {
                "tipo": row["evento_tipo"],
                "config": row["config_modificado"],
                "desc": row["descripcion"],
                "delta": row["delta"],
                "fecha": row["timestamp"]
            }
            for row in cur.fetchall()
        ]

        conn.close()

    except Exception as e:
        print(f"[SYNC] Error leyendo BD: {e}")

    return metrics


def calculate_learning_rate(db_metrics: Dict) -> str:
    """
    Calcula tasa de aprendizaje del último run.

    Returns:
        String con formato "X.X% (N reglas / M ofertas)"
    """
    # Por ahora retornamos una aproximación
    # En futuro: calcular delta_reglas del último run vs anterior
    ofertas = db_metrics.get("ultimo_run_ofertas", 0)
    if ofertas == 0:
        return "N/A"

    # Asumimos 0 reglas nuevas si no hay eventos recientes
    eventos = db_metrics.get("learning_events", [])
    reglas_nuevas = sum(
        e.get("delta", 0)
        for e in eventos
        if e.get("tipo") == "regla_agregada"
    )

    tasa = (reglas_nuevas / ofertas * 100) if ofertas > 0 else 0
    return f"{tasa:.1f}% ({reglas_nuevas} reglas / {ofertas} ofertas)"


def update_yaml_section(content: str, section_key: str, updates: Dict[str, Any]) -> str:
    """
    Actualiza una sección específica del YAML preservando estructura.

    Args:
        content: Contenido YAML como string
        section_key: Clave de la sección a actualizar (ej: "conteos")
        updates: Dict con pares clave: valor a actualizar

    Returns:
        Contenido YAML actualizado
    """
    lines = content.split('\n')
    result = []
    in_section = False
    section_indent = 0

    for line in lines:
        # Detectar inicio de sección
        if line.strip().startswith(f"{section_key}:"):
            in_section = True
            section_indent = len(line) - len(line.lstrip())
            result.append(line)
            continue

        # Si estamos en la sección
        if in_section:
            current_indent = len(line) - len(line.lstrip())

            # Si encontramos otra sección principal (mismo o menor indent)
            if line.strip() and not line.strip().startswith('#') and current_indent <= section_indent and ':' in line:
                in_section = False
                result.append(line)
                continue

            # Buscar si esta línea es una clave a actualizar
            updated = False
            for key, value in updates.items():
                # Patrón: "  key: value" o "  key: value  # comentario"
                pattern = rf'^(\s*)({key}):\s*.*$'
                match = re.match(pattern, line)
                if match:
                    indent = match.group(1)
                    # Preservar comentario si existe
                    comment_match = re.search(r'#.*$', line)
                    comment = comment_match.group(0) if comment_match else ""

                    # Formatear valor
                    if isinstance(value, str):
                        formatted_value = f'"{value}"' if ' ' in value or ':' in value else value
                    else:
                        formatted_value = value

                    if comment:
                        new_line = f"{indent}{key}: {formatted_value}  {comment}"
                    else:
                        new_line = f"{indent}{key}: {formatted_value}"

                    result.append(new_line)
                    updated = True
                    break

            if not updated:
                result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


def get_phase1_metrics() -> Dict[str, Any]:
    """
    Métricas de Fase 1: Adquisición (Scraping).

    Returns:
        Dict con métricas de scraping
    """
    metrics = {
        "ofertas_totales": 0,
        "ultimo_scraping": None,
        "dias_desde_scraping": None,
        "ofertas_activas": 0,
        "ofertas_cerradas": 0,
        "fuentes": {}
    }

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Total ofertas
        cur.execute("SELECT COUNT(*) FROM ofertas")
        metrics["ofertas_totales"] = cur.fetchone()[0]

        # Ofertas activas vs cerradas
        cur.execute("""
            SELECT estado_oferta, COUNT(*) as cnt
            FROM ofertas
            GROUP BY estado_oferta
        """)
        for row in cur.fetchall():
            estado = row["estado_oferta"] or "activa"
            if estado == "activa":
                metrics["ofertas_activas"] = row["cnt"]
            else:
                metrics["ofertas_cerradas"] += row["cnt"]

        # Último scraping (fecha más reciente en ofertas)
        cur.execute("SELECT MAX(scrapeado_en) FROM ofertas")
        row = cur.fetchone()
        if row and row[0]:
            metrics["ultimo_scraping"] = row[0][:10]  # Solo fecha
            try:
                last_date = datetime.strptime(row[0][:10], "%Y-%m-%d")
                metrics["dias_desde_scraping"] = (datetime.now() - last_date).days
            except:
                pass

        # Ofertas por fuente (portal)
        cur.execute("""
            SELECT portal, COUNT(*) as cnt
            FROM ofertas
            GROUP BY portal
        """)
        for row in cur.fetchall():
            metrics["fuentes"][row["portal"] or "unknown"] = row["cnt"]

        conn.close()

    except Exception as e:
        metrics["error"] = str(e)

    return metrics


def get_phase2_metrics() -> Dict[str, Any]:
    """
    Métricas de Fase 2: Procesamiento (NLP + Matching + Validación).

    Returns:
        Dict con métricas de procesamiento
    """
    metrics = {
        "ofertas_con_nlp": 0,
        "ofertas_sin_nlp": 0,
        "ofertas_con_matching": 0,
        "ofertas_pendientes_matching": 0,
        "ofertas_validadas": 0,
        "ofertas_pendientes_validacion": 0,
        "errores_sin_resolver": 0,
        "ultimo_run": None,
        "dias_desde_run": None,
        "tasa_convergencia": "N/A",
        "reglas_negocio": 0
    }

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Ofertas con NLP procesado
        cur.execute("SELECT COUNT(*) FROM ofertas_nlp")
        metrics["ofertas_con_nlp"] = cur.fetchone()[0]

        # Ofertas sin NLP
        cur.execute("""
            SELECT COUNT(*) FROM ofertas o
            WHERE NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = CAST(o.id_oferta AS TEXT))
        """)
        metrics["ofertas_sin_nlp"] = cur.fetchone()[0]

        # Ofertas con matching
        cur.execute("SELECT COUNT(DISTINCT id_oferta) FROM ofertas_esco_matching")
        metrics["ofertas_con_matching"] = cur.fetchone()[0]

        # Ofertas pendientes de matching (tienen NLP pero no matching)
        cur.execute("""
            SELECT COUNT(*) FROM ofertas_nlp n
            WHERE NOT EXISTS (SELECT 1 FROM ofertas_esco_matching m WHERE m.id_oferta = CAST(n.id_oferta AS TEXT))
        """)
        metrics["ofertas_pendientes_matching"] = cur.fetchone()[0]

        # Ofertas validadas vs pendientes
        cur.execute("""
            SELECT estado_validacion, COUNT(*) as cnt
            FROM ofertas_esco_matching
            GROUP BY estado_validacion
        """)
        for row in cur.fetchall():
            estado = row["estado_validacion"] or "pendiente"
            if estado == "validado":
                metrics["ofertas_validadas"] = row["cnt"]
            else:
                metrics["ofertas_pendientes_validacion"] += row["cnt"]

        # Errores sin resolver
        cur.execute("""
            SELECT COUNT(*) FROM validation_errors
            WHERE resuelto = 0 OR resuelto IS NULL
        """)
        metrics["errores_sin_resolver"] = cur.fetchone()[0]

        # Último run
        cur.execute("""
            SELECT run_id, timestamp, delta_reglas, ofertas_count
            FROM pipeline_runs
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            metrics["ultimo_run"] = row["run_id"]
            if row["timestamp"]:
                try:
                    last_date = datetime.fromisoformat(row["timestamp"].replace("Z", ""))
                    metrics["dias_desde_run"] = (datetime.now() - last_date).days
                except:
                    pass
            # Tasa de convergencia
            if row["ofertas_count"] and row["ofertas_count"] > 0:
                delta = row["delta_reglas"] or 0
                tasa = (delta / row["ofertas_count"]) * 100
                metrics["tasa_convergencia"] = f"{tasa:.1f}%"

        conn.close()

        # Reglas de negocio (desde config)
        config_counts = load_config_counts()
        metrics["reglas_negocio"] = config_counts["reglas_negocio"]

    except Exception as e:
        metrics["error"] = str(e)

    return metrics


def get_phase3_metrics() -> Dict[str, Any]:
    """
    Métricas de Fase 3: Presentación (Supabase + Dashboard).

    Returns:
        Dict con métricas de presentación
    """
    import urllib.request
    import json as json_module

    metrics = {
        "ultimo_sync_supabase": None,
        "dias_desde_sync": None,
        "ofertas_sincronizadas": 0,
        "ofertas_pendientes_sync": 0,
        "dashboard_url": "https://mol-nextjs.vercel.app/"
    }

    # Primero intentar consultar Supabase directamente
    try:
        supabase_url = "https://uywzoyhjjofsvvsrrnek.supabase.co"
        service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV5d3pveWhqam9mc3Z2c3JybmVrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODQ5NDUyNiwiZXhwIjoyMDg0MDcwNTI2fQ.wSqtg8rtnbN3howe7_A0HLeEuUwtciGxo71IiKd7Nh4"

        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/ofertas?select=count",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Prefer": "count=exact"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json_module.loads(response.read().decode())
            if data and len(data) > 0 and "count" in data[0]:
                metrics["ofertas_sincronizadas"] = data[0]["count"]
    except Exception:
        # Si falla Supabase, usar conteo local como fallback
        pass

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Buscar último sync en learning_history o alguna tabla de sync
        cur.execute("""
            SELECT timestamp, descripcion FROM learning_history
            WHERE evento_tipo LIKE '%sync%' OR descripcion LIKE '%supabase%'
            ORDER BY timestamp DESC LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            metrics["ultimo_sync_supabase"] = row["timestamp"][:10] if row["timestamp"] else None

        # Si no pudimos consultar Supabase, usar conteo local
        if metrics["ofertas_sincronizadas"] == 0:
            cur.execute("""
                SELECT COUNT(*) FROM ofertas_esco_matching
                WHERE estado_validacion IN ('validado', 'validado_claude', 'validado_humano')
            """)
            metrics["ofertas_sincronizadas"] = cur.fetchone()[0]

        conn.close()

    except Exception as e:
        metrics["error"] = str(e)

    return metrics


def determine_suggested_phase(p1: Dict, p2: Dict, p3: Dict) -> Tuple[int, str, str]:
    """
    Determina qué fase necesita atención basado en las métricas.

    Returns:
        Tuple (fase_num, fase_nombre, razón)
    """
    # Prioridades:
    # 1. Errores sin resolver en Fase 2 (bloquean producción)
    # 2. Ofertas pendientes de validación en Fase 2
    # 3. Scraping desactualizado (>3 días) en Fase 1
    # 4. Sync desactualizado en Fase 3
    # 5. Ofertas sin NLP en Fase 2

    # Fase 2: Errores sin resolver
    if p2.get("errores_sin_resolver", 0) > 0:
        return (2, "Procesamiento", f"{p2['errores_sin_resolver']} errores sin resolver")

    # Fase 2: Muchas ofertas pendientes validación
    if p2.get("ofertas_pendientes_validacion", 0) > 50:
        return (2, "Procesamiento", f"{p2['ofertas_pendientes_validacion']} ofertas pendientes validación")

    # Fase 1: Scraping desactualizado
    dias_scraping = p1.get("dias_desde_scraping")
    if dias_scraping is not None and dias_scraping > 3:
        return (1, "Adquisición", f"Último scraping hace {dias_scraping} días")

    # Fase 3: Sync pendiente
    if p3.get("ofertas_pendientes_sync", 0) > 0:
        return (3, "Presentación", f"{p3['ofertas_pendientes_sync']} ofertas pendientes sync")

    # Fase 2: Ofertas sin procesar
    if p2.get("ofertas_sin_nlp", 0) > 100:
        return (2, "Procesamiento", f"{p2['ofertas_sin_nlp']} ofertas sin NLP")

    if p2.get("ofertas_pendientes_matching", 0) > 50:
        return (2, "Procesamiento", f"{p2['ofertas_pendientes_matching']} ofertas pendientes matching")

    # Todo OK
    return (0, "Ninguna urgente", "Sistema al día")


def generate_phase_report(output_for_claude: bool = True) -> str:
    """
    Genera reporte de estado de las 3 fases.

    Args:
        output_for_claude: Si True, formatea para contexto de Claude

    Returns:
        String con el reporte
    """
    p1 = get_phase1_metrics()
    p2 = get_phase2_metrics()
    p3 = get_phase3_metrics()

    suggested_phase, phase_name, reason = determine_suggested_phase(p1, p2, p3)

    if output_for_claude:
        # Formato compacto para contexto de Claude (ASCII)
        report = f"""
=== MOL - ESTADO DE FASES ===

FASE 1 - ADQUISICION (Scraping)
  Ofertas totales: {p1['ofertas_totales']:,}
  Activas: {p1['ofertas_activas']:,} | Cerradas: {p1['ofertas_cerradas']:,}
  Ultimo scraping: {p1['ultimo_scraping'] or 'N/A'} ({p1['dias_desde_scraping'] or '?'} dias)

FASE 2 - PROCESAMIENTO (NLP + Matching)
  Con NLP: {p2['ofertas_con_nlp']:,} | Sin NLP: {p2['ofertas_sin_nlp']:,}
  Con Matching: {p2['ofertas_con_matching']:,} | Pendientes: {p2['ofertas_pendientes_matching']:,}
  Validadas: {p2['ofertas_validadas']:,} | Pendientes validacion: {p2['ofertas_pendientes_validacion']:,}
  Errores sin resolver: {p2['errores_sin_resolver']}
  Reglas negocio: {p2['reglas_negocio']} | Convergencia: {p2['tasa_convergencia']}
  Ultimo run: {p2['ultimo_run'] or 'N/A'}

FASE 3 - PRESENTACION (Dashboard)
  Ofertas en Supabase: {p3['ofertas_sincronizadas']:,}
  Dashboard: {p3['dashboard_url']}

>>> SUGERENCIA: Fase {suggested_phase} ({phase_name}) - {reason}
"""
    else:
        # Formato detallado para humanos (ASCII compatible)
        report = f"""
================================================================
              MOL - ESTADO DE LAS 3 FASES
================================================================

--- FASE 1: ADQUISICION (Scraping) ---
  Ofertas totales:    {p1['ofertas_totales']:>10,}
  Ofertas activas:    {p1['ofertas_activas']:>10,}
  Ofertas cerradas:   {p1['ofertas_cerradas']:>10,}
  Ultimo scraping:    {str(p1['ultimo_scraping'] or 'N/A'):>10}  ({p1['dias_desde_scraping'] or '?'} dias)

--- FASE 2: PROCESAMIENTO (NLP + Matching) ---
  Con NLP:            {p2['ofertas_con_nlp']:>10,}
  Sin NLP:            {p2['ofertas_sin_nlp']:>10,}
  Con Matching:       {p2['ofertas_con_matching']:>10,}
  Pendientes Match:   {p2['ofertas_pendientes_matching']:>10,}
  Validadas:          {p2['ofertas_validadas']:>10,}
  Pend. Validacion:   {p2['ofertas_pendientes_validacion']:>10,}
  Errores pendientes: {p2['errores_sin_resolver']:>10}
  Reglas negocio:     {p2['reglas_negocio']:>10}
  Convergencia:       {p2['tasa_convergencia']:>10}
  Ultimo run:         {str(p2['ultimo_run'] or 'N/A'):>10}

--- FASE 3: PRESENTACION (Dashboard) ---
  En Supabase:        {p3['ofertas_sincronizadas']:>10,}
  Pendientes sync:    {p3['ofertas_pendientes_sync']:>10,}
  Dashboard:          {p3['dashboard_url']}

================================================================
>>> SUGERENCIA: Fase {suggested_phase} ({phase_name})
>>> Razon: {reason}
================================================================
"""

    return report.strip()


def sync_to_supabase(p1: Dict, p2: Dict, p3: Dict, suggested: Tuple[int, str, str], verbose: bool = True) -> bool:
    """
    Sincroniza métricas de fases a Supabase para colaboración.

    Args:
        p1: Métricas de Fase 1
        p2: Métricas de Fase 2
        p3: Métricas de Fase 3
        suggested: Tuple (fase_num, fase_nombre, razon)
        verbose: Mostrar progreso

    Returns:
        True si se sincronizó correctamente
    """
    # Verificar config
    if not SUPABASE_CONFIG_PATH.exists():
        if verbose:
            print("[SUPABASE] Config no encontrado, saltando sync")
        return False

    try:
        with open(SUPABASE_CONFIG_PATH, 'r') as f:
            config = json.load(f)

        if not config.get('url') or not config.get('anon_key'):
            if verbose:
                print("[SUPABASE] Config incompleto, saltando sync")
            return False

        # Importar supabase
        try:
            from supabase import create_client
        except ImportError:
            if verbose:
                print("[SUPABASE] Librería no instalada (pip install supabase)")
            return False

        # Conectar
        client = create_client(config['url'], config['anon_key'])

        # Preparar datos
        data = {
            # Fase 1
            "fase1_ofertas_totales": p1.get("ofertas_totales", 0),
            "fase1_ofertas_activas": p1.get("ofertas_activas", 0),
            "fase1_ofertas_cerradas": p1.get("ofertas_cerradas", 0),
            "fase1_ultimo_scraping": p1.get("ultimo_scraping"),
            "fase1_dias_desde_scraping": p1.get("dias_desde_scraping"),
            "fase1_fuentes": p1.get("fuentes", {}),

            # Fase 2
            "fase2_con_nlp": p2.get("ofertas_con_nlp", 0),
            "fase2_sin_nlp": p2.get("ofertas_sin_nlp", 0),
            "fase2_con_matching": p2.get("ofertas_con_matching", 0),
            "fase2_pendientes_matching": p2.get("ofertas_pendientes_matching", 0),
            "fase2_validadas": p2.get("ofertas_validadas", 0),
            "fase2_pendientes_validacion": p2.get("ofertas_pendientes_validacion", 0),
            "fase2_errores_sin_resolver": p2.get("errores_sin_resolver", 0),
            "fase2_reglas_negocio": p2.get("reglas_negocio", 0),
            "fase2_tasa_convergencia": p2.get("tasa_convergencia", "N/A"),
            "fase2_ultimo_run": p2.get("ultimo_run"),

            # Fase 3
            "fase3_ofertas_supabase": p3.get("ofertas_sincronizadas", 0),
            "fase3_pendientes_sync": p3.get("ofertas_pendientes_sync", 0),

            # Sugerencia
            "fase_sugerida": suggested[0],
            "fase_sugerida_nombre": suggested[1],
            "fase_sugerida_razon": suggested[2],

            # Metadata
            "sync_version": "2.1"
        }

        # Insertar
        result = client.table("sistema_estado").insert(data).execute()

        if verbose:
            print(f"[SUPABASE] Estado sincronizado (fase sugerida: {suggested[0]})")

        return True

    except Exception as e:
        error_str = str(e)

        # Detectar si la tabla no existe
        if "PGRST205" in error_str or "Could not find the table" in error_str:
            if verbose:
                print("[SUPABASE] Tabla 'sistema_estado' no existe.")
                print("           Ejecutar migracion: migrations/010_create_sistema_estado.sql")
                print("           en Supabase SQL Editor: https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek/sql")
            return False

        if verbose:
            print(f"[SUPABASE] Error: {e}")
        return False


def sync_learnings_yaml(verbose: bool = True) -> bool:
    """
    Sincroniza métricas desde BD/configs hacia learnings.yaml.

    Args:
        verbose: Mostrar progreso

    Returns:
        True si se actualizó correctamente
    """
    if verbose:
        print("[SYNC] Sincronizando learnings.yaml...")

    # Cargar datos
    config_counts = load_config_counts()
    db_metrics = load_db_metrics()

    if verbose:
        print(f"[SYNC] Conteos config: {config_counts}")
        print(f"[SYNC] Métricas BD: runs={db_metrics['total_runs']}, matching={db_metrics['ofertas_con_matching']}")

    # Leer YAML actual
    if not LEARNINGS_PATH.exists():
        print(f"[SYNC] Error: {LEARNINGS_PATH} no existe")
        return False

    with open(LEARNINGS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Actualizar sección "conteos"
    conteos_updates = {
        "reglas_negocio": config_counts["reglas_negocio"],
        "reglas_validacion": config_counts["reglas_validacion"],
        "sinonimos_argentinos": config_counts["sinonimos_argentinos"],
        "empresas_catalogo": config_counts["empresas_catalogo"],
        "ultima_verificacion": datetime.now().strftime("%Y-%m-%d"),
    }
    content = update_yaml_section(content, "conteos", conteos_updates)

    # Actualizar sección "estadisticas_actuales"
    stats_updates = {
        "ofertas_validadas": db_metrics["ofertas_validadas"],
        "ofertas_pendientes": db_metrics["ofertas_pendientes"],
        "reglas_negocio": config_counts["reglas_negocio"],
        "tasa_aprendizaje": calculate_learning_rate(db_metrics),
    }
    content = update_yaml_section(content, "estadisticas_actuales", stats_updates)

    # Actualizar sección "learning_evolution"
    evolution_updates = {
        "total_runs": db_metrics["total_runs"],
        "ofertas_con_matching": db_metrics["ofertas_con_matching"],
        "reglas_actual": config_counts["reglas_negocio"],
    }
    content = update_yaml_section(content, "learning_evolution", evolution_updates)

    # Actualizar fecha en current_state
    current_updates = {
        "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    content = update_yaml_section(content, "current_state", current_updates)

    # Guardar
    with open(LEARNINGS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    if verbose:
        print(f"[SYNC] learnings.yaml actualizado")
        print(f"[SYNC]   - reglas_negocio: {config_counts['reglas_negocio']}")
        print(f"[SYNC]   - total_runs: {db_metrics['total_runs']}")
        print(f"[SYNC]   - ofertas_matching: {db_metrics['ofertas_con_matching']}")

    return True


def main():
    """Entry point para ejecución directa."""
    import argparse

    parser = argparse.ArgumentParser(description="Sincronizar learnings.yaml y mostrar estado de fases")
    parser.add_argument("--quiet", action="store_true", help="Solo sync, sin reporte de fases")
    parser.add_argument("--report-only", action="store_true", help="Solo mostrar reporte, sin sync")
    parser.add_argument("--human", action="store_true", help="Formato detallado para humanos")
    parser.add_argument("--no-supabase", action="store_true", help="No sincronizar a Supabase")
    parser.add_argument("--supabase-only", action="store_true", help="Solo sincronizar a Supabase")
    args = parser.parse_args()

    # Obtener métricas de fases (necesarias para Supabase y reporte)
    p1 = get_phase1_metrics()
    p2 = get_phase2_metrics()
    p3 = get_phase3_metrics()
    suggested = determine_suggested_phase(p1, p2, p3)

    # Sync YAML local
    if not args.report_only and not args.supabase_only:
        sync_learnings_yaml(verbose=False)

    # Sync a Supabase (para colaboración)
    if not args.no_supabase and not args.report_only:
        sync_to_supabase(p1, p2, p3, suggested, verbose=not args.quiet)

    # Generar y mostrar reporte de fases (stdout va a Claude como contexto)
    if not args.quiet and not args.supabase_only:
        report = generate_phase_report(output_for_claude=not args.human)
        print(report)

    return 0


if __name__ == "__main__":
    exit(main())
