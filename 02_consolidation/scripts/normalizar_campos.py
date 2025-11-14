"""
Normalizadores de campos para cada fuente de datos.
Convierte datos crudos al schema unificado.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Agregar path del proyecto
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


class BaseNormalizer:
    """Clase base para normalizadores"""

    def __init__(self, source_name: str):
        self.source_name = source_name

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza un DataFrame al schema unificado"""
        raise NotImplementedError

    def _create_unified_id(self, source_id: str) -> str:
        """Crea ID unificado: source_sourceId"""
        return f"{self.source_name}_{source_id}"

    def _normalizar_modalidad(self, modalidad_raw: str) -> Optional[str]:
        """Normaliza modalidad de trabajo"""
        if pd.isna(modalidad_raw):
            return None

        modalidad_lower = str(modalidad_raw).lower()

        if any(word in modalidad_lower for word in ['remoto', 'remote', 'home office', 'teletrabajo']):
            return 'remoto'
        elif any(word in modalidad_lower for word in ['presencial', 'on-site', 'oficina']):
            return 'presencial'
        elif any(word in modalidad_lower for word in ['híbrido', 'hibrido', 'hybrid', 'mixto']):
            return 'hibrido'

        return None

    def _normalizar_tipo_trabajo(self, tipo_raw: str) -> Optional[str]:
        """Normaliza tipo de trabajo"""
        if pd.isna(tipo_raw):
            return None

        tipo_lower = str(tipo_raw).lower()

        if any(word in tipo_lower for word in ['full', 'tiempo completo', 'jornada completa']):
            return 'full_time'
        elif any(word in tipo_lower for word in ['part', 'medio tiempo', 'media jornada']):
            return 'part_time'
        elif any(word in tipo_lower for word in ['freelance', 'independiente', 'contractor']):
            return 'freelance'
        elif any(word in tipo_lower for word in ['temporar', 'temporal']):
            return 'temporario'
        elif any(word in tipo_lower for word in ['pasant', 'internship', 'práctica']):
            return 'pasantia'

        return 'otro'

    def _convertir_fecha_iso(self, fecha: Any) -> Optional[str]:
        """Convierte fecha a formato ISO 8601"""
        if pd.isna(fecha):
            return None

        try:
            if isinstance(fecha, str):
                # Intentar parsear string de fecha
                dt = pd.to_datetime(fecha)
            else:
                dt = pd.to_datetime(fecha)

            return dt.isoformat()
        except:
            return None

    def _limpiar_html(self, text: str) -> str:
        """Limpia tags HTML del texto"""
        if pd.isna(text):
            return ""

        # Remover tags HTML
        clean = re.sub(r'<[^>]+>', '', str(text))
        # Remover espacios múltiples
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def _normalizar_texto(self, text: str) -> str:
        """Normaliza texto para matching"""
        if pd.isna(text):
            return ""

        # Lowercase
        normalized = str(text).lower()
        # Remover caracteres especiales
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        # Remover espacios múltiples
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()


class ZonaJobsNormalizer(BaseNormalizer):
    """Normalizador para datos de ZonaJobs"""

    def __init__(self):
        super().__init__('zonajobs')

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de ZonaJobs al schema unificado"""

        # Crear DataFrame normalizado con el índice correcto
        normalized = pd.DataFrame(index=df.index)

        # === METADATA ===
        normalized['_metadata.source'] = 'zonajobs'
        normalized['_metadata.source_id'] = df['id_oferta'].astype(str)
        normalized['_metadata.unified_id'] = normalized['_metadata.source_id'].apply(
            lambda x: self._create_unified_id(x)
        )
        normalized['_metadata.url_oferta'] = df['url_oferta']
        normalized['_metadata.fecha_extraccion'] = df['scrapeado_en'].apply(
            self._convertir_fecha_iso
        )
        normalized['_metadata.version_scraper'] = '3.0'

        # === INFORMACION BASICA ===
        normalized['informacion_basica.titulo'] = df['titulo']
        normalized['informacion_basica.titulo_normalizado'] = df['titulo'].apply(
            self._normalizar_texto
        )
        normalized['informacion_basica.empresa'] = df['empresa']
        normalized['informacion_basica.empresa_id'] = df['id_empresa'].astype(str)
        normalized['informacion_basica.descripcion'] = df['descripcion']
        normalized['informacion_basica.descripcion_limpia'] = df['descripcion'].apply(
            self._limpiar_html
        )

        # === UBICACION ===
        normalized['ubicacion.pais'] = 'Argentina'
        normalized['ubicacion.provincia'] = df['localizacion'].apply(
            self._extraer_provincia_zonajobs
        )
        normalized['ubicacion.ciudad'] = df['localizacion'].apply(
            self._extraer_ciudad_zonajobs
        )
        normalized['ubicacion.ubicacion_raw'] = df['localizacion']
        normalized['ubicacion.codigo_postal'] = None

        # === MODALIDAD ===
        normalized['modalidad.tipo_trabajo'] = df['tipo_trabajo'].apply(
            self._normalizar_tipo_trabajo
        )
        normalized['modalidad.modalidad_trabajo'] = df['modalidad_trabajo'].apply(
            self._normalizar_modalidad
        )
        normalized['modalidad.tipo_trabajo_raw'] = df['tipo_trabajo']
        normalized['modalidad.modalidad_raw'] = df['modalidad_trabajo']

        # === FECHAS ===
        normalized['fechas.fecha_publicacion'] = df['fecha_publicacion'].apply(
            self._convertir_fecha_iso
        )
        normalized['fechas.fecha_modificacion'] = df.get('fecha_modificacion', pd.Series([None] * len(df))).apply(
            self._convertir_fecha_iso
        )
        normalized['fechas.fecha_cierre'] = None
        normalized['fechas.fecha_publicacion_raw'] = df['fecha_publicacion']

        # === REQUISITOS ===
        normalized['requisitos.experiencia_minima'] = None
        normalized['requisitos.nivel_educativo'] = None
        normalized['requisitos.idiomas'] = None
        normalized['requisitos.habilidades'] = None
        normalized['requisitos.certificaciones'] = None

        # === COMPENSACION ===
        normalized['compensacion.salario_minimo'] = None
        normalized['compensacion.salario_maximo'] = None
        normalized['compensacion.moneda'] = 'ARS'
        normalized['compensacion.periodo'] = None
        normalized['compensacion.salario_raw'] = None
        normalized['compensacion.beneficios'] = None

        # === DETALLES ===
        normalized['detalles.cantidad_vacantes'] = df.get('cantidad_vacantes', None)
        normalized['detalles.area_trabajo'] = None
        normalized['detalles.nivel_puesto'] = None
        normalized['detalles.apto_discapacitado'] = df.get('apto_discapacitado', None)
        normalized['detalles.confidencial'] = df.get('empresa_confidencial', None)

        # === CLASIFICACION ESCO (vacío, se llena en etapa 03) ===
        normalized['clasificacion_esco.ocupacion_esco_code'] = None
        normalized['clasificacion_esco.ocupacion_esco_label'] = None
        normalized['clasificacion_esco.isco_code'] = None
        normalized['clasificacion_esco.isco_label'] = None
        normalized['clasificacion_esco.similarity_score'] = None
        normalized['clasificacion_esco.skills'] = None
        normalized['clasificacion_esco.matching_method'] = None
        normalized['clasificacion_esco.matching_timestamp'] = None

        # === SOURCE SPECIFIC ===
        # Guardar campos específicos de ZonaJobs que no están en schema
        source_specific = {}
        for col in df.columns:
            if col not in [
                'id_oferta', 'titulo', 'empresa', 'id_empresa', 'descripcion',
                'localizacion', 'modalidad_trabajo', 'tipo_trabajo',
                'fecha_publicacion', 'fecha_modificacion', 'cantidad_vacantes',
                'apto_discapacitado', 'url_oferta', 'scrapeado_en'
            ]:
                source_specific[col] = df[col].tolist()

        if source_specific:
            normalized['source_specific'] = [source_specific for _ in range(len(df))]
        else:
            normalized['source_specific'] = None

        return normalized

    def _extraer_provincia_zonajobs(self, ubicacion: str) -> Optional[str]:
        """Extrae provincia de string de ubicación de ZonaJobs"""
        if pd.isna(ubicacion):
            return None

        ubicacion_lower = str(ubicacion).lower()

        # Mapeo de provincias
        provincias = {
            'capital federal': 'CABA',
            'buenos aires': 'Buenos Aires',
            'córdoba': 'Córdoba',
            'santa fe': 'Santa Fe',
            'mendoza': 'Mendoza',
            'tucumán': 'Tucumán',
            'entre ríos': 'Entre Ríos',
            'salta': 'Salta',
            'misiones': 'Misiones',
            'chaco': 'Chaco',
            'corrientes': 'Corrientes',
            'santiago del estero': 'Santiago del Estero',
            'jujuy': 'Jujuy',
            'san juan': 'San Juan',
            'río negro': 'Río Negro',
            'formosa': 'Formosa',
            'neuquén': 'Neuquén',
            'chubut': 'Chubut',
            'san luis': 'San Luis',
            'catamarca': 'Catamarca',
            'la rioja': 'La Rioja',
            'la pampa': 'La Pampa',
            'santa cruz': 'Santa Cruz',
            'tierra del fuego': 'Tierra del Fuego'
        }

        for key, value in provincias.items():
            if key in ubicacion_lower:
                return value

        return None

    def _extraer_ciudad_zonajobs(self, ubicacion: str) -> Optional[str]:
        """Extrae ciudad de string de ubicación de ZonaJobs"""
        if pd.isna(ubicacion):
            return None

        # Por ahora, retornar la ubicación completa
        # Podría implementarse un parser más sofisticado
        return str(ubicacion)


class BumeranNormalizer(BaseNormalizer):
    """Normalizador para datos de Bumeran"""

    def __init__(self):
        super().__init__('bumeran')

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de Bumeran al schema unificado"""

        # Crear DataFrame normalizado con el índice correcto
        normalized = pd.DataFrame(index=df.index)

        # === METADATA ===
        normalized['_metadata.source'] = 'bumeran'
        normalized['_metadata.source_id'] = df['id_oferta'].astype(str)
        normalized['_metadata.unified_id'] = normalized['_metadata.source_id'].apply(
            lambda x: self._create_unified_id(x)
        )
        normalized['_metadata.url_oferta'] = df['url_oferta']
        normalized['_metadata.fecha_extraccion'] = df['scrapeado_en'].apply(
            self._convertir_fecha_iso
        )
        normalized['_metadata.version_scraper'] = '1.0'

        # === INFORMACION BASICA ===
        normalized['informacion_basica.titulo'] = df['titulo']
        normalized['informacion_basica.titulo_normalizado'] = df['titulo'].apply(
            self._normalizar_texto
        )
        normalized['informacion_basica.empresa'] = df['empresa']
        normalized['informacion_basica.empresa_id'] = df['id_empresa'].astype(str)
        normalized['informacion_basica.descripcion'] = df['descripcion']
        normalized['informacion_basica.descripcion_limpia'] = df['descripcion'].apply(
            self._limpiar_html
        )

        # === UBICACION ===
        normalized['ubicacion.pais'] = 'Argentina'
        normalized['ubicacion.provincia'] = df['localizacion'].apply(
            self._extraer_provincia_bumeran
        )
        normalized['ubicacion.ciudad'] = df['localizacion'].apply(
            self._extraer_ciudad_bumeran
        )
        normalized['ubicacion.ubicacion_raw'] = df['localizacion']
        normalized['ubicacion.codigo_postal'] = None

        # === MODALIDAD ===
        normalized['modalidad.tipo_trabajo'] = df['tipo_trabajo'].apply(
            self._normalizar_tipo_trabajo
        )
        normalized['modalidad.modalidad_trabajo'] = df['modalidad_trabajo'].apply(
            self._normalizar_modalidad
        )
        normalized['modalidad.tipo_trabajo_raw'] = df['tipo_trabajo']
        normalized['modalidad.modalidad_raw'] = df['modalidad_trabajo']

        # === FECHAS ===
        normalized['fechas.fecha_publicacion'] = df['fecha_publicacion'].apply(
            self._convertir_fecha_bumeran
        )
        normalized['fechas.fecha_modificacion'] = df.get('fecha_modificado', pd.Series([None] * len(df))).apply(
            self._convertir_fecha_bumeran
        )
        normalized['fechas.fecha_cierre'] = None
        normalized['fechas.fecha_publicacion_raw'] = df['fecha_publicacion']

        # === REQUISITOS ===
        normalized['requisitos.experiencia_minima'] = None
        normalized['requisitos.nivel_educativo'] = None
        normalized['requisitos.idiomas'] = None
        normalized['requisitos.habilidades'] = None
        normalized['requisitos.certificaciones'] = None

        # === COMPENSACION ===
        normalized['compensacion.salario_minimo'] = None
        normalized['compensacion.salario_maximo'] = None
        normalized['compensacion.moneda'] = 'ARS'
        normalized['compensacion.periodo'] = None
        normalized['compensacion.salario_raw'] = None
        normalized['compensacion.beneficios'] = None

        # === DETALLES ===
        normalized['detalles.cantidad_vacantes'] = df.get('cantidad_vacantes', None)
        normalized['detalles.area_trabajo'] = df.get('id_area', None).astype(str) if 'id_area' in df.columns else None
        normalized['detalles.nivel_puesto'] = None
        normalized['detalles.apto_discapacitado'] = df.get('apto_discapacitado', None)
        normalized['detalles.confidencial'] = df.get('confidencial', None)

        # === CLASIFICACION ESCO (vacío, se llena en etapa 03) ===
        normalized['clasificacion_esco.ocupacion_esco_code'] = None
        normalized['clasificacion_esco.ocupacion_esco_label'] = None
        normalized['clasificacion_esco.isco_code'] = None
        normalized['clasificacion_esco.isco_label'] = None
        normalized['clasificacion_esco.similarity_score'] = None
        normalized['clasificacion_esco.skills'] = None
        normalized['clasificacion_esco.matching_method'] = None
        normalized['clasificacion_esco.matching_timestamp'] = None

        # === SOURCE SPECIFIC ===
        # Guardar campos específicos de Bumeran
        source_specific_cols = [
            'logo_url', 'empresa_validada', 'empresa_pro', 'promedio_empresa',
            'plan_publicacion_id', 'plan_publicacion_nombre', 'portal',
            'tipo_aviso', 'tiene_preguntas', 'salario_obligatorio',
            'alta_revision_perfiles', 'id_subarea', 'id_pais'
        ]

        source_specific = {}
        for col in source_specific_cols:
            if col in df.columns:
                source_specific[col] = df[col].tolist()

        if source_specific:
            normalized['source_specific'] = [source_specific for _ in range(len(df))]
        else:
            normalized['source_specific'] = None

        return normalized

    def _extraer_provincia_bumeran(self, ubicacion: str) -> Optional[str]:
        """Extrae provincia de string de ubicación de Bumeran"""
        if pd.isna(ubicacion):
            return None

        ubicacion_str = str(ubicacion)

        # Bumeran usa formato "Ciudad, Provincia"
        if ',' in ubicacion_str:
            partes = ubicacion_str.split(',')
            if len(partes) >= 2:
                provincia = partes[-1].strip()

                # Mapeo de provincias
                provincias_map = {
                    'buenos aires': 'Buenos Aires',
                    'capital federal': 'CABA',
                    'caba': 'CABA',
                    'córdoba': 'Córdoba',
                    'cordoba': 'Córdoba',
                    'santa fe': 'Santa Fe',
                    'mendoza': 'Mendoza',
                    'tucumán': 'Tucumán',
                    'tucuman': 'Tucumán',
                }

                provincia_lower = provincia.lower()
                return provincias_map.get(provincia_lower, provincia)

        return None

    def _extraer_ciudad_bumeran(self, ubicacion: str) -> Optional[str]:
        """Extrae ciudad de string de ubicación de Bumeran"""
        if pd.isna(ubicacion):
            return None

        ubicacion_str = str(ubicacion)

        # Bumeran usa formato "Ciudad, Provincia"
        if ',' in ubicacion_str:
            partes = ubicacion_str.split(',')
            return partes[0].strip()

        return ubicacion_str

    def _convertir_fecha_bumeran(self, fecha: Any) -> Optional[str]:
        """Convierte fecha de Bumeran a formato ISO 8601"""
        if pd.isna(fecha):
            return None

        try:
            # Bumeran usa formato "DD-MM-YYYY" o "DD-MM-YYYY HH:MM:SS"
            fecha_str = str(fecha).strip()

            # Intentar parsear diferentes formatos
            for fmt in ['%d-%m-%Y %H:%M:%S', '%d-%m-%Y']:
                try:
                    dt = datetime.strptime(fecha_str, fmt)
                    return dt.isoformat()
                except:
                    continue

            # Si no funciona, usar pandas
            dt = pd.to_datetime(fecha, errors='coerce')
            if pd.notna(dt):
                return dt.isoformat()

        except:
            pass

        return None


class ComputRabajoNormalizer(BaseNormalizer):
    """Normalizador para datos de ComputRabajo"""

    def __init__(self):
        super().__init__('computrabajo')

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de ComputRabajo al schema unificado"""

        ofertas_normalizadas = []

        for _, row in df.iterrows():
            # Parsear ubicación "Ciudad, Provincia"
            ciudad, provincia = self._parsear_ubicacion(row.get('ubicacion'))

            oferta_normalizada = {
                # Metadata
                '_metadata': {
                    'source': 'computrabajo',
                    'source_id': str(row.get('id_oferta', '')),
                    'unified_id': f"computrabajo_{str(row.get('id_oferta', ''))}",
                    'url_oferta': row.get('url_completa', ''),
                    'fecha_scraping': row.get('scrapeado_en', datetime.now().isoformat()),
                    'version_schema': '1.0'
                },

                # Información Básica
                'informacion_basica': {
                    'titulo': row.get('titulo', ''),
                    'descripcion': '',  # ComputRabajo no tiene descripción en listado
                    'empresa': row.get('empresa', ''),
                    'empresa_validada': False,  # No disponible
                    'empresa_id': '',  # No disponible en listado
                    'empresa_url': row.get('empresa_url', ''),
                    'logo_url': ''  # No disponible en listado
                },

                # Ubicación
                'ubicacion': {
                    'ubicacion_raw': row.get('ubicacion', ''),
                    'provincia': provincia,
                    'ciudad': ciudad,
                    'zona': '',  # No disponible
                    'pais': 'Argentina'
                },

                # Modalidad
                'modalidad': {
                    'modalidad_trabajo': self._normalizar_modalidad(row.get('modalidad')),
                    'tipo_trabajo': '',  # No disponible en listado
                    'nivel_laboral': ''  # No disponible en listado
                },

                # Fechas
                'fechas': {
                    'fecha_publicacion': row.get('fecha_publicacion', ''),  # Ya en ISO
                    'fecha_cierre': '',  # No disponible
                    'fecha_actualizacion': ''  # No disponible
                },

                # Requisitos
                'requisitos': {
                    'estudios_minimos': '',  # No disponible en listado
                    'experiencia_minima': '',  # No disponible en listado
                    'habilidades': [],  # No disponible en listado
                    'idiomas': []  # No disponible en listado
                },

                # Compensación
                'compensacion': {
                    'salario_minimo': None,  # No disponible
                    'salario_maximo': None,  # No disponible
                    'moneda': '',  # No disponible
                    'mostrar_salario': False,  # No disponible
                    'beneficios': []  # No disponible
                },

                # Detalles
                'detalles': {
                    'cantidad_vacantes': None,  # No disponible en listado
                    'area_trabajo': '',  # No disponible
                    'subarea': ''  # No disponible
                },

                # Clasificación ESCO (se completa en etapa 3)
                'clasificacion_esco': {
                    'ocupacion_esco_uri': '',
                    'ocupacion_esco_codigo': '',
                    'ocupacion_esco_titulo': '',
                    'habilidades_esco': [],
                    'confidence_score': None
                },

                # Campos específicos de ComputRabajo
                'source_specific': {
                    'empresa_rating': row.get('empresa_rating'),
                    'fecha_publicacion_raw': row.get('fecha_publicacion_raw', ''),  # "Hace X horas"
                    'url_relativa': row.get('url_relativa', '')
                }
            }

            ofertas_normalizadas.append(oferta_normalizada)

        # Convertir a DataFrame con columnas expandidas
        df_normalized = pd.json_normalize(ofertas_normalizadas, sep='.')

        return df_normalized

    def _parsear_ubicacion(self, ubicacion_raw: str) -> tuple:
        """
        Parsea ubicación de ComputRabajo "Ciudad, Provincia"

        Args:
            ubicacion_raw: String de ubicación

        Returns:
            Tuple (ciudad, provincia)
        """
        if not ubicacion_raw or pd.isna(ubicacion_raw):
            return ('', '')

        # Formato típico: "Balvanera, Capital Federal" o "Monserrat, Capital Federal"
        if ',' in ubicacion_raw:
            partes = ubicacion_raw.split(',')
            ciudad = partes[0].strip()
            provincia = partes[1].strip() if len(partes) > 1 else ''

            # Normalizar "Capital Federal" a "Buenos Aires"
            if provincia == 'Capital Federal':
                provincia = 'Buenos Aires'

            return (ciudad, provincia)

        # Si no tiene coma, asumir que es ciudad
        return (ubicacion_raw.strip(), '')


# Factory para obtener normalizador por fuente
def get_normalizer(source: str) -> BaseNormalizer:
    """Obtiene normalizador para una fuente específica"""
    normalizers = {
        'zonajobs': ZonaJobsNormalizer,
        'bumeran': BumeranNormalizer,
        'computrabajo': ComputRabajoNormalizer,
        'linkedin': LinkedInNormalizer,
        'indeed': IndeedNormalizer,
    }

    if source not in normalizers:
        raise ValueError(f"Fuente '{source}' no soportada. Fuentes disponibles: {list(normalizers.keys())}")

    return normalizers[source]()


if __name__ == "__main__":
    # Test con datos de ZonaJobs
    print("=== Test de Normalizador ZonaJobs ===\n")

    # Cargar datos de ejemplo (ajustar path)
    import glob
    zonajobs_files = glob.glob(str(project_root / "01_sources" / "zonajobs" / "data" / "raw" / "*.csv"))

    if zonajobs_files:
        latest_file = max(zonajobs_files)
        print(f"Cargando: {latest_file}")

        df_raw = pd.read_csv(latest_file)
        print(f"Ofertas cargadas: {len(df_raw)}")

        normalizer = ZonaJobsNormalizer()
        df_normalized = normalizer.normalize(df_raw)

        print(f"\nCampos normalizados: {len(df_normalized.columns)}")
        print("\nPrimeras columnas:")
        print(df_normalized.columns.tolist()[:10])

        print("\nPrimera oferta normalizada:")
        print(df_normalized.iloc[0].to_dict())
    else:
        print("No se encontraron archivos de ZonaJobs")


class LinkedInNormalizer(BaseNormalizer):
    """Normalizador para datos de LinkedIn (via JobSpy)"""

    def __init__(self):
        super().__init__('linkedin')

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de LinkedIn al schema unificado"""

        ofertas_normalizadas = []

        for _, row in df.iterrows():
            # Parsear ubicación
            ciudad, provincia = self._parsear_ubicacion_linkedin(row.get('location', ''))

            # Determinar modalidad según is_remote
            modalidad = self._determinar_modalidad(row.get('is_remote'), row.get('location', ''))

            oferta_normalizada = {
                # Metadata
                '_metadata': {
                    'source': 'linkedin',
                    'source_id': str(row.get('id', '')),
                    'unified_id': f"linkedin_{str(row.get('id', ''))}",
                    'url_oferta': row.get('job_url', ''),
                    'fecha_scraping': row.get('scrapeado_en', datetime.now().isoformat()),
                    'version_schema': '1.0'
                },

                # Información Básica
                'informacion_basica': {
                    'titulo': row.get('title', ''),
                    'descripcion': row.get('description', ''),
                    'empresa': row.get('company', ''),
                    'empresa_validada': False,
                    'empresa_id': '',
                    'empresa_url': row.get('company_url', ''),
                    'logo_url': row.get('company_logo', '')
                },

                # Ubicación
                'ubicacion': {
                    'ubicacion_raw': row.get('location', ''),
                    'provincia': provincia,
                    'ciudad': ciudad,
                    'zona': '',
                    'pais': 'Argentina'
                },

                # Modalidad
                'modalidad': {
                    'modalidad_trabajo': modalidad,
                    'esquema_horario': '',
                    'disponibilidad': ''
                },

                # Fechas
                'fechas': {
                    'fecha_publicacion': self._convertir_fecha_iso(row.get('date_posted')),
                    'fecha_cierre': '',
                    'fecha_inicio': ''
                },

                # Requisitos (vacíos - no disponibles en scraping básico)
                'requisitos': {
                    'experiencia_requerida': row.get('experience_range', ''),
                    'nivel_educativo': '',
                    'areas_estudio': '',
                    'idiomas': '',
                    'conocimientos_tecnicos': row.get('skills', '')
                },

                # Condiciones (vacíos)
                'condiciones': {
                    'tipo_contrato': row.get('job_type', ''),
                    'nivel_jerarquico': row.get('job_level', ''),
                    'rango_salarial': self._formatear_salario(row),
                    'beneficios': ''
                },

                # Descripción (vacío - requiere fetch_description=True)
                'descripcion': {
                    'descripcion_completa': row.get('description', ''),
                    'responsabilidades': '',
                    'requisitos_deseables': ''
                },

                # Source specific
                'source_specific': {
                    'job_function': row.get('job_function', ''),
                    'listing_type': row.get('listing_type', ''),
                    'company_industry': row.get('company_industry', ''),
                    'company_num_employees': row.get('company_num_employees', ''),
                    'company_revenue': row.get('company_revenue', ''),
                    'search_term_usado': row.get('search_term_usado', ''),
                    'work_from_home_type': row.get('work_from_home_type', '')
                }
            }

            ofertas_normalizadas.append(oferta_normalizada)

        # Convertir a DataFrame flat
        df_normalized = pd.json_normalize(ofertas_normalizadas, sep='.')

        return df_normalized

    def _parsear_ubicacion_linkedin(self, location_str):
        """
        Parsea ubicación de LinkedIn
        Formato puede ser: "Ciudad, Provincia, Argentina" o "Provincia, Argentina" o similar
        """
        if pd.isna(location_str) or location_str == '':
            return '', ''

        # Remover "Argentina" si está presente
        location_clean = location_str.replace(', Argentina', '').replace(',Argentina', '')

        # Split por coma
        parts = [p.strip() for p in location_clean.split(',')]

        if len(parts) >= 2:
            # "Ciudad, Provincia"
            ciudad = parts[0]
            provincia = parts[1]
        elif len(parts) == 1:
            # Solo provincia o ciudad
            ciudad = parts[0]
            provincia = parts[0]
        else:
            ciudad = location_clean
            provincia = ''

        # Normalizar "Capital Federal" → "Buenos Aires"
        if provincia == 'Capital Federal' or ciudad == 'Capital Federal':
            provincia = 'Buenos Aires'

        return ciudad, provincia

    def _determinar_modalidad(self, is_remote, location):
        """Determina modalidad según is_remote flag"""
        if pd.isna(is_remote):
            return ''

        if is_remote == True:
            return 'remoto'
        elif is_remote == False:
            # Si no es remoto y tiene ubicación, es presencial
            if pd.notna(location) and str(location).strip():
                return 'presencial'
            else:
                return ''
        else:
            return ''

    def _formatear_salario(self, row):
        """Formatea rango salarial si está disponible"""
        min_sal = row.get('min_amount')
        max_sal = row.get('max_amount')
        currency = row.get('currency')
        interval = row.get('interval')

        if pd.notna(min_sal) or pd.notna(max_sal):
            parts = []
            if currency:
                parts.append(currency)
            if pd.notna(min_sal):
                parts.append(f"{min_sal}")
            if pd.notna(max_sal):
                parts.append(f"- {max_sal}")
            if interval:
                parts.append(f"({interval})")
            return ' '.join(parts)
        return ''


class IndeedNormalizer(BaseNormalizer):
    """Normalizador para datos de Indeed (via JobSpy)"""

    def __init__(self):
        super().__init__('indeed')

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza DataFrame de LinkedIn al schema unificado"""

        ofertas_normalizadas = []

        for _, row in df.iterrows():
            # Parsear ubicación
            ciudad, provincia = self._parsear_ubicacion_indeed(row.get('location', ''))

            # Determinar modalidad según is_remote
            modalidad = self._determinar_modalidad(row.get('is_remote'), row.get('location', ''))

            oferta_normalizada = {
                # Metadata
                '_metadata': {
                    'source': 'indeed',
                    'source_id': str(row.get('id', '')),
                    'unified_id': f"indeed_{str(row.get('id', ''))}",
                    'url_oferta': row.get('job_url', ''),
                    'fecha_scraping': row.get('scrapeado_en', datetime.now().isoformat()),
                    'version_schema': '1.0'
                },

                # Información Básica
                'informacion_basica': {
                    'titulo': row.get('title', ''),
                    'descripcion': row.get('description', ''),
                    'empresa': row.get('company', ''),
                    'empresa_validada': False,
                    'empresa_id': '',
                    'empresa_url': row.get('company_url', ''),
                    'logo_url': row.get('company_logo', '')
                },

                # Ubicación
                'ubicacion': {
                    'ubicacion_raw': row.get('location', ''),
                    'provincia': provincia,
                    'ciudad': ciudad,
                    'zona': '',
                    'pais': 'Argentina'
                },

                # Modalidad
                'modalidad': {
                    'modalidad_trabajo': modalidad,
                    'esquema_horario': '',
                    'disponibilidad': ''
                },

                # Fechas
                'fechas': {
                    'fecha_publicacion': self._convertir_fecha_iso(row.get('date_posted')),
                    'fecha_cierre': '',
                    'fecha_inicio': ''
                },

                # Requisitos (vacíos - no disponibles en scraping básico)
                'requisitos': {
                    'experiencia_requerida': row.get('experience_range', ''),
                    'nivel_educativo': '',
                    'areas_estudio': '',
                    'idiomas': '',
                    'conocimientos_tecnicos': row.get('skills', '')
                },

                # Condiciones (vacíos)
                'condiciones': {
                    'tipo_contrato': row.get('job_type', ''),
                    'nivel_jerarquico': row.get('job_level', ''),
                    'rango_salarial': self._formatear_salario(row),
                    'beneficios': ''
                },

                # Descripción (vacío - requiere fetch_description=True)
                'descripcion': {
                    'descripcion_completa': row.get('description', ''),
                    'responsabilidades': '',
                    'requisitos_deseables': ''
                },

                # Source specific
                'source_specific': {
                    'job_function': row.get('job_function', ''),
                    'listing_type': row.get('listing_type', ''),
                    'company_industry': row.get('company_industry', ''),
                    'company_num_employees': row.get('company_num_employees', ''),
                    'company_revenue': row.get('company_revenue', ''),
                    'search_term_usado': row.get('search_term_usado', ''),
                    'work_from_home_type': row.get('work_from_home_type', '')
                }
            }

            ofertas_normalizadas.append(oferta_normalizada)

        # Convertir a DataFrame flat
        df_normalized = pd.json_normalize(ofertas_normalizadas, sep='.')

        return df_normalized

    def _parsear_ubicacion_indeed(self, location_str):
        """
        Parsea ubicación de LinkedIn
        Formato puede ser: "Ciudad, Provincia, Argentina" o "Provincia, Argentina" o similar
        """
        if pd.isna(location_str) or location_str == '':
            return '', ''

        # Remover "Argentina" si está presente
        location_clean = location_str.replace(', Argentina', '').replace(',Argentina', '')

        # Split por coma
        parts = [p.strip() for p in location_clean.split(',')]

        if len(parts) >= 2:
            # "Ciudad, Provincia"
            ciudad = parts[0]
            provincia = parts[1]
        elif len(parts) == 1:
            # Solo provincia o ciudad
            ciudad = parts[0]
            provincia = parts[0]
        else:
            ciudad = location_clean
            provincia = ''

        # Normalizar "Capital Federal" → "Buenos Aires"
        if provincia == 'Capital Federal' or ciudad == 'Capital Federal':
            provincia = 'Buenos Aires'

        return ciudad, provincia

    def _determinar_modalidad(self, is_remote, location):
        """Determina modalidad según is_remote flag"""
        if pd.isna(is_remote):
            return ''

        if is_remote == True:
            return 'remoto'
        elif is_remote == False:
            # Si no es remoto y tiene ubicación, es presencial
            if pd.notna(location) and str(location).strip():
                return 'presencial'
            else:
                return ''
        else:
            return ''

    def _formatear_salario(self, row):
        """Formatea rango salarial si está disponible"""
        min_sal = row.get('min_amount')
        max_sal = row.get('max_amount')
        currency = row.get('currency')
        interval = row.get('interval')

        if pd.notna(min_sal) or pd.notna(max_sal):
            parts = []
            if currency:
                parts.append(currency)
            if pd.notna(min_sal):
                parts.append(f"{min_sal}")
            if pd.notna(max_sal):
                parts.append(f"- {max_sal}")
            if interval:
                parts.append(f"({interval})")
            return ' '.join(parts)
        return ''
