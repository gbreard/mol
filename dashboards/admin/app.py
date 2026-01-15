"""
MOL Dashboard Admin - Monitor de Ofertas Laborales
Dashboard Streamlit con 5 tabs para monitoreo del sistema
Fase 1: Funciones ejecutables (MOL-55)
"""
import streamlit as st
import sqlite3
import json
import subprocess
import threading
import signal
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Agregar path para imports locales
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.scraping.keyword_optimizer import KeywordOptimizer

# Configuracion de paths
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
TRACKING_PATH = BASE_DIR / "01_sources" / "bumeran" / "tracking" / "scraped_ids.json"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_manual_v2.json"
EXPERIMENTS_PATH = BASE_DIR / "metrics" / "experiments.json"
TIMING_LOGS_PATH = BASE_DIR / "metrics" / "timing_logs.jsonl"
EXPORTS_DIR = BASE_DIR / "exports"

# Scripts paths
NLP_SCRIPT = BASE_DIR / "database" / "process_nlp_from_db_v11.py"
TEST_SCRIPT = BASE_DIR / "tests" / "matching" / "test_gold_set_manual.py"

st.set_page_config(
    page_title="MOL Admin",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== SESSION STATE ==============
if "process_running" not in st.session_state:
    st.session_state.process_running = False
if "process_name" not in st.session_state:
    st.session_state.process_name = ""
if "process_output" not in st.session_state:
    st.session_state.process_output = []
if "process_handle" not in st.session_state:
    st.session_state.process_handle = None
if "last_test_result" not in st.session_state:
    st.session_state.last_test_result = None


def get_db_connection():
    """Conexion a SQLite"""
    return sqlite3.connect(str(DB_PATH))


def run_command(cmd, name, cwd=None):
    """Ejecuta un comando y captura output"""
    st.session_state.process_running = True
    st.session_state.process_name = name
    st.session_state.process_output = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd or str(BASE_DIR),
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        st.session_state.process_handle = process

        for line in iter(process.stdout.readline, ''):
            if line:
                st.session_state.process_output.append(line.strip())

        process.wait()
        return process.returncode
    except Exception as e:
        st.session_state.process_output.append(f"ERROR: {str(e)}")
        return -1
    finally:
        st.session_state.process_running = False
        st.session_state.process_handle = None


def run_command_sync(cmd, cwd=None):
    """Ejecuta comando sincronico y retorna output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or str(BASE_DIR),
            timeout=300
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT: El proceso tardo mas de 5 minutos"
    except Exception as e:
        return -1, f"ERROR: {str(e)}"


def stop_process():
    """Detiene el proceso en ejecucion"""
    if st.session_state.process_handle:
        try:
            if sys.platform == "win32":
                st.session_state.process_handle.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                st.session_state.process_handle.terminate()
            st.session_state.process_output.append(">>> Proceso detenido por usuario")
        except Exception as e:
            st.session_state.process_output.append(f"Error al detener: {e}")
        finally:
            st.session_state.process_running = False
            st.session_state.process_handle = None


@st.cache_data(ttl=60)
def get_ofertas_stats():
    """Estadisticas generales de ofertas"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM ofertas")
    stats["total_ofertas"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ofertas WHERE estado_oferta = 'activa'")
    stats["ofertas_activas"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT DATE(scrapeado_en) as fecha, COUNT(*) as cnt
        FROM ofertas
        WHERE scrapeado_en IS NOT NULL
        GROUP BY DATE(scrapeado_en)
        ORDER BY fecha DESC
        LIMIT 30
    """)
    stats["ofertas_por_fecha"] = cursor.fetchall()

    cursor.execute("""
        SELECT provincia_normalizada, COUNT(*) as cnt
        FROM ofertas
        WHERE provincia_normalizada IS NOT NULL
        GROUP BY provincia_normalizada
        ORDER BY cnt DESC
        LIMIT 10
    """)
    stats["ofertas_por_provincia"] = cursor.fetchall()

    # Ultimas 50 ofertas
    cursor.execute("""
        SELECT id_oferta, titulo, empresa, provincia_normalizada, scrapeado_en
        FROM ofertas
        ORDER BY scrapeado_en DESC
        LIMIT 50
    """)
    stats["ultimas_ofertas"] = cursor.fetchall()

    conn.close()
    return stats


@st.cache_data(ttl=60)
def get_tracking_stats():
    """Estadisticas de tracking de IDs"""
    if not TRACKING_PATH.exists():
        return {"total_ids": 0, "ids_por_fecha": []}

    with open(TRACKING_PATH, "r") as f:
        data = json.load(f)

    scraped_ids = data.get("scraped_ids", {})

    ids_por_fecha = {}
    for id_oferta, fecha_str in scraped_ids.items():
        fecha = fecha_str.split("T")[0]
        ids_por_fecha[fecha] = ids_por_fecha.get(fecha, 0) + 1

    return {
        "total_ids": len(scraped_ids),
        "ids_por_fecha": sorted(ids_por_fecha.items(), reverse=True)[:30]
    }


@st.cache_data(ttl=60)
def get_nlp_stats():
    """Estadisticas de procesamiento NLP"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
    stats["total_nlp"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT nlp_version, COUNT(*) as cnt
        FROM ofertas_nlp
        GROUP BY nlp_version
        ORDER BY cnt DESC
    """)
    stats["por_version"] = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE n.id_oferta IS NULL
    """)
    stats["sin_nlp"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            SUM(CASE WHEN experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END) as exp_min,
            SUM(CASE WHEN nivel_educativo IS NOT NULL THEN 1 ELSE 0 END) as nivel_edu,
            SUM(CASE WHEN skills_tecnicas_list IS NOT NULL AND skills_tecnicas_list != '[]' THEN 1 ELSE 0 END) as skills,
            SUM(CASE WHEN salario_min IS NOT NULL THEN 1 ELSE 0 END) as salario,
            COUNT(*) as total
        FROM ofertas_nlp
    """)
    row = cursor.fetchone()
    stats["cobertura_campos"] = {
        "experiencia": row[0] or 0,
        "educacion": row[1] or 0,
        "skills": row[2] or 0,
        "salario": row[3] or 0,
        "total": row[4] or 1
    }

    conn.close()
    return stats


@st.cache_data(ttl=60)
def get_matching_stats():
    """Estadisticas de matching ESCO"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
    stats["total_matching"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            AVG(score_final_ponderado) as avg_score,
            SUM(CASE WHEN match_confirmado = 1 THEN 1 ELSE 0 END) as confirmados,
            SUM(CASE WHEN requiere_revision = 1 THEN 1 ELSE 0 END) as revision
        FROM ofertas_esco_matching
    """)
    row = cursor.fetchone()
    stats["avg_score"] = row[0] or 0
    stats["confirmados"] = row[1] or 0
    stats["requiere_revision"] = row[2] or 0

    cursor.execute("""
        SELECT matching_version, COUNT(*) as cnt
        FROM ofertas_esco_matching
        GROUP BY matching_version
        ORDER BY cnt DESC
    """)
    stats["por_version"] = cursor.fetchall()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN score_final_ponderado >= 0.60 THEN 1 ELSE 0 END) as alto,
            SUM(CASE WHEN score_final_ponderado >= 0.50 AND score_final_ponderado < 0.60 THEN 1 ELSE 0 END) as medio,
            SUM(CASE WHEN score_final_ponderado < 0.50 THEN 1 ELSE 0 END) as bajo
        FROM ofertas_esco_matching
    """)
    row = cursor.fetchone()
    stats["score_distribution"] = {
        "alto": row[0] or 0,
        "medio": row[1] or 0,
        "bajo": row[2] or 0
    }

    conn.close()
    return stats


@st.cache_data(ttl=10)
def get_gold_set_stats():
    """Estadisticas del gold set"""
    if not GOLD_SET_PATH.exists():
        return {"total": 0, "correctos": 0, "precision": 0, "errores_por_tipo": {}, "detalle": []}

    with open(GOLD_SET_PATH, "r", encoding="utf-8") as f:
        gold_set = json.load(f)

    total = len(gold_set)
    correctos = sum(1 for item in gold_set if item.get("esco_ok", False))

    errores_por_tipo = {}
    for item in gold_set:
        if not item.get("esco_ok", False):
            tipo = item.get("tipo_error", "sin_clasificar")
            errores_por_tipo[tipo] = errores_por_tipo.get(tipo, 0) + 1

    return {
        "total": total,
        "correctos": correctos,
        "precision": (correctos / total * 100) if total > 0 else 0,
        "errores_por_tipo": errores_por_tipo,
        "detalle": gold_set
    }


@st.cache_data(ttl=60)
def get_experiments():
    """Obtener experimentos registrados"""
    if not EXPERIMENTS_PATH.exists():
        return {}

    with open(EXPERIMENTS_PATH, "r") as f:
        return json.load(f)


@st.cache_data(ttl=60)
def get_timing_logs(limit=100):
    """Obtener logs de timing"""
    if not TIMING_LOGS_PATH.exists():
        return []

    logs = []
    with open(TIMING_LOGS_PATH, "r") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    return logs[-limit:]


@st.cache_data(ttl=60)
def get_exports_status():
    """Estado de exports a S3"""
    if not EXPORTS_DIR.exists():
        return {"snapshots": [], "latest": None}

    snapshots = []
    for item in EXPORTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("2"):
            files = list(item.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            snapshots.append({
                "fecha": item.name,
                "archivos": len(files),
                "tamano_mb": total_size / (1024 * 1024)
            })

    latest_path = EXPORTS_DIR / "latest.json"
    latest = None
    if latest_path.exists():
        with open(latest_path, "r") as f:
            latest = json.load(f)

    return {
        "snapshots": sorted(snapshots, key=lambda x: x["fecha"], reverse=True),
        "latest": latest
    }


# ============== SIDEBAR ==============
with st.sidebar:
    st.header("Estado del Sistema")

    if st.session_state.process_running:
        st.error(f"🔴 Proceso activo")
        st.info(f"**{st.session_state.process_name}**")
        with st.spinner("Ejecutando..."):
            pass
        if st.button("🛑 Detener Proceso", type="primary", use_container_width=True):
            stop_process()
            st.rerun()
    else:
        st.success("🟢 Sistema disponible")

    st.divider()

    # Quick stats
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
        nlp = cursor.fetchone()[0]
        conn.close()

        st.metric("Ofertas BD", f"{total:,}")
        st.metric("Con NLP", f"{nlp:,}")
        st.metric("Pendientes", f"{total - nlp:,}")
    except Exception as e:
        st.warning(f"Error BD: {e}")

    st.divider()
    if st.button("🔄 Refrescar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ============== HEADER ==============
st.title("📊 MOL Dashboard Admin")
st.caption("Monitor de Ofertas Laborales - Centro de Control")


# ============== TABS ==============
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Scraping",
    "🧠 Pipeline NLP",
    "✅ Tests",
    "☁️ S3 Sync",
    "📋 Logs",
    "🔑 Keywords"
])


# ============== TAB 1: SCRAPING ==============
with tab1:
    st.header("Estado del Scraping")

    # Info y refresh
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("**Para ejecutar scraping completo:** `python run_scheduler.py --test`")
    with col2:
        if st.button("🔄 Refrescar", use_container_width=True, key="refresh_scraping"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # Metricas
    st.subheader("Metricas")
    ofertas_stats = get_ofertas_stats()
    tracking_stats = get_tracking_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Ofertas BD", f"{ofertas_stats['total_ofertas']:,}")
    with col2:
        st.metric("Ofertas Activas", f"{ofertas_stats['ofertas_activas']:,}")
    with col3:
        st.metric("IDs en Tracking", f"{tracking_stats['total_ids']:,}")
    with col4:
        cobertura = (ofertas_stats['total_ofertas'] / tracking_stats['total_ids'] * 100) if tracking_stats['total_ids'] > 0 else 0
        st.metric("Cobertura", f"{cobertura:.1f}%")

    st.divider()

    # Graficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ofertas por Fecha")
        if ofertas_stats["ofertas_por_fecha"]:
            df = pd.DataFrame(ofertas_stats["ofertas_por_fecha"], columns=["Fecha", "Cantidad"])
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            st.bar_chart(df.set_index("Fecha"))
        else:
            st.info("Sin datos")

    with col2:
        st.subheader("Top 10 Provincias")
        if ofertas_stats["ofertas_por_provincia"]:
            df = pd.DataFrame(ofertas_stats["ofertas_por_provincia"], columns=["Provincia", "Cantidad"])
            st.bar_chart(df.set_index("Provincia"))
        else:
            st.info("Sin datos")

    st.divider()

    # Ultimas ofertas
    st.subheader("Ultimas 50 Ofertas")
    if ofertas_stats["ultimas_ofertas"]:
        df = pd.DataFrame(
            ofertas_stats["ultimas_ofertas"],
            columns=["ID", "Titulo", "Empresa", "Provincia", "Fecha"]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)


# ============== TAB 2: PIPELINE NLP ==============
with tab2:
    st.header("Pipeline NLP")

    # Acciones
    st.subheader("Acciones")
    col1, col2, col3 = st.columns(3)

    nlp_stats = get_nlp_stats()

    with col1:
        limit = st.number_input("Limite de ofertas", min_value=10, max_value=1000, value=100, step=10)

    with col2:
        st.write("")  # Espaciador
        if st.button("🟢 Procesar NLP",
                     disabled=st.session_state.process_running,
                     use_container_width=True,
                     help=f"Ejecuta process_nlp_from_db_v10.py --limit {limit}"):
            with st.spinner(f"Procesando {limit} ofertas con NLP..."):
                code, output = run_command_sync(
                    [sys.executable, str(NLP_SCRIPT), "--limit", str(limit)]
                )
            if code == 0:
                st.success(f"Procesamiento completado")
            else:
                st.error(f"Error (codigo {code})")
            st.session_state.nlp_output = output
            st.cache_data.clear()

    with col3:
        st.write("")

    # Barra de progreso
    total_ofertas = nlp_stats["total_nlp"] + nlp_stats["sin_nlp"]
    if total_ofertas > 0:
        progreso = nlp_stats["total_nlp"] / total_ofertas
        st.progress(progreso)
        st.caption(f"Progreso: {nlp_stats['total_nlp']:,} / {total_ofertas:,} ({progreso*100:.1f}%)")

    # Output
    if hasattr(st.session_state, 'nlp_output') and st.session_state.nlp_output:
        with st.expander("📄 Output NLP", expanded=True):
            st.code(st.session_state.nlp_output, language="text")

    st.divider()

    # Metricas
    st.subheader("Metricas")
    matching_stats = get_matching_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ofertas con NLP", f"{nlp_stats['total_nlp']:,}")
    with col2:
        st.metric("Sin Procesar", f"{nlp_stats['sin_nlp']:,}")
    with col3:
        st.metric("Con Matching ESCO", f"{matching_stats['total_matching']:,}")
    with col4:
        st.metric("Score Promedio", f"{matching_stats['avg_score']:.2%}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ofertas por Version NLP")
        if nlp_stats["por_version"]:
            df = pd.DataFrame(nlp_stats["por_version"], columns=["Version", "Cantidad"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos")

    with col2:
        st.subheader("Cobertura de Campos NLP")
        cov = nlp_stats["cobertura_campos"]
        if cov["total"] > 0:
            data = {
                "Campo": ["Experiencia", "Educacion", "Skills", "Salario"],
                "Extraidos": [cov["experiencia"], cov["educacion"], cov["skills"], cov["salario"]],
                "Cobertura %": [
                    f"{cov['experiencia']/cov['total']*100:.1f}%",
                    f"{cov['educacion']/cov['total']*100:.1f}%",
                    f"{cov['skills']/cov['total']*100:.1f}%",
                    f"{cov['salario']/cov['total']*100:.1f}%"
                ]
            }
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    st.divider()

    # Matching
    st.subheader("Matching ESCO por Version")
    if matching_stats["por_version"]:
        df = pd.DataFrame(matching_stats["por_version"], columns=["Version", "Cantidad"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Distribucion de Scores")
    col1, col2, col3 = st.columns(3)
    dist = matching_stats["score_distribution"]
    with col1:
        st.metric("Score >= 60%", f"{dist['alto']:,}", help="Alta confianza")
    with col2:
        st.metric("Score 50-60%", f"{dist['medio']:,}", help="Media confianza")
    with col3:
        st.metric("Score < 50%", f"{dist['bajo']:,}", help="Baja confianza")


# ============== TAB 3: TESTS ==============
with tab3:
    st.header("Gold Set y Precision")

    # Acciones
    st.subheader("Acciones")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🟢 Correr Test Gold Set",
                     disabled=st.session_state.process_running,
                     use_container_width=True,
                     help="Ejecuta test_gold_set_manual.py"):
            with st.spinner("Ejecutando tests..."):
                code, output = run_command_sync(
                    [sys.executable, str(TEST_SCRIPT)],
                    cwd=str(BASE_DIR / "database")
                )
            st.session_state.last_test_result = {
                "code": code,
                "output": output,
                "timestamp": datetime.now().isoformat()
            }
            st.cache_data.clear()
            if code == 0:
                st.success("Test completado")
            else:
                st.warning(f"Test finalizado con codigo {code}")

    with col2:
        st.write("")
    with col3:
        st.write("")

    # Resultado del test
    if st.session_state.last_test_result:
        result = st.session_state.last_test_result
        with st.expander("📄 Resultado del Test", expanded=True):
            st.caption(f"Ejecutado: {result['timestamp'][:19]}")
            st.code(result["output"], language="text")

    st.divider()

    # Metricas
    st.subheader("Metricas")
    gold_stats = get_gold_set_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Casos", gold_stats["total"])
    with col2:
        st.metric("Correctos", gold_stats["correctos"])
    with col3:
        st.metric("Incorrectos", gold_stats["total"] - gold_stats["correctos"])
    with col4:
        precision = gold_stats["precision"]
        delta_color = "normal" if precision >= 90 else "inverse"
        st.metric("Precision", f"{precision:.1f}%", delta=f"Obj: 95%", delta_color=delta_color)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Errores por Tipo")
        if gold_stats["errores_por_tipo"]:
            df = pd.DataFrame([
                {"Tipo Error": k, "Cantidad": v}
                for k, v in gold_stats["errores_por_tipo"].items()
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("Sin errores")

    with col2:
        st.subheader("Progreso hacia Objetivo")
        objetivo = 200
        actual = gold_stats["total"]
        progreso = min(actual / objetivo, 1.0)
        st.progress(progreso)
        st.caption(f"{actual} / {objetivo} casos ({progreso*100:.0f}%)")

    st.divider()

    st.subheader("Detalle del Gold Set")
    if gold_stats["detalle"]:
        df = pd.DataFrame(gold_stats["detalle"])
        df["resultado"] = df["esco_ok"].apply(lambda x: "✅" if x else "❌")
        cols_to_show = ["id_oferta", "resultado", "comentario"]
        if "tipo_error" in df.columns:
            cols_to_show.append("tipo_error")
        st.dataframe(
            df[cols_to_show].fillna(""),
            use_container_width=True,
            hide_index=True
        )


# ============== TAB 4: S3 SYNC ==============
with tab4:
    st.header("Estado de Exports a S3")

    exports_status = get_exports_status()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ultimo Snapshot")
        if exports_status["latest"]:
            st.json(exports_status["latest"])
        else:
            st.warning("Sin informacion")

    with col2:
        st.subheader("Total Snapshots Locales")
        st.metric("Snapshots", len(exports_status["snapshots"]))

    st.divider()

    st.subheader("Snapshots Disponibles")
    if exports_status["snapshots"]:
        df = pd.DataFrame(exports_status["snapshots"])
        df["tamano_mb"] = df["tamano_mb"].apply(lambda x: f"{x:.2f} MB")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Sin snapshots")

    st.divider()

    st.subheader("Configuracion S3")
    s3_config_path = BASE_DIR / "config" / "aws_credentials.example.json"
    if s3_config_path.exists():
        st.success("Config S3 encontrada")
    else:
        st.warning("Falta config/aws_credentials.json")


# ============== TAB 5: LOGS ==============
with tab5:
    st.header("Logs y Experimentos")

    experiments = get_experiments()
    timing_logs = get_timing_logs(200)

    st.subheader("Experimentos Registrados")
    if experiments:
        for name, exp in experiments.items():
            with st.expander(f"📊 {name} - {exp.get('timestamp', 'N/A')[:10]}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Metricas:**")
                    st.json(exp.get("metrics", {}))
                with col2:
                    st.write("**Config:**")
                    st.json(exp.get("config", {}))
                st.write(f"**Tags:** {', '.join(exp.get('tags', []))}")
                st.write(f"**Descripcion:** {exp.get('description', 'N/A')}")
    else:
        st.info("Sin experimentos")

    st.divider()

    st.subheader("Timing Logs")
    if timing_logs:
        by_component = {}
        for log in timing_logs:
            comp = log.get("component", "unknown")
            if comp not in by_component:
                by_component[comp] = []
            by_component[comp].append(log.get("duration_ms", 0))

        stats_data = []
        for comp, durations in by_component.items():
            stats_data.append({
                "Componente": comp,
                "Llamadas": len(durations),
                "Avg (ms)": f"{sum(durations)/len(durations):.2f}",
                "Min (ms)": f"{min(durations):.2f}",
                "Max (ms)": f"{max(durations):.2f}"
            })

        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

        st.subheader("Ultimos 20 Logs")
        recent = timing_logs[-20:]
        df = pd.DataFrame(recent)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            df["duration_ms"] = df["duration_ms"].apply(lambda x: f"{x:.2f}")
            st.dataframe(df[["timestamp", "component", "duration_ms"]], use_container_width=True, hide_index=True)
    else:
        st.info("Sin timing logs")


# ============== TAB 6: KEYWORDS ==============
with tab6:
    st.header("Optimizacion de Keywords")

    # Inicializar optimizer
    try:
        optimizer = KeywordOptimizer()
        analysis = optimizer.analyze()

        # Metricas principales
        st.subheader("Resumen")
        s = analysis["summary"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Keywords", f"{s['total_keywords']:,}")
        with col2:
            delta_color = "inverse" if s['sin_resultados_pct'] > 30 else "normal"
            st.metric("Sin Resultados", f"{s['sin_resultados']:,}", delta=f"{s['sin_resultados_pct']}%", delta_color=delta_color)
        with col3:
            st.metric("Muy Genericos", s['muy_genericos'])
        with col4:
            st.metric("Tasa Novedad", f"{s['tasa_novedad_global']}%")

        st.divider()

        # Distribucion
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribucion de Keywords")
            if analysis.get("distribution"):
                dist_data = [
                    {"Categoria": k.replace("_", " ").title(), "Cantidad": v}
                    for k, v in analysis["distribution"].items()
                ]
                st.dataframe(pd.DataFrame(dist_data), use_container_width=True, hide_index=True)

        with col2:
            st.subheader("Keywords Muy Genericos")
            if analysis["problematic"]["muy_genericos"]:
                gen_data = [
                    {"Keyword": g["keyword"] if g["keyword"] else "(vacio)", "Ofertas": f"{g['ofertas']:,}"}
                    for g in analysis["problematic"]["muy_genericos"]
                ]
                st.dataframe(pd.DataFrame(gen_data), use_container_width=True, hide_index=True)
            else:
                st.success("Sin keywords muy genericos")

        st.divider()

        # Recomendaciones
        st.subheader("Recomendaciones")
        if analysis["recommendations"]:
            for r in analysis["recommendations"]:
                if r["tipo"] == "critico":
                    st.error(f"**CRITICO:** {r['mensaje']}")
                elif r["tipo"] == "alerta":
                    st.warning(f"**ALERTA:** {r['mensaje']}")
                else:
                    st.info(r['mensaje'])
        else:
            st.success("Sin recomendaciones pendientes")

        st.divider()

        # Acciones
        st.subheader("Acciones")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Generar Propuesta v3.3",
                         disabled=st.session_state.process_running,
                         use_container_width=True):
                with st.spinner("Generando propuesta..."):
                    proposal = optimizer.propose_changes(analysis, "3.3")
                st.session_state.keyword_proposal = proposal
                st.success(f"Propuesta v{proposal['version']} generada")

        with col2:
            st.write("")

        with col3:
            st.write("")

        # Mostrar propuesta si existe
        if hasattr(st.session_state, 'keyword_proposal') and st.session_state.keyword_proposal:
            prop = st.session_state.keyword_proposal
            with st.expander(f"Propuesta v{prop['version']}", expanded=True):
                st.write(f"**Base:** v{prop['base_version']}")
                st.write(f"**Keywords a eliminar:** {len(prop['changes']['remove'])}")

                impact = prop["expected_impact"]
                st.write(f"**Impacto:** -{impact['keywords_eliminados']} keywords ({impact['reduccion_pct']}%)")
                st.write(f"**Ahorro estimado:** {impact['tiempo_estimado_ahorro_min']} minutos por scraping")

                st.write("**Justificacion:**")
                for j in prop["justification"]:
                    st.write(f"- {j}")

        st.divider()

        # Historial de versiones
        st.subheader("Historial de Versiones")
        history = optimizer.get_version_history()
        if history:
            hist_data = [
                {
                    "Version": f"v{v['version']}",
                    "Fecha": v.get("date", "N/A"),
                    "Autor": v.get("author", "N/A"),
                    "Cambios": f"+{v['changes']['added']} -{v['changes']['removed']}"
                }
                for v in reversed(history)
            ]
            st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)
        else:
            st.info("Sin historial de versiones")

    except Exception as e:
        st.error(f"Error al cargar KeywordOptimizer: {e}")
        st.info("Verifica que exista master_keywords.json y keywords_performance en la BD")


# Footer
st.divider()
st.caption(f"MOL Admin Dashboard v1.2 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
