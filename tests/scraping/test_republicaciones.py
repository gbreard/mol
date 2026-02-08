"""
Tests para detección de republicaciones.

Testea:
- Normalización de títulos
- Generación de hash de grupo
- Detección de grupos republicados
- Marcado en BD (con SQLite in-memory)
- Estadísticas
"""

import sqlite3
import pytest
from pathlib import Path

from database.detectar_republicaciones import (
    normalizar_titulo,
    generar_grupo_hash,
    DetectorRepublicaciones,
)


# ============================================================================
# NORMALIZACIÓN DE TÍTULOS
# ============================================================================

class TestNormalizarTitulo:
    @pytest.mark.parametrize("titulo,expected", [
        ("Gerente de Ventas", "gerente de ventas"),
        ("  Gerente de Ventas  ", "gerente de ventas"),
        ("Gerente de Ventas.", "gerente de ventas"),
        ("Gerente de Ventas...", "gerente de ventas"),
        ("Gerente de Ventas-", "gerente de ventas"),
        ("Gerente de Ventas!", "gerente de ventas"),
        ("GERENTE DE VENTAS", "gerente de ventas"),
        ("Gerente   de   Ventas", "gerente de ventas"),
        ("", ""),
        (None, ""),
    ])
    def test_normaliza_correctamente(self, titulo, expected):
        assert normalizar_titulo(titulo) == expected

    def test_titulos_equivalentes_producen_mismo_resultado(self):
        variantes = [
            "Analista Comercial (San Martín)",
            "analista comercial (san martín)",
            "  Analista Comercial (San Martín)  ",
            "Analista Comercial (San Martín).",
        ]
        resultados = {normalizar_titulo(t) for t in variantes}
        assert len(resultados) == 1


# ============================================================================
# HASH DE GRUPO
# ============================================================================

class TestGenerarGrupoHash:
    def test_mismo_input_mismo_hash(self):
        h1 = generar_grupo_hash("gerente de ventas", 12345)
        h2 = generar_grupo_hash("gerente de ventas", 12345)
        assert h1 == h2

    def test_distinto_titulo_distinto_hash(self):
        h1 = generar_grupo_hash("gerente de ventas", 12345)
        h2 = generar_grupo_hash("analista contable", 12345)
        assert h1 != h2

    def test_distinta_empresa_distinto_hash(self):
        h1 = generar_grupo_hash("gerente de ventas", 12345)
        h2 = generar_grupo_hash("gerente de ventas", 99999)
        assert h1 != h2

    def test_hash_tiene_12_caracteres(self):
        h = generar_grupo_hash("test", 1)
        assert len(h) == 12


# ============================================================================
# DETECCIÓN CON BD IN-MEMORY
# ============================================================================

@pytest.fixture
def db_memory(tmp_path):
    """Crea BD SQLite in-memory con schema de ofertas y datos de prueba."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear tabla ofertas (schema mínimo necesario)
    cursor.execute("""
        CREATE TABLE ofertas (
            id_oferta INTEGER PRIMARY KEY,
            titulo TEXT,
            empresa TEXT,
            id_empresa INTEGER,
            fecha_publicacion_iso TEXT,
            estado_oferta TEXT DEFAULT 'activa',
            cantidad_vacantes INTEGER DEFAULT 1,
            scrapeado_en TEXT DEFAULT (datetime('now'))
        )
    """)

    # Crear tabla ofertas_nlp (schema mínimo)
    cursor.execute("""
        CREATE TABLE ofertas_nlp (
            id_oferta TEXT PRIMARY KEY,
            es_republica INTEGER
        )
    """)

    # Insertar datos de prueba
    ofertas = [
        # Grupo 1: "Gerente de Ventas" en empresa 100 - publicado 3 veces
        (1001, "Gerente de Ventas", "Acme SA", 100, "2026-01-01", "baja"),
        (1002, "Gerente de Ventas", "Acme SA", 100, "2026-01-15", "baja"),
        (1003, "Gerente de Ventas", "Acme SA", 100, "2026-02-01", "activa"),

        # Grupo 2: "Analista Contable" en empresa 200 - publicado 2 veces
        (2001, "Analista Contable", "Beta SRL", 200, "2026-01-10", "baja"),
        (2002, "Analista Contable", "Beta SRL", 200, "2026-02-05", "activa"),

        # NO republicación: mismo título DISTINTA empresa
        (3001, "Desarrollador Python", "Gamma SA", 300, "2026-01-20", "activa"),
        (3002, "Desarrollador Python", "Delta SA", 400, "2026-01-25", "activa"),

        # NO republicación: oferta única
        (4001, "Director Financiero", "Omega SA", 500, "2026-02-01", "activa"),

        # Oferta confidencial (sin id_empresa) - debe ignorarse
        (5001, "Contador Senior", None, None, "2026-01-15", "activa"),
        (5002, "Contador Senior", None, None, "2026-02-01", "activa"),
    ]

    for o in ofertas:
        cursor.execute(
            "INSERT INTO ofertas (id_oferta, titulo, empresa, id_empresa, "
            "fecha_publicacion_iso, estado_oferta) VALUES (?, ?, ?, ?, ?, ?)",
            o
        )

    # Insertar en ofertas_nlp para los que tienen NLP
    for o in ofertas:
        cursor.execute(
            "INSERT INTO ofertas_nlp (id_oferta, es_republica) VALUES (?, NULL)",
            (str(o[0]),)
        )

    conn.commit()
    conn.close()

    return db_path


class TestDetectorRepublicaciones:
    def test_detecta_grupos_correctamente(self, db_memory):
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            grupos = detector.detectar_grupos()

        # Debe detectar 2 grupos (Gerente Ventas x3 + Analista Contable x2)
        assert len(grupos) == 2

        # Verificar que "Desarrollador Python" NO es grupo (distinta empresa)
        titulos = {g['titulo_norm'] for g in grupos}
        assert "desarrollador python" not in titulos

    def test_no_incluye_confidenciales(self, db_memory):
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            grupos = detector.detectar_grupos()

        # "Contador Senior" sin empresa NO debe aparecer
        titulos = {g['titulo_norm'] for g in grupos}
        assert "contador senior" not in titulos

    def test_marca_republicaciones_en_bd(self, db_memory):
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            stats = detector.ejecutar()

        assert stats['grupos_detectados'] == 2
        assert stats['ofertas_republicadas'] == 3  # 2 de grupo1 + 1 de grupo2
        assert stats['ofertas_originales'] == 2

        # Verificar en BD
        conn = sqlite3.connect(db_memory)
        cursor = conn.cursor()

        # Oferta 1001 debe ser original (numero_republicacion=1)
        cursor.execute(
            "SELECT es_republicacion, numero_republicacion FROM ofertas WHERE id_oferta = 1001"
        )
        row = cursor.fetchone()
        assert row[0] == 0  # es original
        assert row[1] == 1  # primera publicación

        # Oferta 1003 debe ser republicación (numero_republicacion=3)
        cursor.execute(
            "SELECT es_republicacion, numero_republicacion, id_oferta_original "
            "FROM ofertas WHERE id_oferta = 1003"
        )
        row = cursor.fetchone()
        assert row[0] == 1  # es republicación
        assert row[1] == 3  # tercera publicación
        assert row[2] == 1001  # original es 1001

        # Oferta 4001 (única) NO debe tener grupo
        cursor.execute(
            "SELECT grupo_republicacion FROM ofertas WHERE id_oferta = 4001"
        )
        row = cursor.fetchone()
        assert row[0] is None

        conn.close()

    def test_actualiza_ofertas_nlp_es_republica(self, db_memory):
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            detector.ejecutar()

        conn = sqlite3.connect(db_memory)
        cursor = conn.cursor()

        # Ofertas republicadas deben tener es_republica=1 en ofertas_nlp
        cursor.execute(
            "SELECT es_republica FROM ofertas_nlp WHERE id_oferta = '1002'"
        )
        row = cursor.fetchone()
        assert row[0] == 1

        # Oferta original no debería tener es_republica=1
        # (solo las republicaciones se marcan, no las originales)
        cursor.execute(
            "SELECT es_republica FROM ofertas_nlp WHERE id_oferta = '4001'"
        )
        row = cursor.fetchone()
        assert row[0] is None  # no tocada

        conn.close()

    def test_estadisticas_correctas(self, db_memory):
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            detector.ejecutar()
            stats = detector.obtener_estadisticas()

        assert stats['total_republicaciones'] == 3
        assert stats['total_grupos'] == 2
        # Distribución: 1 grupo de 3 ofertas, 1 grupo de 2 ofertas
        assert stats['distribucion'] == {2: 1, 3: 1}

    def test_dry_run_no_modifica_bd(self, db_memory):
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            stats = detector.ejecutar(dry_run=True)

        assert stats['dry_run'] is True

        # Verificar que la BD NO fue modificada
        conn = sqlite3.connect(db_memory)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ofertas WHERE grupo_republicacion IS NOT NULL"
        )
        assert cursor.fetchone()[0] == 0
        conn.close()

    def test_idempotente(self, db_memory):
        """Ejecutar dos veces produce el mismo resultado."""
        with DetectorRepublicaciones(db_memory) as detector:
            detector.aplicar_migracion()
            stats1 = detector.ejecutar()

        with DetectorRepublicaciones(db_memory) as detector:
            stats2 = detector.ejecutar()

        assert stats1['grupos_detectados'] == stats2['grupos_detectados']
        assert stats1['ofertas_republicadas'] == stats2['ofertas_republicadas']


# ============================================================================
# TESTS CON BD REAL (solo si existe)
# ============================================================================

class TestRepublicacionesBDReal:
    """Tests contra la BD real de producción (solo lectura)."""

    @pytest.fixture
    def real_db(self):
        db_path = Path(__file__).parent.parent.parent / "database" / "bumeran_scraping.db"
        if not db_path.exists():
            pytest.skip("BD de producción no disponible")
        return db_path

    def test_migracion_aplicada(self, real_db):
        conn = sqlite3.connect(real_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ofertas)")
        columnas = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'grupo_republicacion' in columnas
        assert 'es_republicacion' in columnas
        assert 'numero_republicacion' in columnas

    def test_hay_republicaciones_detectadas(self, real_db):
        conn = sqlite3.connect(real_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas WHERE es_republicacion = 1")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0, "Debería haber republicaciones detectadas en la BD"

    def test_vista_republicaciones_resumen_funciona(self, real_db):
        conn = sqlite3.connect(real_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM v_republicaciones_resumen")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0

    def test_vista_puestos_dificiles_funciona(self, real_db):
        conn = sqlite3.connect(real_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM v_puestos_dificiles_cubrir LIMIT 5")
        rows = cursor.fetchall()
        conn.close()

        # Puede haber 0 o más, pero la vista no debe fallar
        assert isinstance(rows, list)
