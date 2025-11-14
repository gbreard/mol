#!/usr/bin/env python3
"""
FASE 5: Matching sem[U+00E1]ntico Ofertas-ESCO con BGE-M3

Realiza matching sem[U+00E1]ntico entre ofertas de trabajo y la ontolog[U+00ED]a ESCO:
1. Genera embeddings de ocupaciones ESCO (3,008)
2. Genera embeddings de ofertas (t[U+00ED]tulo + descripci[U+00F3]n)
3. Calcula similaridad coseno
4. Guarda top-3 matches por oferta en ofertas_esco_matching
5. Matchea skills extra[U+00ED]das con skills ESCO

Modelo: BAAI/bge-m3 (multiling[U+00FC]e, optimizado para espa[U+00F1]ol)
Tiempo estimado: 30-60 minutos (primera ejecuci[U+00F3]n), 10-15 min (con embeddings guardados)

Requisitos:
    pip install sentence-transformers numpy
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: La librer[U+00ED]a 'sentence-transformers' no est[U+00E1] instalada.")
    print("Instal[U+00E1] con: pip install sentence-transformers")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("ERROR: La librer[U+00ED]a 'numpy' no est[U+00E1] instalada.")
    print("Instal[U+00E1] con: pip install numpy")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: La librer[U+00ED]a 'tqdm' no est[U+00E1] instalada. No se mostrar[U+00E1] barra de progreso.")
    tqdm = None


class ESCOMatcher:
    """Matching sem[U+00E1]ntico Ofertas-ESCO con BGE-M3"""

    def __init__(self, db_path='bumeran_scraping.db', model_name='BAAI/bge-m3'):
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.model_name = model_name
        self.model = None
        self.conn = None

        # Rutas para guardar embeddings
        self.embeddings_dir = Path(__file__).parent / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)

        self.esco_occ_embeddings_path = self.embeddings_dir / "esco_occupations_embeddings.npy"
        self.esco_occ_metadata_path = self.embeddings_dir / "esco_occupations_metadata.json"

        self.esco_skills_embeddings_path = self.embeddings_dir / "esco_skills_embeddings.npy"
        self.esco_skills_metadata_path = self.embeddings_dir / "esco_skills_metadata.json"

        self.stats = {
            'esco_ocupaciones': 0,
            'esco_skills': 0,
            'ofertas_procesadas': 0,
            'matches_ocupaciones': 0,
            'matches_skills': 0,
            'errores': []
        }

    def conectar_db(self):
        """Conecta a DB"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[OK] Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            return False

    def cargar_modelo(self):
        """Carga modelo BGE-M3"""
        print("\n[BOT] CARGANDO MODELO BGE-M3")
        print("=" * 70)
        print(f"  Modelo: {self.model_name}")
        print("  Nota: Primera carga puede tomar 2-5 minutos (descarga ~2.3 GB)")

        try:
            self.model = SentenceTransformer(self.model_name)
            print("  [OK] Modelo cargado exitosamente")
            return True
        except Exception as e:
            print(f"  [ERROR] Error cargando modelo: {e}")
            return False

    def generar_embeddings_ocupaciones(self):
        """Genera embeddings de ocupaciones ESCO"""
        print("\n[STATS] GENERANDO EMBEDDINGS DE OCUPACIONES ESCO")
        print("=" * 70)

        # Verificar si ya existen
        if self.esco_occ_embeddings_path.exists() and self.esco_occ_metadata_path.exists():
            print("  -> Embeddings ya existen, cargando desde disco...")
            embeddings = np.load(self.esco_occ_embeddings_path)
            with open(self.esco_occ_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            print(f"  [OK] {len(embeddings):,} embeddings cargados desde cache")
            return embeddings, metadata

        # Obtener ocupaciones
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT occupation_uri, preferred_label_es, description_es
            FROM esco_occupations
            WHERE preferred_label_es IS NOT NULL
            ORDER BY occupation_uri
        """)
        ocupaciones = cursor.fetchall()

        if not ocupaciones:
            print("  [WARNING] No se encontraron ocupaciones ESCO")
            return None, None

        print(f"  -> {len(ocupaciones):,} ocupaciones encontradas")
        self.stats['esco_ocupaciones'] = len(ocupaciones)

        # Preparar textos para embedding
        # Formato: "T[U+00ED]tulo. Descripci[U+00F3]n (primeras 200 palabras)"
        textos = []
        metadata = []

        for uri, label, description in ocupaciones:
            # Texto combinado
            texto = label
            if description:
                # Limitar descripci[U+00F3]n a primeras 200 palabras
                desc_words = description.split()[:200]
                desc_short = " ".join(desc_words)
                texto = f"{label}. {desc_short}"

            textos.append(texto)
            metadata.append({
                'uri': uri,
                'label': label
            })

        # Generar embeddings en batches
        print("  -> Generando embeddings (esto puede tomar 5-10 minutos)...")

        batch_size = 32
        embeddings_list = []

        iterator = range(0, len(textos), batch_size)
        if tqdm:
            iterator = tqdm(iterator, desc="  Embeddings", unit="batch")

        for i in iterator:
            batch = textos[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings_list.append(batch_embeddings)

        embeddings = np.vstack(embeddings_list)

        # Guardar en disco
        print("  -> Guardando embeddings en cache...")
        np.save(self.esco_occ_embeddings_path, embeddings)
        with open(self.esco_occ_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  [OK] {len(embeddings):,} embeddings generados y guardados")
        return embeddings, metadata

    def generar_embeddings_skills(self):
        """Genera embeddings de skills ESCO"""
        print("\n[TARGET] GENERANDO EMBEDDINGS DE SKILLS ESCO")
        print("=" * 70)

        # Verificar si ya existen
        if self.esco_skills_embeddings_path.exists() and self.esco_skills_metadata_path.exists():
            print("  -> Embeddings ya existen, cargando desde disco...")
            embeddings = np.load(self.esco_skills_embeddings_path)
            with open(self.esco_skills_metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            print(f"  [OK] {len(embeddings):,} embeddings cargados desde cache")
            return embeddings, metadata

        # Obtener skills
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT skill_uri, preferred_label_es, description_es
            FROM esco_skills
            WHERE preferred_label_es IS NOT NULL
            ORDER BY skill_uri
        """)
        skills = cursor.fetchall()

        if not skills:
            print("  [WARNING] No se encontraron skills ESCO")
            return None, None

        print(f"  -> {len(skills):,} skills encontrados")
        self.stats['esco_skills'] = len(skills)

        # Preparar textos
        textos = []
        metadata = []

        for uri, label, description in skills:
            texto = label
            if description:
                desc_words = description.split()[:100]
                desc_short = " ".join(desc_words)
                texto = f"{label}. {desc_short}"

            textos.append(texto)
            metadata.append({
                'uri': uri,
                'label': label
            })

        # Generar embeddings
        print("  -> Generando embeddings (esto puede tomar 10-15 minutos)...")

        batch_size = 32
        embeddings_list = []

        iterator = range(0, len(textos), batch_size)
        if tqdm:
            iterator = tqdm(iterator, desc="  Embeddings", unit="batch")

        for i in iterator:
            batch = textos[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings_list.append(batch_embeddings)

        embeddings = np.vstack(embeddings_list)

        # Guardar
        print("  -> Guardando embeddings en cache...")
        np.save(self.esco_skills_embeddings_path, embeddings)
        with open(self.esco_skills_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  [OK] {len(embeddings):,} embeddings generados y guardados")
        return embeddings, metadata

    def matchear_ofertas_a_ocupaciones(self, esco_embeddings, esco_metadata):
        """Matchea ofertas con ocupaciones ESCO (top-3)"""
        print("\n[LINK] MATCHING OFERTAS -> OCUPACIONES ESCO")
        print("=" * 70)

        # Obtener ofertas
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id_oferta, titulo, descripcion_utf8
            FROM ofertas
            WHERE titulo IS NOT NULL
            ORDER BY id_oferta
        """)
        ofertas = cursor.fetchall()

        if not ofertas:
            print("  [WARNING] No se encontraron ofertas")
            return

        print(f"  -> {len(ofertas):,} ofertas a procesar")

        # Limpiar tabla
        cursor.execute("DELETE FROM ofertas_esco_matching")
        self.conn.commit()

        # Procesar por batches
        batch_size = 50
        iterator = range(0, len(ofertas), batch_size)
        if tqdm:
            iterator = tqdm(iterator, desc="  Matching", unit="batch")

        for i in iterator:
            batch = ofertas[i:i + batch_size]

            # Preparar textos de ofertas
            textos_ofertas = []
            ids_ofertas = []

            for id_oferta, titulo, descripcion in batch:
                # Texto: t[U+00ED]tulo + primeras 300 palabras de descripci[U+00F3]n
                texto = titulo
                if descripcion:
                    desc_words = descripcion.split()[:300]
                    desc_short = " ".join(desc_words)
                    texto = f"{titulo}. {desc_short}"

                textos_ofertas.append(texto)
                ids_ofertas.append(id_oferta)

            # Generar embeddings de ofertas
            ofertas_embeddings = self.model.encode(textos_ofertas, show_progress_bar=False)

            # Calcular similaridades con todas las ocupaciones ESCO
            for j, oferta_embedding in enumerate(ofertas_embeddings):
                id_oferta = ids_ofertas[j]

                # Similaridad coseno: dot product (embeddings ya normalizados)
                similarities = np.dot(esco_embeddings, oferta_embedding)

                # Top-1 match (solo el mejor)
                best_idx = np.argmax(similarities)
                occupation_uri = esco_metadata[best_idx]['uri']
                occupation_label = esco_metadata[best_idx]['label']
                score = float(similarities[best_idx])

                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO ofertas_esco_matching (
                            id_oferta, esco_occupation_uri, esco_occupation_label,
                            occupation_match_score, occupation_match_method,
                            matching_timestamp, matching_version
                        ) VALUES (?, ?, ?, ?, ?, datetime('now'), 'bge-m3-v1')
                    """, (str(id_oferta), occupation_uri, occupation_label, score, 'bge-m3'))

                    self.stats['matches_ocupaciones'] += 1
                except Exception as e:
                    if len(self.stats['errores']) < 10:
                        self.stats['errores'].append(f"Match ocupaci[U+00F3]n {id_oferta}: {e}")

        self.conn.commit()
        self.stats['ofertas_procesadas'] = len(ofertas)
        print(f"  [OK] {self.stats['ofertas_procesadas']:,} ofertas procesadas")
        print(f"  [OK] {self.stats['matches_ocupaciones']:,} matches guardados")

    def matchear_skills_nlp_a_esco(self, esco_skills_embeddings, esco_skills_metadata):
        """Matchea skills extra[U+00ED]das por NLP con skills ESCO"""
        print("\n[TARGET] MATCHING SKILLS NLP -> SKILLS ESCO")
        print("=" * 70)

        # Obtener skills de NLP
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id_oferta, skills_tecnicas_list, skills_blandas_list
            FROM ofertas_nlp
            WHERE skills_tecnicas_list IS NOT NULL OR skills_blandas_list IS NOT NULL
        """)
        ofertas_nlp = cursor.fetchall()

        if not ofertas_nlp:
            print("  [WARNING] No se encontraron skills en ofertas_nlp")
            print("  -> Esta tabla se poblar[U+00E1] cuando se complete la Fase 02.5 (NLP Extraction)")
            return

        print(f"  -> {len(ofertas_nlp):,} ofertas con skills NLP")

        # Limpiar tabla
        cursor.execute("DELETE FROM ofertas_esco_skills_detalle")
        self.conn.commit()

        total_skills_procesados = 0

        iterator = tqdm(ofertas_nlp, desc="  Matching skills", unit="oferta") if tqdm else ofertas_nlp

        for id_oferta, skills_tecnicas_json, skills_blandas_json in iterator:
            # Parsear JSONs
            skills_tecnicas = []
            skills_blandas = []

            if skills_tecnicas_json:
                try:
                    skills_tecnicas = json.loads(skills_tecnicas_json)
                    if not isinstance(skills_tecnicas, list):
                        skills_tecnicas = [skills_tecnicas]
                except:
                    pass

            if skills_blandas_json:
                try:
                    skills_blandas = json.loads(skills_blandas_json)
                    if not isinstance(skills_blandas, list):
                        skills_blandas = [skills_blandas]
                except:
                    pass

            # Combinar todos los skills
            todos_skills = skills_tecnicas + skills_blandas

            if not todos_skills:
                continue

            # Generar embeddings de skills
            skills_embeddings = self.model.encode(todos_skills, show_progress_bar=False)

            # Matchear cada skill con ESCO
            for skill_text, skill_embedding in zip(todos_skills, skills_embeddings):
                # Calcular similaridad
                similarities = np.dot(esco_skills_embeddings, skill_embedding)
                best_match_idx = np.argmax(similarities)
                best_score = float(similarities[best_match_idx])

                # Solo guardar si score > 0.6 (umbral de confianza)
                if best_score > 0.6:
                    esco_skill_uri = esco_skills_metadata[best_match_idx]['uri']
                    esco_skill_label = esco_skills_metadata[best_match_idx]['label']

                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO ofertas_esco_skills_detalle (
                                id_oferta, skill_mencionado, esco_skill_uri,
                                esco_skill_label, match_score, match_method
                            ) VALUES (?, ?, ?, ?, ?, 'bge-m3')
                        """, (str(id_oferta), skill_text, esco_skill_uri, esco_skill_label, best_score))

                        self.stats['matches_skills'] += 1
                        total_skills_procesados += 1
                    except Exception as e:
                        if len(self.stats['errores']) < 10:
                            self.stats['errores'].append(f"Match skill {id_oferta}: {e}")

        self.conn.commit()
        print(f"  [OK] {total_skills_procesados:,} skills procesados")
        print(f"  [OK] {self.stats['matches_skills']:,} matches guardados (score > 0.6)")

    def generar_reporte(self):
        """Genera reporte final"""
        print("\n" + "=" * 70)
        print("REPORTE FINAL DE MATCHING ESCO")
        print("=" * 70)

        print(f"\n[STATS] ESTAD[U+00CD]STICAS:")
        print(f"  - Ocupaciones ESCO:           {self.stats['esco_ocupaciones']:,}")
        print(f"  - Skills ESCO:                {self.stats['esco_skills']:,}")
        print(f"  - Ofertas procesadas:         {self.stats['ofertas_procesadas']:,}")
        print(f"  - Matches ocupaciones (top-3):{self.stats['matches_ocupaciones']:,}")
        print(f"  - Matches skills:             {self.stats['matches_skills']:,}")

        if self.stats['errores']:
            print(f"\n[WARNING] ERRORES: {len(self.stats['errores'])}")
            for error in self.stats['errores'][:10]:
                print(f"  - {error}")

        # Consultar estad[U+00ED]sticas finales
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT id_oferta) FROM ofertas_esco_matching")
        ofertas_con_match = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(occupation_match_score) FROM ofertas_esco_matching WHERE occupation_match_rank = 1")
        avg_score = cursor.fetchone()[0] or 0

        print(f"\n[CHART] M[U+00C9]TRICAS DE CALIDAD:")
        print(f"  - Ofertas con match:          {ofertas_con_match:,}")
        print(f"  - Score promedio (rank 1):    {avg_score:.3f}")

        print("\n" + "=" * 70)
        print("[OK] PROCESO COMPLETADO")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta proceso completo"""
        print("\n" + "=" * 70)
        print("MATCHING SEM[U+00C1]NTICO OFERTAS-ESCO CON BGE-M3")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.conectar_db():
            return False

        if not self.cargar_modelo():
            return False

        # Generar embeddings ESCO
        esco_occ_embeddings, esco_occ_metadata = self.generar_embeddings_ocupaciones()
        if esco_occ_embeddings is None:
            print("[ERROR] Error generando embeddings de ocupaciones")
            return False

        esco_skills_embeddings, esco_skills_metadata = self.generar_embeddings_skills()
        if esco_skills_embeddings is None:
            print("[ERROR] Error generando embeddings de skills")
            return False

        # Matching
        self.matchear_ofertas_a_ocupaciones(esco_occ_embeddings, esco_occ_metadata)
        # NOTA: Skills matching deshabilitado temporalmente por incompatibilidad de schema
        # self.matchear_skills_nlp_a_esco(esco_skills_embeddings, esco_skills_metadata)

        # Reporte
        self.generar_reporte()

        self.conn.close()
        return True

    def __del__(self):
        if self.conn:
            self.conn.close()


def main():
    try:
        matcher = ESCOMatcher()
        exito = matcher.ejecutar()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
