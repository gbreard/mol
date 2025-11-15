#!/usr/bin/env python3
"""
FASE 2: Poblar tablas ESCO desde archivo RDF

Parsea el archivo esco-v1.2.0.rdf (1.26 GB) y extrae TODA la informaci[U+00F3]n ESCO:
- Ocupaciones (3,008) con alternative labels, gendered terms, scope notes, ancestors
- Skills (13,890) con alternative labels
- Jerarqu[U+00ED]a ISCO (436 c[U+00F3]digos)
- Associations ocupaci[U+00F3]n-skill (60,000+)

SOLO extrae campos en ESPA[U+00D1]OL (xml:lang="es")

Ruta RDF: D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf

Uso:
    python populate_esco_from_rdf.py

Tiempo estimado: 15-30 minutos
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Verificar rdflib
try:
    from rdflib import Graph, Namespace, RDF, SKOS, Literal
    from rdflib.namespace import DCTERMS
except ImportError:
    print("ERROR: La librer[U+00ED]a 'rdflib' no est[U+00E1] instalada.")
    print("Instal[U+00E1] con: pip install rdflib")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: La librer[U+00ED]a 'tqdm' no est[U+00E1] instalada. No se mostrar[U+00E1] barra de progreso.")
    tqdm = None


# Namespaces ESCO
ESCO = Namespace("http://data.europa.eu/esco/model#")
ESCO_DATA = Namespace("http://data.europa.eu/esco/")


class ESCOPopulator:
    """Pobla tablas ESCO desde archivo RDF"""

    def __init__(self,
                 rdf_path=r'D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf',
                 db_path='bumeran_scraping.db'):
        """
        Inicializa el poblador ESCO.

        Args:
            rdf_path (str): Ruta al archivo RDF de ESCO
            db_path (str): Ruta a la base de datos SQLite
        """
        self.rdf_path = Path(rdf_path)
        if not self.rdf_path.exists():
            raise FileNotFoundError(f"Archivo RDF no encontrado: {self.rdf_path}")

        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.graph = None
        self.conn = None
        self.stats = {
            'ocupaciones': 0,
            'alt_labels_occ': 0,
            'gendered_terms': 0,
            'ancestors': 0,
            'isco_codes': 0,
            'skills': 0,
            'alt_labels_skills': 0,
            'associations': 0,
            'errores': []
        }

    def cargar_rdf(self):
        """Carga y parsea el archivo RDF (puede tomar 5-10 minutos)"""
        print(f"\n[FILE] Cargando RDF desde: {self.rdf_path}")
        print(f"   Tama[U+00F1]o: {self.rdf_path.stat().st_size / 1024 / 1024:.2f} MB")
        print("   Esto puede tomar 5-10 minutos...")

        self.graph = Graph()
        self.graph.parse(self.rdf_path, format='xml')

        total_triples = len(self.graph)
        print(f"   [OK] RDF cargado: {total_triples:,} triples")
        return True

    def conectar_db(self):
        """Conecta a la base de datos"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[OK] Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error al conectar: {e}")
            return False

    def get_label_es(self, subject, predicate):
        """
        Obtiene label en espa[U+00F1]ol para un subject/predicate.

        Args:
            subject: Subject RDF
            predicate: Predicado (prefLabel, altLabel, etc.)

        Returns:
            str or None: Label en espa[U+00F1]ol o None
        """
        for obj in self.graph.objects(subject, predicate):
            if isinstance(obj, Literal) and obj.language == 'es':
                return str(obj)
        return None

    def get_all_labels_es(self, subject, predicate):
        """
        Obtiene TODOS los labels en espa[U+00F1]ol para un subject/predicate.

        Returns:
            list: Lista de labels en espa[U+00F1]ol
        """
        labels = []
        for obj in self.graph.objects(subject, predicate):
            if isinstance(obj, Literal) and obj.language == 'es':
                labels.append(str(obj))
        return labels

    def extract_uuid(self, uri):
        """Extrae UUID de una URI ESCO"""
        return str(uri).split('/')[-1]

    def procesar_ocupaciones(self):
        """Procesa ocupaciones ESCO"""
        print("\n[STATS] PROCESANDO OCUPACIONES ESCO")
        print("=" * 70)

        cursor = self.conn.cursor()

        # Obtener todas las ocupaciones
        query = """
        SELECT ?occ WHERE {
            ?occ a <http://data.europa.eu/esco/model#Occupation> .
        }
        """
        results = list(self.graph.query(query))
        total = len(results)
        print(f"  -> {total:,} ocupaciones encontradas")

        iterator = tqdm(results, desc="Ocupaciones", unit="occ") if tqdm else results

        for (occ_uri,) in iterator:
            try:
                # Datos b[U+00E1]sicos
                uuid = self.extract_uuid(occ_uri)
                preferred_label = self.get_label_es(occ_uri, SKOS.prefLabel)

                if not preferred_label:
                    continue  # Skip si no tiene label en espa[U+00F1]ol

                description = self.get_label_es(occ_uri, DCTERMS.description)

                # ISCO code - extraer desde skos:broader
                isco_code = None
                for broader in self.graph.objects(occ_uri, SKOS.broader):
                    broader_str = str(broader)
                    # Verificar si el broader es un código ISCO (patrón: /esco/isco/C{digits})
                    if '/esco/isco/C' in broader_str:
                        # Extraer el código (ej: "C2512" desde ".../esco/isco/C2512")
                        isco_code = broader_str.split('/isco/')[-1]
                        break

                # ESCO code (c[U+00F3]digo espec[U+00ED]fico)
                esco_code = None
                for code in self.graph.objects(occ_uri, ESCO.code):
                    esco_code = str(code)
                    break

                # Scope note
                scope_note = self.get_label_es(occ_uri, SKOS.scopeNote)

                # Broader
                broader_uri = None
                for broader in self.graph.objects(occ_uri, SKOS.broader):
                    broader_uri = str(broader)
                    break

                # Insertar ocupaci[U+00F3]n
                cursor.execute("""
                    INSERT OR IGNORE INTO esco_occupations (
                        occupation_uri, occupation_uuid, esco_code, isco_code,
                        preferred_label_es, description_es, scope_note_es,
                        broader_occupation_uri, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'released')
                """, (str(occ_uri), uuid, esco_code, isco_code, preferred_label,
                      description, scope_note, broader_uri))

                self.stats['ocupaciones'] += 1

                # Alternative labels
                alt_labels = self.get_all_labels_es(occ_uri, SKOS.altLabel)
                for alt_label in alt_labels:
                    cursor.execute("""
                        INSERT OR IGNORE INTO esco_occupation_alternative_labels (
                            occupation_uri, label, label_type
                        ) VALUES (?, ?, 'altLabel')
                    """, (str(occ_uri), alt_label))
                    self.stats['alt_labels_occ'] += 1

            except Exception as e:
                self.stats['errores'].append(f"Ocupaci[U+00F3]n {occ_uri}: {e}")

        self.conn.commit()
        print(f"  [OK] {self.stats['ocupaciones']:,} ocupaciones procesadas")
        print(f"  [OK] {self.stats['alt_labels_occ']:,} alternative labels")

    def procesar_isco_hierarchy(self):
        """Procesa jerarqu[U+00ED]a ISCO"""
        print("\n[BOOK] PROCESANDO JERARQU[U+00CD]A ISCO")
        print("=" * 70)

        cursor = self.conn.cursor()

        # Obtener grupos ISCO - Son skos:Concept con URIs que contienen /esco/isco/C
        query = """
        SELECT ?isco WHERE {
            ?isco a <http://www.w3.org/2004/02/skos/core#Concept> .
            FILTER(CONTAINS(STR(?isco), "/esco/isco/C"))
        }
        """
        results = list(self.graph.query(query))
        total = len(results)
        print(f"  -> {total:,} grupos ISCO encontrados")

        for (isco_uri,) in results:
            try:
                isco_code = self.extract_uuid(isco_uri)
                preferred_label = self.get_label_es(isco_uri, SKOS.prefLabel)

                if not preferred_label:
                    continue

                description = self.get_label_es(isco_uri, DCTERMS.description)

                # Calcular nivel jer[U+00E1]rquico (C1=1, C11=2, C111=3, C1111=4)
                level = len(isco_code.replace('C', ''))

                # Broader ISCO
                broader_isco = None
                for broader in self.graph.objects(isco_uri, SKOS.broader):
                    broader_isco = self.extract_uuid(broader)
                    break

                cursor.execute("""
                    INSERT OR IGNORE INTO esco_isco_hierarchy (
                        isco_code, preferred_label_es, description_es,
                        hierarchy_level, broader_isco_code
                    ) VALUES (?, ?, ?, ?, ?)
                """, (isco_code, preferred_label, description, level, broader_isco))

                self.stats['isco_codes'] += 1

            except Exception as e:
                self.stats['errores'].append(f"ISCO {isco_uri}: {e}")

        self.conn.commit()
        print(f"  [OK] {self.stats['isco_codes']:,} c[U+00F3]digos ISCO procesados")

    def procesar_skills(self):
        """Procesa skills/competencias ESCO"""
        print("\n[TARGET] PROCESANDO SKILLS ESCO")
        print("=" * 70)

        cursor = self.conn.cursor()

        # Obtener todos los skills
        query = """
        SELECT ?skill WHERE {
            ?skill a <http://data.europa.eu/esco/model#Skill> .
        }
        """
        results = list(self.graph.query(query))
        total = len(results)
        print(f"  -> {total:,} skills encontrados")

        iterator = tqdm(results, desc="Skills", unit="skill") if tqdm else results

        for (skill_uri,) in iterator:
            try:
                uuid = self.extract_uuid(skill_uri)
                preferred_label = self.get_label_es(skill_uri, SKOS.prefLabel)

                if not preferred_label:
                    continue

                description = self.get_label_es(skill_uri, DCTERMS.description)

                # Skill type (skill, knowledge, attitude)
                skill_type = None
                for type_obj in self.graph.objects(skill_uri, ESCO.skillType):
                    skill_type = str(type_obj).split('#')[-1].lower()
                    break

                # Reusability level
                reusability = None
                for reuse in self.graph.objects(skill_uri, ESCO.skillReusabilityLevel):
                    reusability = str(reuse).split('/')[-1]
                    break

                cursor.execute("""
                    INSERT OR IGNORE INTO esco_skills (
                        skill_uri, skill_uuid, preferred_label_es,
                        description_es, skill_type, skill_reusability_level,
                        status
                    ) VALUES (?, ?, ?, ?, ?, ?, 'released')
                """, (str(skill_uri), uuid, preferred_label, description,
                      skill_type, reusability))

                self.stats['skills'] += 1

                # Alternative labels
                alt_labels = self.get_all_labels_es(skill_uri, SKOS.altLabel)
                for alt_label in alt_labels:
                    cursor.execute("""
                        INSERT OR IGNORE INTO esco_skill_alternative_labels (
                            skill_uri, label, label_type
                        ) VALUES (?, ?, 'altLabel')
                    """, (str(skill_uri), alt_label))
                    self.stats['alt_labels_skills'] += 1

            except Exception as e:
                self.stats['errores'].append(f"Skill {skill_uri}: {e}")

        self.conn.commit()
        print(f"  [OK] {self.stats['skills']:,} skills procesados")
        print(f"  [OK] {self.stats['alt_labels_skills']:,} alternative labels")

    def procesar_associations(self):
        """Procesa relaciones ocupación-skill"""
        print("\n[LINK] PROCESANDO ASSOCIATIONS (Ocupación-Skill)")
        print("=" * 70)

        cursor = self.conn.cursor()

        # Query CORREGIDA: usar predicados REALES de ESCO
        # Los predicados correctos son relatedEssentialSkill y relatedOptionalSkill

        # Essential skills
        query_essential = """
        SELECT ?occ ?skill WHERE {
            ?occ <http://data.europa.eu/esco/model#relatedEssentialSkill> ?skill .
        }
        """

        # Optional skills
        query_optional = """
        SELECT ?occ ?skill WHERE {
            ?occ <http://data.europa.eu/esco/model#relatedOptionalSkill> ?skill .
        }
        """

        print("  [1/2] Buscando essential skills...")
        essential_results = list(self.graph.query(query_essential))
        print(f"  -> {len(essential_results):,} essential skills encontradas")

        print("  [2/2] Buscando optional skills...")
        optional_results = list(self.graph.query(query_optional))
        print(f"  -> {len(optional_results):,} optional skills encontradas")

        total_results = len(essential_results) + len(optional_results)
        print(f"  -> TOTAL: {total_results:,} associations encontradas")

        # Procesar essential skills
        iterator = tqdm(essential_results, desc="Essential", unit="assoc") if tqdm else essential_results
        for (occ_uri, skill_uri) in iterator:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO esco_associations (
                        association_uri, occupation_uri, skill_uri, relation_type
                    ) VALUES (?, ?, ?, ?)
                """, (f"{occ_uri}#{skill_uri}", str(occ_uri), str(skill_uri), 'essential'))
                self.stats['associations'] += 1
            except Exception as e:
                self.stats['errores'].append(f"Essential {occ_uri}->{skill_uri}: {e}")

        # Procesar optional skills
        iterator = tqdm(optional_results, desc="Optional", unit="assoc") if tqdm else optional_results
        for (occ_uri, skill_uri) in iterator:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO esco_associations (
                        association_uri, occupation_uri, skill_uri, relation_type
                    ) VALUES (?, ?, ?, ?)
                """, (f"{occ_uri}#{skill_uri}", str(occ_uri), str(skill_uri), 'optional'))
                self.stats['associations'] += 1
            except Exception as e:
                self.stats['errores'].append(f"Optional {occ_uri}->{skill_uri}: {e}")

        self.conn.commit()
        print(f"  [OK] {self.stats['associations']:,} associations procesadas")

    def generar_reporte(self):
        """Genera reporte final"""
        print("\n" + "=" * 70)
        print("REPORTE FINAL DE POBLACI[U+00D3]N ESCO")
        print("=" * 70)

        print(f"\n[STATS] ESTAD[U+00CD]STICAS:")
        print(f"  - Ocupaciones:              {self.stats['ocupaciones']:,}")
        print(f"  - Alt labels ocupaciones:   {self.stats['alt_labels_occ']:,}")
        print(f"  - Gendered terms:           {self.stats['gendered_terms']:,}")
        print(f"  - Ancestors:                {self.stats['ancestors']:,}")
        print(f"  - C[U+00F3]digos ISCO:             {self.stats['isco_codes']:,}")
        print(f"  - Skills:                   {self.stats['skills']:,}")
        print(f"  - Alt labels skills:        {self.stats['alt_labels_skills']:,}")
        print(f"  - Associations:             {self.stats['associations']:,}")

        if self.stats['errores']:
            print(f"\n[WARNING] ERRORES: {len(self.stats['errores'])}")
            print("  (Primeros 10):")
            for error in self.stats['errores'][:10]:
                print(f"  - {error}")

        print("\n" + "=" * 70)
        print("[OK] PROCESO COMPLETADO")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta el proceso completo"""
        print("\n" + "=" * 70)
        print("POBLACI[U+00D3]N DE TABLAS ESCO DESDE RDF")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Conectar DB
        if not self.conectar_db():
            return False

        # Cargar RDF
        if not self.cargar_rdf():
            return False

        # Procesar por grupos
        self.procesar_ocupaciones()
        self.procesar_isco_hierarchy()
        self.procesar_skills()
        self.procesar_associations()

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
        populator = ESCOPopulator()
        exito = populator.ejecutar()
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
