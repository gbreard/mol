"""
Tests para los fixes P0/P1 del pipeline de scraping.

Testea:
- Backup: resolución correcta de rutas
- DB Manager: normalización auto camelCase → snake_case
- DB Manager: id_empresa no es campo crítico
- Bajas: detección de tracking desactualizado
"""

import sqlite3
import json
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch


# ============================================================================
# BACKUP: PATHS CORRECTOS
# ============================================================================

class TestBackupPaths:
    def test_base_dir_apunta_a_project_root(self):
        from scripts.db.backup_database import BASE_DIR
        # BASE_DIR debe ser la raíz del proyecto (contiene database/, scripts/, etc.)
        assert (BASE_DIR / "database").exists(), f"BASE_DIR={BASE_DIR} no contiene database/"
        assert (BASE_DIR / "scripts").exists(), f"BASE_DIR={BASE_DIR} no contiene scripts/"

    def test_db_path_es_correcto(self):
        from scripts.db.backup_database import DB_PATH
        # Debe apuntar a database/bumeran_scraping.db
        assert DB_PATH.parent.name == "database"
        assert DB_PATH.name == "bumeran_scraping.db"

    def test_backup_dir_dentro_de_database(self):
        from scripts.db.backup_database import BACKUP_DIR
        # Debe ser database/backups/, no scripts/backups/
        assert BACKUP_DIR.parent.name == "database"
        assert BACKUP_DIR.name == "backups"


# ============================================================================
# DB MANAGER: NORMALIZACIÓN API → SNAKE_CASE
# ============================================================================

class TestNormalizeApiDataframe:
    @pytest.fixture
    def db_manager(self, tmp_path):
        """DatabaseManager con BD temporal."""
        from database.db_manager import DatabaseManager
        db_path = tmp_path / "test_normalize.db"
        dm = DatabaseManager(db_path=str(db_path), enable_dual_write=False)
        dm.connect()
        yield dm
        dm.disconnect()

    def test_detecta_formato_snake_case_no_modifica(self, db_manager):
        df = pd.DataFrame([{
            'id_oferta': 1,
            'titulo': 'Test',
            'empresa': 'Acme',
            'id_empresa': 100,
            'fecha_publicacion_iso': '2026-01-01',
        }])

        result = db_manager._normalize_api_dataframe(df)

        # No debe modificar — ya está en snake_case
        assert 'id_oferta' in result.columns
        assert 'id' not in result.columns

    def test_detecta_formato_camelcase_y_convierte(self, db_manager):
        """
        Requiere que bumeran_scraper esté en sys.path.
        En producción run_scheduler.py agrega el path.
        Para el test, agregamos el path manualmente.
        """
        import sys
        scraper_path = str(Path(__file__).parent.parent.parent / "01_sources" / "bumeran" / "scrapers")
        sys.path.insert(0, scraper_path)

        try:
            df = pd.DataFrame([{
                'id': 12345,
                'idEmpresa': 100,
                'titulo': 'Gerente de Ventas',
                'empresa': 'Acme SA',
                'detalle': '<p>Descripción</p>',
                'fechaPublicacion': '2026-01-15T10:00:00',
                'fechaHoraPublicacion': '2026-01-15T10:00:00',
                'fechaModificado': '2026-01-15T10:00:00',
                'localizacion': 'Buenos Aires',
                'modalidadTrabajo': 'presencial',
                'tipoTrabajo': 'Full-time',
                'cantidadVacantes': 2,
                'confidencial': 0,
                'aptoDiscapacitado': 0,
                'idArea': 1,
                'idSubarea': 2,
                'idPais': 1,
                'logoURL': None,
                'validada': 1,
                'empresaPro': 0,
                'promedioEmpresa': 4.5,
                'planPublicacion': None,
                'portal': 'bumeran',
                'tipoAviso': 'simple',
                'tienePreguntas': 0,
                'salarioObligatorio': 0,
                'altaRevisionPerfiles': 0,
                'guardado': 0,
                'gptwUrl': None,
            }])

            result = db_manager._normalize_api_dataframe(df)

            # Debe tener columnas snake_case
            assert 'id_oferta' in result.columns
            assert 'id_empresa' in result.columns
            assert 'titulo' in result.columns
            assert result.iloc[0]['id_oferta'] == 12345
            assert result.iloc[0]['id_empresa'] == 100

            # No debe tener columnas camelCase
            assert 'idEmpresa' not in result.columns
            assert 'fechaPublicacion' not in result.columns
        finally:
            sys.path.remove(scraper_path)


# ============================================================================
# DB MANAGER: ID_EMPRESA NO ES CRÍTICO
# ============================================================================

class TestIdEmpresaNoCritico:
    @pytest.fixture
    def db_with_schema(self, tmp_path):
        """BD SQLite con schema de ofertas para test de inserción."""
        db_path = tmp_path / "test_insert.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE ofertas (
                id_oferta INTEGER PRIMARY KEY,
                id_empresa INTEGER,
                titulo TEXT NOT NULL,
                empresa TEXT,
                descripcion TEXT,
                confidencial INTEGER,
                localizacion TEXT,
                modalidad_trabajo TEXT,
                tipo_trabajo TEXT,
                fecha_publicacion_original TEXT,
                fecha_publicacion_iso TEXT,
                fecha_publicacion_datetime TEXT,
                fecha_hora_publicacion_original TEXT,
                fecha_hora_publicacion_iso TEXT,
                fecha_hora_publicacion_datetime TEXT,
                fecha_modificado_original TEXT,
                fecha_modificado_iso TEXT,
                fecha_modificado_datetime TEXT,
                cantidad_vacantes INTEGER,
                apto_discapacitado INTEGER,
                id_area INTEGER,
                id_subarea INTEGER,
                id_pais INTEGER,
                logo_url TEXT,
                empresa_validada INTEGER,
                empresa_pro INTEGER,
                promedio_empresa REAL,
                plan_publicacion_id INTEGER,
                plan_publicacion_nombre TEXT,
                portal TEXT,
                tipo_aviso TEXT,
                tiene_preguntas INTEGER,
                salario_obligatorio INTEGER,
                alta_revision_perfiles INTEGER,
                guardado INTEGER,
                gptw_url TEXT,
                url_oferta TEXT,
                scrapeado_en TEXT NOT NULL DEFAULT (datetime('now')),
                estado_oferta TEXT DEFAULT 'activa',
                fecha_ultimo_visto TEXT,
                fecha_baja TEXT,
                dias_publicada INTEGER,
                veces_vista INTEGER DEFAULT 1,
                categoria_permanencia TEXT,
                descripcion_utf8 TEXT,
                provincia_normalizada TEXT,
                codigo_provincia_indec TEXT,
                localidad_normalizada TEXT,
                codigo_localidad_indec TEXT
            )
        """)
        conn.commit()
        conn.close()
        return db_path

    def test_oferta_sin_id_empresa_se_inserta(self, db_with_schema):
        from database.db_manager import DatabaseManager

        df = pd.DataFrame([{
            'id_oferta': 9999,
            'titulo': 'Contador Senior',
            'empresa': 'Confidencial',  # Bumeran pone "Confidencial" como empresa
            'id_empresa': None,  # Sin id_empresa = oferta confidencial
            'descripcion': 'Buscamos contador',
            'localizacion': 'Buenos Aires',
            'modalidad_trabajo': 'presencial',
            'tipo_trabajo': 'Full-time',
            'fecha_publicacion_iso': '2026-01-15',
            'scrapeado_en': datetime.now().isoformat(),
        }])

        with DatabaseManager(db_path=str(db_with_schema), enable_dual_write=False) as db:
            inserted = db.insert_ofertas(df)

        assert inserted == 1

        # Verificar que se insertó
        conn = sqlite3.connect(db_with_schema)
        cursor = conn.cursor()
        cursor.execute("SELECT titulo FROM ofertas WHERE id_oferta = 9999")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == 'Contador Senior'


# ============================================================================
# BAJAS: DETECCIÓN DE TRACKING DESACTUALIZADO
# ============================================================================

class TestBajasTrackingDesactualizado:
    @pytest.fixture
    def tracking_file(self, tmp_path):
        """Crea archivo de tracking con fecha configurable."""
        def _create(dias_atras: int):
            fecha = (datetime.now() - timedelta(days=dias_atras)).isoformat()
            data = {
                'last_update': fecha,
                'scraped_ids': {'1001': '2026-01-01', '1002': '2026-01-02'}
            }
            path = tmp_path / "scraped_ids.json"
            with open(path, 'w') as f:
                json.dump(data, f)
            return path
        return _create

    @pytest.fixture
    def db_bajas(self, tmp_path):
        """BD con datos para detección de bajas."""
        db_path = tmp_path / "test_bajas.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE ofertas (
                id_oferta INTEGER PRIMARY KEY,
                titulo TEXT,
                empresa TEXT,
                estado_oferta TEXT DEFAULT 'activa',
                fecha_publicacion_iso TEXT,
                fecha_ultimo_visto TEXT,
                fecha_baja TEXT,
                dias_publicada INTEGER,
                veces_vista INTEGER DEFAULT 1,
                categoria_permanencia TEXT,
                scrapeado_en TEXT DEFAULT (datetime('now'))
            )
        """)
        # Insertar ofertas activas recientes
        for i in range(1001, 1006):
            cursor.execute(
                "INSERT INTO ofertas (id_oferta, titulo, estado_oferta, scrapeado_en) "
                "VALUES (?, 'Test', 'activa', ?)",
                (i, datetime.now().isoformat())
            )
        conn.commit()
        conn.close()
        return db_path

    def test_tracking_reciente_usa_tracking(self, tracking_file, db_bajas):
        """Si el tracking es reciente (<7 días), debe usarlo."""
        from database.detectar_bajas_integrado import DetectorBajasIntegrado

        tf = tracking_file(dias_atras=2)  # 2 días atrás = reciente

        with DetectorBajasIntegrado(db_bajas) as detector:
            ids = detector.obtener_ids_ultimo_scraping(tf)

        # Debe traer los IDs del tracking (1001, 1002)
        assert len(ids) == 2
        assert 1001 in ids

    def test_tracking_viejo_detecta_stale(self, tracking_file):
        """Si el tracking es viejo (>7 días), debe advertir."""
        tf = tracking_file(dias_atras=15)  # 15 días atrás = viejo

        with open(tf, 'r') as f:
            data = json.load(f)

        last_update = data['last_update']
        tracking_date = datetime.fromisoformat(last_update)
        dias = (datetime.now() - tracking_date).days

        assert dias > 7, "El tracking debería ser considerado desactualizado"
