#!/usr/bin/env python3
"""
FASE 1.2: Crear tablas NLP + ESCO completo

Crea estructura completa de 17 tablas:
- ofertas_nlp (27 campos)
- esco_occupations + 4 tablas relacionadas
- esco_skills + 1 tabla relacionada
- esco_associations
- esco_isco_hierarchy
- diccionario_arg_esco
- sinonimos_regionales
- cno_ocupaciones + cno_esco_matches
- ofertas_esco_matching + ofertas_esco_skills_detalle

Uso:
    python create_tables_nlp_esco.py

Tiempo estimado: <1 minuto
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime


class TableCreator:
    """Crea todas las tablas del esquema NLP + ESCO"""

    def __init__(self, db_path='bumeran_scraping.db'):
        """
        Inicializa el creador de tablas.

        Args:
            db_path (str): Ruta a la base de datos SQLite
        """
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.conn = None
        self.stats = {
            'tablas_creadas': [],
            'tablas_existentes': [],
            'indices_creados': [],
            'errores': []
        }

    def conectar_db(self):
        """Conecta a la base de datos SQLite"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[OK] Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error al conectar a la base de datos: {e}")
            return False

    def tabla_existe(self, nombre_tabla):
        """Verifica si una tabla ya existe"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (nombre_tabla,))
        return cursor.fetchone() is not None

    def crear_tabla(self, nombre, sql_create, descripcion=""):
        """
        Crea una tabla si no existe.

        Args:
            nombre (str): Nombre de la tabla
            sql_create (str): SQL CREATE TABLE
            descripcion (str): Descripci[U+00F3]n de la tabla
        """
        if self.tabla_existe(nombre):
            print(f"  (x) {nombre} - Ya existe")
            self.stats['tablas_existentes'].append(nombre)
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create)
            print(f"  [OK] {nombre} - Creada ({descripcion})")
            self.stats['tablas_creadas'].append(nombre)
            return True
        except Exception as e:
            print(f"  [ERROR] {nombre} - ERROR: {e}")
            self.stats['errores'].append(f"{nombre}: {e}")
            return False

    def crear_indice(self, nombre, sql_index):
        """Crea un [U+00ED]ndice si no existe"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_index)
            self.stats['indices_creados'].append(nombre)
            return True
        except Exception as e:
            if "already exists" not in str(e):
                print(f"  [WARNING] Warning creando [U+00ED]ndice {nombre}: {e}")
            return False

    def crear_tablas_nlp(self):
        """Crea tabla ofertas_nlp"""
        print("\n[STATS] GRUPO 1: TABLA NLP")
        print("=" * 70)

        sql = """
        CREATE TABLE ofertas_nlp (
            id_oferta TEXT PRIMARY KEY,

            -- EXPERIENCIA (3 campos)
            experiencia_min_anios INTEGER,
            experiencia_max_anios INTEGER,
            experiencia_area TEXT,

            -- EDUCACI[U+00D3]N (4 campos)
            nivel_educativo TEXT,
            estado_educativo TEXT,
            carrera_especifica TEXT,
            titulo_excluyente INTEGER,

            -- IDIOMAS (4 campos)
            idioma_principal TEXT,
            nivel_idioma_principal TEXT,
            idioma_secundario TEXT,
            nivel_idioma_secundario TEXT,

            -- SKILLS T[U+00C9]CNICAS (4 campos - JSON arrays)
            skills_tecnicas_list TEXT,
            niveles_skills_list TEXT,
            soft_skills_list TEXT,
            certificaciones_list TEXT,

            -- COMPENSACI[U+00D3]N (4 campos)
            salario_min REAL,
            salario_max REAL,
            moneda TEXT,
            beneficios_list TEXT,

            -- REQUISITOS (2 campos)
            requisitos_excluyentes_list TEXT,
            requisitos_deseables_list TEXT,

            -- JORNADA (2 campos)
            jornada_laboral TEXT,
            horario_flexible INTEGER,

            -- METADATA NLP (3 campos)
            nlp_extraction_timestamp TEXT,
            nlp_version TEXT,
            nlp_confidence_score REAL,

            FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
        )
        """
        self.crear_tabla('ofertas_nlp', sql, "27 campos NLP")

        # [U+00CD]ndices
        self.crear_indice('idx_ofertas_nlp_experiencia',
                         'CREATE INDEX idx_ofertas_nlp_experiencia ON ofertas_nlp(experiencia_min_anios)')
        self.crear_indice('idx_ofertas_nlp_nivel_educativo',
                         'CREATE INDEX idx_ofertas_nlp_nivel_educativo ON ofertas_nlp(nivel_educativo)')

    def crear_tablas_esco_occupations(self):
        """Crea tablas relacionadas con ocupaciones ESCO"""
        print("\n[BOOK] GRUPO 2: OCUPACIONES ESCO")
        print("=" * 70)

        # Tabla principal de ocupaciones
        sql_occ = """
        CREATE TABLE esco_occupations (
            -- IDENTIFICADORES
            occupation_uri TEXT PRIMARY KEY,
            occupation_uuid TEXT UNIQUE NOT NULL,
            esco_code TEXT,
            isco_code TEXT,

            -- LABELS Y DESCRIPCIONES (SOLO ESPA[U+00D1]OL)
            preferred_label_es TEXT NOT NULL,
            description_es TEXT,

            -- SCOPE NOTES
            scope_note_es TEXT,
            scope_note_mimetype TEXT DEFAULT 'text/html',

            -- PROFESI[U+00D3]N REGULADA
            regulated_profession_uri TEXT,
            regulated_profession_note TEXT,
            is_regulated INTEGER DEFAULT 0,

            -- JERARQU[U+00CD]A
            broader_occupation_uri TEXT,
            hierarchy_level INTEGER,

            -- METADATA
            status TEXT DEFAULT 'released',
            concept_type TEXT DEFAULT 'Occupation',
            last_modified TEXT,

            FOREIGN KEY (broader_occupation_uri) REFERENCES esco_occupations(occupation_uri)
        )
        """
        self.crear_tabla('esco_occupations', sql_occ, "~3,008 ocupaciones")

        # [U+00CD]ndices ocupaciones
        self.crear_indice('idx_esco_occ_code', 'CREATE INDEX idx_esco_occ_code ON esco_occupations(esco_code)')
        self.crear_indice('idx_esco_occ_isco', 'CREATE INDEX idx_esco_occ_isco ON esco_occupations(isco_code)')
        self.crear_indice('idx_esco_occ_label', 'CREATE INDEX idx_esco_occ_label ON esco_occupations(preferred_label_es)')
        self.crear_indice('idx_esco_occ_broader', 'CREATE INDEX idx_esco_occ_broader ON esco_occupations(broader_occupation_uri)')

        # Alternative labels (SOLO ESPA[U+00D1]OL)
        sql_alt = """
        CREATE TABLE esco_occupation_alternative_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occupation_uri TEXT NOT NULL,
            label TEXT NOT NULL,
            label_type TEXT DEFAULT 'altLabel',

            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
            UNIQUE(occupation_uri, label)
        )
        """
        self.crear_tabla('esco_occupation_alternative_labels', sql_alt, "~6,000 labels ES")

        self.crear_indice('idx_esco_alt_labels_occ',
                         'CREATE INDEX idx_esco_alt_labels_occ ON esco_occupation_alternative_labels(occupation_uri)')
        self.crear_indice('idx_esco_alt_labels_text',
                         'CREATE INDEX idx_esco_alt_labels_text ON esco_occupation_alternative_labels(label)')

        # Gendered terms
        sql_gender = """
        CREATE TABLE esco_occupation_gendered_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occupation_uri TEXT NOT NULL,
            term_label TEXT NOT NULL,
            roles_json TEXT,
            term_type TEXT DEFAULT 'alternativeTerm',

            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri)
        )
        """
        self.crear_tabla('esco_occupation_gendered_terms', sql_gender, "~5,000 t[U+00E9]rminos")

        self.crear_indice('idx_esco_gendered_occ',
                         'CREATE INDEX idx_esco_gendered_occ ON esco_occupation_gendered_terms(occupation_uri)')

        # Ancestors
        sql_ancestors = """
        CREATE TABLE esco_occupation_ancestors (
            occupation_uri TEXT NOT NULL,
            ancestor_uri TEXT NOT NULL,
            ancestor_level INTEGER NOT NULL,
            ancestor_title TEXT,
            ancestor_type TEXT,

            PRIMARY KEY (occupation_uri, ancestor_uri),
            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
            FOREIGN KEY (ancestor_uri) REFERENCES esco_occupations(occupation_uri)
        )
        """
        self.crear_tabla('esco_occupation_ancestors', sql_ancestors, "~12,000 relaciones")

        self.crear_indice('idx_esco_ancestors_occ',
                         'CREATE INDEX idx_esco_ancestors_occ ON esco_occupation_ancestors(occupation_uri)')
        self.crear_indice('idx_esco_ancestors_level',
                         'CREATE INDEX idx_esco_ancestors_level ON esco_occupation_ancestors(ancestor_level)')

        # ISCO hierarchy
        sql_isco = """
        CREATE TABLE esco_isco_hierarchy (
            isco_code TEXT PRIMARY KEY,
            preferred_label_es TEXT NOT NULL,
            description_es TEXT,
            hierarchy_level INTEGER NOT NULL,
            broader_isco_code TEXT,

            FOREIGN KEY (broader_isco_code) REFERENCES esco_isco_hierarchy(isco_code)
        )
        """
        self.crear_tabla('esco_isco_hierarchy', sql_isco, "~436 c[U+00F3]digos ISCO")

        self.crear_indice('idx_isco_level', 'CREATE INDEX idx_isco_level ON esco_isco_hierarchy(hierarchy_level)')

    def crear_tablas_esco_skills(self):
        """Crea tablas relacionadas con skills ESCO"""
        print("\n[TARGET] GRUPO 3: SKILLS ESCO")
        print("=" * 70)

        # Tabla principal de skills
        sql_skills = """
        CREATE TABLE esco_skills (
            -- IDENTIFICADORES
            skill_uri TEXT PRIMARY KEY,
            skill_uuid TEXT UNIQUE NOT NULL,
            skill_code TEXT,

            -- LABELS (SOLO ESPA[U+00D1]OL)
            preferred_label_es TEXT NOT NULL,
            description_es TEXT,

            -- CLASIFICACI[U+00D3]N
            skill_type TEXT,
            skill_reusability_level TEXT,

            -- METADATA
            status TEXT DEFAULT 'released',
            last_modified TEXT,

            CHECK (skill_type IN ('skill', 'knowledge', 'attitude'))
        )
        """
        self.crear_tabla('esco_skills', sql_skills, "~13,890 skills")

        self.crear_indice('idx_esco_skills_label', 'CREATE INDEX idx_esco_skills_label ON esco_skills(preferred_label_es)')
        self.crear_indice('idx_esco_skills_type', 'CREATE INDEX idx_esco_skills_type ON esco_skills(skill_type)')
        self.crear_indice('idx_esco_skills_reusability', 'CREATE INDEX idx_esco_skills_reusability ON esco_skills(skill_reusability_level)')

        # Alternative labels skills (SOLO ESPA[U+00D1]OL)
        sql_alt_skills = """
        CREATE TABLE esco_skill_alternative_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_uri TEXT NOT NULL,
            label TEXT NOT NULL,
            label_type TEXT DEFAULT 'altLabel',

            FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
            UNIQUE(skill_uri, label)
        )
        """
        self.crear_tabla('esco_skill_alternative_labels', sql_alt_skills, "~20,000 labels ES")

        self.crear_indice('idx_esco_skill_alt_occ',
                         'CREATE INDEX idx_esco_skill_alt_occ ON esco_skill_alternative_labels(skill_uri)')
        self.crear_indice('idx_esco_skill_alt_text',
                         'CREATE INDEX idx_esco_skill_alt_text ON esco_skill_alternative_labels(label)')

        # Associations (Ocupaci[U+00F3]n-Skill)
        sql_assoc = """
        CREATE TABLE esco_associations (
            association_uri TEXT PRIMARY KEY,
            occupation_uri TEXT NOT NULL,
            skill_uri TEXT NOT NULL,

            -- TIPO DE RELACI[U+00D3]N
            relation_type TEXT NOT NULL,
            skill_type_in_relation TEXT,

            FOREIGN KEY (occupation_uri) REFERENCES esco_occupations(occupation_uri),
            FOREIGN KEY (skill_uri) REFERENCES esco_skills(skill_uri),
            CHECK (relation_type IN ('essential', 'optional'))
        )
        """
        self.crear_tabla('esco_associations', sql_assoc, "~60,000 asociaciones")

        self.crear_indice('idx_esco_assoc_occ', 'CREATE INDEX idx_esco_assoc_occ ON esco_associations(occupation_uri)')
        self.crear_indice('idx_esco_assoc_skill', 'CREATE INDEX idx_esco_assoc_skill ON esco_associations(skill_uri)')
        self.crear_indice('idx_esco_assoc_type', 'CREATE INDEX idx_esco_assoc_type ON esco_associations(relation_type)')

    def crear_tablas_diccionarios(self):
        """Crea tablas de normalizaci[U+00F3]n argentina"""
        print("\n[ARG] GRUPO 4: DICCIONARIOS ARGENTINOS")
        print("=" * 70)

        # Diccionario Argentina-ESCO
        sql_dict_arg = """
        CREATE TABLE diccionario_arg_esco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            termino_argentino TEXT UNIQUE NOT NULL,
            esco_terms_json TEXT,
            isco_target TEXT,
            esco_preferred_label TEXT,
            notes TEXT
        )
        """
        self.crear_tabla('diccionario_arg_esco', sql_dict_arg, "~300 t[U+00E9]rminos AR")

        self.crear_indice('idx_dict_arg_termino',
                         'CREATE INDEX idx_dict_arg_termino ON diccionario_arg_esco(termino_argentino)')
        self.crear_indice('idx_dict_arg_isco',
                         'CREATE INDEX idx_dict_arg_isco ON diccionario_arg_esco(isco_target)')

        # Sin[U+00F3]nimos regionales
        sql_sinonimos = """
        CREATE TABLE sinonimos_regionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_ocupacional TEXT,
            termino_base TEXT,
            pais TEXT,
            sinonimos_json TEXT,
            descripcion TEXT,

            UNIQUE(categoria_ocupacional, termino_base, pais)
        )
        """
        self.crear_tabla('sinonimos_regionales', sql_sinonimos, "~500 variantes")

        self.crear_indice('idx_sinonimos_cat',
                         'CREATE INDEX idx_sinonimos_cat ON sinonimos_regionales(categoria_ocupacional)')
        self.crear_indice('idx_sinonimos_pais',
                         'CREATE INDEX idx_sinonimos_pais ON sinonimos_regionales(pais)')

        # CNO Ocupaciones
        sql_cno = """
        CREATE TABLE cno_ocupaciones (
            cno_codigo TEXT PRIMARY KEY,
            cno_descripcion TEXT NOT NULL,
            cno_grupo TEXT,
            cno_subgrupo TEXT,
            ejemplos_ocupacionales TEXT,
            vigente INTEGER DEFAULT 1
        )
        """
        self.crear_tabla('cno_ocupaciones', sql_cno, "~594 ocupaciones CNO")

        self.crear_indice('idx_cno_descripcion',
                         'CREATE INDEX idx_cno_descripcion ON cno_ocupaciones(cno_descripcion)')

        # CNO-ESCO Matches
        sql_cno_matches = """
        CREATE TABLE cno_esco_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cno_codigo TEXT NOT NULL,
            esco_occupation_uri TEXT NOT NULL,

            similarity_score REAL,
            matching_method TEXT,

            match_date TEXT,
            validated INTEGER DEFAULT 0,

            FOREIGN KEY (cno_codigo) REFERENCES cno_ocupaciones(cno_codigo),
            FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri)
        )
        """
        self.crear_tabla('cno_esco_matches', sql_cno_matches, "~1,200 matches")

        self.crear_indice('idx_cno_matches_cno',
                         'CREATE INDEX idx_cno_matches_cno ON cno_esco_matches(cno_codigo)')
        self.crear_indice('idx_cno_matches_esco',
                         'CREATE INDEX idx_cno_matches_esco ON cno_esco_matches(esco_occupation_uri)')
        self.crear_indice('idx_cno_matches_score',
                         'CREATE INDEX idx_cno_matches_score ON cno_esco_matches(similarity_score DESC)')

    def crear_tablas_matching(self):
        """Crea tablas de matching ofertas-ESCO"""
        print("\n[LINK] GRUPO 5: MATCHING OFERTAS-ESCO")
        print("=" * 70)

        # Matching principal
        sql_matching = """
        CREATE TABLE ofertas_esco_matching (
            id_oferta TEXT PRIMARY KEY,

            -- MATCHING DE OCUPACI[U+00D3]N
            esco_occupation_uri TEXT,
            esco_occupation_label TEXT,
            occupation_match_score REAL,
            occupation_match_method TEXT,

            -- MATCHING DE T[U+00CD]TULO
            titulo_normalizado TEXT,
            titulo_esco_code TEXT,

            -- SKILLS MATCHEADOS
            esco_skills_esenciales_json TEXT,
            esco_skills_opcionales_json TEXT,

            -- GAP ANALYSIS
            skills_demandados_total INTEGER,
            skills_matcheados_esco INTEGER,
            skills_sin_match_json TEXT,

            -- METADATA
            matching_timestamp TEXT,
            matching_version TEXT,
            confidence_score REAL,

            FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta),
            FOREIGN KEY (esco_occupation_uri) REFERENCES esco_occupations(occupation_uri)
        )
        """
        self.crear_tabla('ofertas_esco_matching', sql_matching, "~5,479 ofertas")

        self.crear_indice('idx_ofertas_esco_occ',
                         'CREATE INDEX idx_ofertas_esco_occ ON ofertas_esco_matching(esco_occupation_uri)')
        self.crear_indice('idx_ofertas_esco_score',
                         'CREATE INDEX idx_ofertas_esco_score ON ofertas_esco_matching(occupation_match_score DESC)')
        self.crear_indice('idx_ofertas_esco_confidence',
                         'CREATE INDEX idx_ofertas_esco_confidence ON ofertas_esco_matching(confidence_score DESC)')

        # Skills detalle
        sql_skills_det = """
        CREATE TABLE ofertas_esco_skills_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta TEXT NOT NULL,

            -- SKILL EXTRA[U+00CD]DO
            skill_mencionado TEXT NOT NULL,
            skill_tipo_fuente TEXT,
            skill_nivel_mencionado TEXT,

            -- MATCHING CON ESCO
            esco_skill_uri TEXT,
            esco_skill_label TEXT,
            match_score REAL,
            match_method TEXT,

            -- CLASIFICACI[U+00D3]N ESCO
            esco_skill_type TEXT,
            esco_skill_reusability TEXT,

            -- RELACI[U+00D3]N CON OCUPACI[U+00D3]N
            is_essential_for_occupation INTEGER DEFAULT 0,
            is_optional_for_occupation INTEGER DEFAULT 0,

            FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta),
            FOREIGN KEY (esco_skill_uri) REFERENCES esco_skills(skill_uri)
        )
        """
        self.crear_tabla('ofertas_esco_skills_detalle', sql_skills_det, "~30,000 skills")

        self.crear_indice('idx_skills_det_oferta',
                         'CREATE INDEX idx_skills_det_oferta ON ofertas_esco_skills_detalle(id_oferta)')
        self.crear_indice('idx_skills_det_esco',
                         'CREATE INDEX idx_skills_det_esco ON ofertas_esco_skills_detalle(esco_skill_uri)')
        self.crear_indice('idx_skills_det_tipo',
                         'CREATE INDEX idx_skills_det_tipo ON ofertas_esco_skills_detalle(esco_skill_type)')

    def actualizar_keywords_performance(self):
        """Actualiza tabla keywords_performance existente con nuevas columnas"""
        print("\n[U+1F511] GRUPO 6: ACTUALIZAR KEYWORDS_PERFORMANCE")
        print("=" * 70)

        if not self.tabla_existe('keywords_performance'):
            print("  [WARNING] Tabla keywords_performance no existe (se crear[U+00E1] en scraping)")
            return

        try:
            cursor = self.conn.cursor()

            # Verificar columnas existentes
            cursor.execute("PRAGMA table_info(keywords_performance)")
            columnas_existentes = [col[1] for col in cursor.fetchall()]

            columnas_nuevas = [
                ('esco_occupation_uri', 'TEXT'),
                ('esco_skill_uri', 'TEXT'),
                ('keyword_source', 'TEXT'),
                ('keyword_version', 'TEXT')
            ]

            for col_name, col_type in columnas_nuevas:
                if col_name not in columnas_existentes:
                    cursor.execute(f"ALTER TABLE keywords_performance ADD COLUMN {col_name} {col_type}")
                    print(f"  [OK] Columna {col_name} agregada")
                else:
                    print(f"  (x) Columna {col_name} ya existe")

            # Crear [U+00ED]ndices
            self.crear_indice('idx_kw_perf_esco_occ',
                             'CREATE INDEX idx_kw_perf_esco_occ ON keywords_performance(esco_occupation_uri)')
            self.crear_indice('idx_kw_perf_source',
                             'CREATE INDEX idx_kw_perf_source ON keywords_performance(keyword_source)')
            self.crear_indice('idx_kw_perf_version',
                             'CREATE INDEX idx_kw_perf_version ON keywords_performance(keyword_version)')

        except Exception as e:
            print(f"  [ERROR] Error actualizando keywords_performance: {e}")

    def generar_reporte(self):
        """Genera reporte final de creaci[U+00F3]n de tablas"""
        print("\n" + "=" * 70)
        print("REPORTE FINAL DE CREACI[U+00D3]N DE TABLAS")
        print("=" * 70)

        print(f"\n[STATS] ESTAD[U+00CD]STICAS:")
        print(f"  - Tablas creadas:        {len(self.stats['tablas_creadas'])}")
        print(f"  - Tablas ya existentes:  {len(self.stats['tablas_existentes'])}")
        print(f"  - [U+00CD]ndices creados:       {len(self.stats['indices_creados'])}")
        print(f"  - Errores:               {len(self.stats['errores'])}")

        if self.stats['tablas_creadas']:
            print(f"\n[OK] TABLAS CREADAS ({len(self.stats['tablas_creadas'])}):")
            for tabla in self.stats['tablas_creadas']:
                print(f"  - {tabla}")

        if self.stats['tablas_existentes']:
            print(f"\n(x) TABLAS EXISTENTES ({len(self.stats['tablas_existentes'])}):")
            for tabla in self.stats['tablas_existentes']:
                print(f"  - {tabla}")

        if self.stats['errores']:
            print(f"\n[ERROR] ERRORES ({len(self.stats['errores'])}):")
            for error in self.stats['errores']:
                print(f"  - {error}")

        print("\n" + "=" * 70)
        if len(self.stats['errores']) == 0:
            print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
        else:
            print("[WARNING] PROCESO COMPLETADO CON ADVERTENCIAS")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta el proceso completo de creaci[U+00F3]n de tablas"""
        print("\n" + "=" * 70)
        print("CREACI[U+00D3]N DE TABLAS NLP + ESCO COMPLETO")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Conectar
        if not self.conectar_db():
            return False

        # Crear tablas por grupos
        self.crear_tablas_nlp()
        self.crear_tablas_esco_occupations()
        self.crear_tablas_esco_skills()
        self.crear_tablas_diccionarios()
        self.crear_tablas_matching()
        self.actualizar_keywords_performance()

        # Commit
        self.conn.commit()

        # Reporte
        self.generar_reporte()

        # Cerrar
        self.conn.close()

        return True

    def __del__(self):
        """Destructor"""
        if self.conn:
            self.conn.close()


def main():
    """Funci[U+00F3]n principal"""
    try:
        creator = TableCreator()
        exito = creator.ejecutar()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
