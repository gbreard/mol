"""
Tests de integración para el pipeline completo
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Agregar project root al path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


class TestPipelineIntegration:
    """Tests de integración del pipeline"""

    @pytest.fixture
    def project_paths(self):
        """Paths del proyecto"""
        return {
            'root': project_root,
            'sources': project_root / "01_sources",
            'consolidation': project_root / "02_consolidation",
            'esco': project_root / "03_esco_matching",
            'analysis': project_root / "04_analysis",
            'products': project_root / "05_products"
        }

    def test_01_estructura_directorios(self, project_paths):
        """Verifica que la estructura de directorios existe"""
        assert project_paths['sources'].exists(), "Directorio 01_sources no existe"
        assert project_paths['consolidation'].exists(), "Directorio 02_consolidation no existe"
        assert project_paths['esco'].exists(), "Directorio 03_esco_matching no existe"
        assert project_paths['analysis'].exists(), "Directorio 04_analysis no existe"
        assert project_paths['products'].exists(), "Directorio 05_products no existe"

    def test_02_schema_unificado_existe(self, project_paths):
        """Verifica que el schema unificado existe"""
        schema_path = project_paths['root'] / "shared" / "schemas" / "schema_unificado.json"
        assert schema_path.exists(), "Schema unificado no existe"

        # Verificar que es JSON válido
        import json
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            assert 'title' in schema
            assert 'properties' in schema

    def test_03_normalizadores_disponibles(self, project_paths):
        """Verifica que los normalizadores están disponibles"""
        normalizers_path = project_paths['consolidation'] / "scripts" / "normalizar_campos.py"
        assert normalizers_path.exists(), "normalizar_campos.py no existe"

        # Importar y verificar
        from sys import path
        path.append(str(project_paths['consolidation'] / "scripts"))

        from normalizar_campos import get_normalizer, ZonaJobsNormalizer

        # Verificar que ZonaJobs está disponible
        normalizer = get_normalizer('zonajobs')
        assert isinstance(normalizer, ZonaJobsNormalizer)

    def test_04_consolidacion_procesa_zonajobs(self, project_paths):
        """Test de consolidación con datos de ZonaJobs (si existen)"""
        zonajobs_raw = project_paths['sources'] / "zonajobs" / "data" / "raw"

        if not zonajobs_raw.exists():
            pytest.skip("No hay datos de ZonaJobs para testear")

        csv_files = list(zonajobs_raw.glob("*.csv"))
        if not csv_files:
            pytest.skip("No hay archivos CSV de ZonaJobs")

        # Cargar datos
        latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)

        assert len(df) > 0, "Archivo CSV está vacío"
        assert 'id_oferta' in df.columns, "Falta columna id_oferta"
        assert 'titulo' in df.columns, "Falta columna titulo"

    def test_05_validador_schema(self, project_paths):
        """Verifica que el validador funciona"""
        from sys import path
        path.append(str(project_paths['consolidation'] / "scripts"))

        from validacion import ValidadorSchema

        validador = ValidadorSchema()
        assert validador.schema is not None

    def test_06_pipeline_script_existe(self, project_paths):
        """Verifica que el script del pipeline existe"""
        pipeline_script = project_paths['root'] / "pipeline_completo.py"
        assert pipeline_script.exists(), "pipeline_completo.py no existe"

    def test_07_readme_principal_existe(self, project_paths):
        """Verifica que existe documentación principal"""
        readme = project_paths['root'] / "README_NUEVO.md"
        assert readme.exists(), "README_NUEVO.md no existe"

    def test_08_docs_arquitectura_existe(self, project_paths):
        """Verifica que existe documentación de arquitectura"""
        arch = project_paths['root'] / "docs" / "arquitectura.md"
        assert arch.exists(), "docs/arquitectura.md no existe"


class TestNormalizacionZonaJobs:
    """Tests específicos de normalización de ZonaJobs"""

    @pytest.fixture
    def sample_zonajobs_data(self):
        """Datos de ejemplo de ZonaJobs"""
        return pd.DataFrame({
            'id_oferta': ['12345', '67890'],
            'titulo': ['Desarrollador Python', 'Analista de Datos'],
            'empresa': ['Tech Corp', 'Data Inc'],
            'id_empresa': ['111', '222'],
            'descripcion': ['<p>Buscamos dev</p>', '<p>Analista</p>'],
            'localizacion': ['Capital Federal, Buenos Aires', 'Córdoba, Córdoba'],
            'modalidad_trabajo': ['Remoto', 'Presencial'],
            'tipo_trabajo': ['Tiempo completo', 'Part-time'],
            'fecha_publicacion': ['2025-10-20', '2025-10-19'],
            'cantidad_vacantes': [1, 2],
            'apto_discapacitado': [True, False],
            'url_oferta': ['https://zonajobs.com/1', 'https://zonajobs.com/2'],
            'scrapeado_en': ['2025-10-21T10:00:00', '2025-10-21T10:00:00']
        })

    def test_normalizacion_basica(self, sample_zonajobs_data):
        """Test de normalización básica"""
        from sys import path
        consolidation_path = project_root / "02_consolidation" / "scripts"
        path.append(str(consolidation_path))

        from normalizar_campos import ZonaJobsNormalizer

        normalizer = ZonaJobsNormalizer()
        df_normalized = normalizer.normalize(sample_zonajobs_data)

        # Verificar que tiene las columnas esperadas
        assert '_metadata.source' in df_normalized.columns
        assert '_metadata.source_id' in df_normalized.columns
        assert 'informacion_basica.titulo' in df_normalized.columns
        assert 'informacion_basica.empresa' in df_normalized.columns

        # Verificar valores
        assert all(df_normalized['_metadata.source'] == 'zonajobs')
        assert len(df_normalized) == 2

    def test_normalizacion_modalidad(self, sample_zonajobs_data):
        """Test de normalización de modalidades"""
        from sys import path
        consolidation_path = project_root / "02_consolidation" / "scripts"
        path.append(str(consolidation_path))

        from normalizar_campos import ZonaJobsNormalizer

        normalizer = ZonaJobsNormalizer()
        df_normalized = normalizer.normalize(sample_zonajobs_data)

        # Modalidades normalizadas
        assert df_normalized.loc[0, 'modalidad.modalidad_trabajo'] == 'remoto'
        assert df_normalized.loc[1, 'modalidad.modalidad_trabajo'] == 'presencial'

        # Tipo de trabajo normalizado
        assert df_normalized.loc[0, 'modalidad.tipo_trabajo'] == 'full_time'
        assert df_normalized.loc[1, 'modalidad.tipo_trabajo'] == 'part_time'


class TestDeduplicacion:
    """Tests de deduplicación"""

    @pytest.fixture
    def sample_duplicates(self):
        """Datos con duplicados"""
        return pd.DataFrame({
            '_metadata.unified_id': ['zj_1', 'zj_2', 'zj_1', 'bm_3'],
            'informacion_basica.titulo': ['Dev Python', 'Analista', 'Dev Python', 'Designer'],
            'informacion_basica.titulo_normalizado': ['dev python', 'analista', 'dev python', 'designer'],
            'informacion_basica.empresa': ['Tech', 'Data', 'Tech', 'Design Co']
        })

    def test_deduplicacion_por_id(self, sample_duplicates):
        """Test deduplicación por ID exacto"""
        from sys import path
        consolidation_path = project_root / "02_consolidation" / "scripts"
        path.append(str(consolidation_path))

        from deduplicacion import DeduplicadorOfertas

        dedup = DeduplicadorOfertas()
        df_unique = dedup.deduplicar(sample_duplicates)

        # Debe haber removido 1 duplicado (zj_1)
        assert len(df_unique) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
