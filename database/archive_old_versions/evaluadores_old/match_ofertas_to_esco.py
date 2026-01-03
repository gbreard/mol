#!/usr/bin/env python3
"""
FASE 5: Matching semántico Ofertas-ESCO con Pipeline Híbrido BGE-M3 + ESCO-XLM

Realiza matching semántico entre ofertas de trabajo y la ontología ESCO:
1. BGE-M3 genera top-10 ocupaciones candidatas (similarity search)
2. ESCO-XLM re-rankea y selecciona el mejor match (clasificador)
3. Guarda resultado final con ambos scores (similarity + rerank)

Modelos:
- BAAI/bge-m3: Para similarity search inicial (embeddings multilingüe)
- jjzha/esco-xlm-roberta-large: Para re-ranking (especializado ESCO, ACL 2023)

Tiempo estimado: 60-90 minutos (primera ejecución), 20-30 min (con cache)

Requisitos:
    pip install sentence-transformers numpy transformers
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
    print("WARNING: La librería 'tqdm' no está instalada. No se mostrará barra de progreso.")
    tqdm = None

try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    RERANKER_AVAILABLE = True
except ImportError:
    print("WARNING: transformers/torch no disponible. Re-ranking deshabilitado.")
    RERANKER_AVAILABLE = False


def normalizar_embeddings(embeddings):
    """Normaliza embeddings a norma L2 unitaria para similitud coseno correcta"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Evitar división por cero
    norms = np.where(norms == 0, 1, norms)
    return embeddings / norms


class ESCOReranker:
    """
    Re-ranker usando ESCO-XLM-RoBERTa-Large como Cross-Encoder.

    Calcula similaridad semántica entre oferta y cada candidato ESCO
    usando los hidden states del modelo (no clasificación).
    """

    def __init__(self, model_name='jjzha/esco-xlm-roberta-large'):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def cargar(self):
        """Carga modelo ESCO-XLM para re-ranking via embeddings"""
        print(f"\n  [RERANKER] Cargando ESCO-XLM-RoBERTa-Large (Cross-Encoder)...")
        print(f"  -> Device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # Usar AutoModel base (no classification head)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

        print(f"  [OK] Reranker cargado (modo cross-encoder)")
        return True

    def _get_embedding(self, text):
        """Obtiene embedding de un texto usando mean pooling de hidden states"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            # Mean pooling sobre tokens (excluyendo padding)
            attention_mask = inputs['attention_mask']
            hidden_states = outputs.last_hidden_state

            # Expand attention mask
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
            sum_embeddings = torch.sum(hidden_states * mask_expanded, dim=1)
            sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
            embedding = sum_embeddings / sum_mask

        return embedding.cpu().numpy()[0]

    def rerank(self, oferta_texto, candidatos_esco, top_k=1):
        """
        Re-rankea candidatos usando similaridad coseno con ESCO-XLM embeddings.

        El modelo ESCO-XLM está pre-entrenado en texto de ESCO, por lo que
        sus embeddings capturan mejor la semántica ocupacional que BGE-M3.

        Args:
            oferta_texto: Texto de la oferta (título + descripción)
            candidatos_esco: Lista de dicts con 'uri', 'label', 'similarity_score'
            top_k: Número de mejores resultados a retornar

        Returns:
            Lista de candidatos re-rankeados con 'rerank_score'
        """
        if not self.model:
            raise RuntimeError("Modelo no cargado. Llamar a cargar() primero.")

        # Truncar oferta
        oferta_truncada = ' '.join(oferta_texto.split()[:300])

        # Embedding de la oferta
        oferta_embedding = self._get_embedding(oferta_truncada)
        oferta_embedding = oferta_embedding / np.linalg.norm(oferta_embedding)

        # Calcular similaridad con cada candidato
        for candidato in candidatos_esco:
            candidato_embedding = self._get_embedding(candidato['label'])
            candidato_embedding = candidato_embedding / np.linalg.norm(candidato_embedding)

            # Similaridad coseno
            score = float(np.dot(oferta_embedding, candidato_embedding))
            candidato['rerank_score'] = score

        # Ordenar por rerank_score descendente
        candidatos_rankeados = sorted(candidatos_esco, key=lambda x: x['rerank_score'], reverse=True)

        return candidatos_rankeados[:top_k]


class ESCOMatcher:
    """Matching semántico híbrido Ofertas-ESCO con BGE-M3 + ESCO-XLM"""

    def __init__(self, db_path='bumeran_scraping.db',
                 embedding_model='BAAI/bge-m3',
                 use_reranker=True):
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.use_reranker = use_reranker and RERANKER_AVAILABLE
        self.reranker = None
        self.conn = None

        # Rutas para guardar embeddings (BGE-M3)
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
            'reranked': 0,
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

    def cargar_modelos(self):
        """Carga modelo BGE-M3 para embeddings y opcionalmente ESCO-XLM para re-ranking"""
        print("\n[BOT] CARGANDO MODELOS")
        print("=" * 70)

        # 1. Cargar BGE-M3 para embeddings
        print(f"\n  [EMBEDDINGS] Cargando BGE-M3...")
        print(f"  Modelo: {self.embedding_model_name}")
        print("  Nota: Primera carga puede tomar 2-5 minutos")

        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            print("  [OK] BGE-M3 cargado exitosamente")
        except Exception as e:
            print(f"  [ERROR] Error cargando BGE-M3: {e}")
            return False

        # 2. Cargar ESCO-XLM para re-ranking (opcional)
        if self.use_reranker:
            self.reranker = ESCOReranker()
            try:
                self.reranker.cargar()
            except Exception as e:
                print(f"  [WARNING] Error cargando reranker: {e}")
                print("  -> Continuando sin re-ranking")
                self.reranker = None
                self.use_reranker = False
        else:
            print("\n  [INFO] Re-ranking deshabilitado")

        return True

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
            batch_embeddings = self.embedding_model.encode(batch, show_progress_bar=False)
            embeddings_list.append(batch_embeddings)

        embeddings = np.vstack(embeddings_list)

        # Normalizar embeddings para similitud coseno
        print("  -> Normalizando embeddings (L2)...")
        embeddings = normalizar_embeddings(embeddings)

        # Guardar en disco
        print("  -> Guardando embeddings en cache...")
        np.save(self.esco_occ_embeddings_path, embeddings)
        with open(self.esco_occ_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  [OK] {len(embeddings):,} embeddings generados y guardados (BGE-M3, normalizados)")
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
            batch_embeddings = self.embedding_model.encode(batch, show_progress_bar=False)
            embeddings_list.append(batch_embeddings)

        embeddings = np.vstack(embeddings_list)

        # Normalizar embeddings para similitud coseno
        print("  -> Normalizando embeddings (L2)...")
        embeddings = normalizar_embeddings(embeddings)

        # Guardar
        print("  -> Guardando embeddings en cache...")
        np.save(self.esco_skills_embeddings_path, embeddings)
        with open(self.esco_skills_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  [OK] {len(embeddings):,} embeddings generados y guardados (BGE-M3, normalizados)")
        return embeddings, metadata

    def matchear_ofertas_a_ocupaciones(self, esco_embeddings, esco_metadata):
        """
        Matchea ofertas con ocupaciones ESCO usando pipeline híbrido:
        1. BGE-M3 genera top-10 candidatos (similarity search)
        2. ESCO-XLM re-rankea y selecciona el mejor (clasificador)
        """
        print("\n[LINK] MATCHING OFERTAS -> OCUPACIONES ESCO (Pipeline Híbrido)")
        print("=" * 70)

        if self.use_reranker and self.reranker:
            print("  -> Modo: BGE-M3 (top-10) + ESCO-XLM (re-ranking)")
        else:
            print("  -> Modo: Solo BGE-M3 (top-1)")

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

        # Agregar columna rerank_score si no existe
        try:
            cursor.execute("ALTER TABLE ofertas_esco_matching ADD COLUMN rerank_score REAL")
            self.conn.commit()
        except:
            pass  # Columna ya existe

        # Procesar por batches (más pequeños si hay reranking)
        batch_size = 20 if self.use_reranker else 50
        iterator = range(0, len(ofertas), batch_size)
        if tqdm:
            iterator = tqdm(iterator, desc="  Matching", unit="batch")

        for i in iterator:
            batch = ofertas[i:i + batch_size]

            # Preparar textos de ofertas
            textos_ofertas = []
            ids_ofertas = []

            for id_oferta, titulo, descripcion in batch:
                # Texto: título + primeras 300 palabras de descripción
                texto = titulo
                if descripcion:
                    desc_words = descripcion.split()[:300]
                    desc_short = " ".join(desc_words)
                    texto = f"{titulo}. {desc_short}"

                textos_ofertas.append(texto)
                ids_ofertas.append(id_oferta)

            # Generar embeddings de ofertas con BGE-M3
            ofertas_embeddings = self.embedding_model.encode(textos_ofertas, show_progress_bar=False)
            ofertas_embeddings = normalizar_embeddings(ofertas_embeddings)

            # Calcular similaridades con todas las ocupaciones ESCO
            for j, oferta_embedding in enumerate(ofertas_embeddings):
                id_oferta = ids_ofertas[j]
                texto_oferta = textos_ofertas[j]

                # Similaridad coseno: dot product (embeddings ya normalizados)
                similarities = np.dot(esco_embeddings, oferta_embedding)

                # Obtener top-10 candidatos
                top_k = 10
                top_indices = np.argsort(similarities)[-top_k:][::-1]

                candidatos = []
                for idx in top_indices:
                    candidatos.append({
                        'uri': esco_metadata[idx]['uri'],
                        'label': esco_metadata[idx]['label'],
                        'similarity_score': float(similarities[idx])
                    })

                # Re-ranking con ESCO-XLM si está disponible
                rerank_score = None
                if self.use_reranker and self.reranker:
                    try:
                        reranked = self.reranker.rerank(texto_oferta, candidatos, top_k=1)
                        best_match = reranked[0]
                        rerank_score = best_match['rerank_score']
                        self.stats['reranked'] += 1
                    except Exception as e:
                        # Fallback al mejor por similarity
                        best_match = candidatos[0]
                        if len(self.stats['errores']) < 10:
                            self.stats['errores'].append(f"Rerank {id_oferta}: {e}")
                else:
                    best_match = candidatos[0]

                # Guardar resultado
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO ofertas_esco_matching (
                            id_oferta, esco_occupation_uri, esco_occupation_label,
                            occupation_match_score, occupation_match_method,
                            matching_timestamp, matching_version, rerank_score
                        ) VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
                    """, (
                        str(id_oferta),
                        best_match['uri'],
                        best_match['label'],
                        best_match['similarity_score'],
                        'bge-m3+esco-xlm' if rerank_score else 'bge-m3',
                        'hybrid-v1' if rerank_score else 'bge-m3-v1',
                        rerank_score
                    ))

                    self.stats['matches_ocupaciones'] += 1
                except Exception as e:
                    if len(self.stats['errores']) < 10:
                        self.stats['errores'].append(f"Match ocupación {id_oferta}: {e}")

        self.conn.commit()
        self.stats['ofertas_procesadas'] = len(ofertas)
        print(f"  [OK] {self.stats['ofertas_procesadas']:,} ofertas procesadas")
        print(f"  [OK] {self.stats['matches_ocupaciones']:,} matches guardados")
        if self.use_reranker:
            print(f"  [OK] {self.stats['reranked']:,} ofertas re-rankeadas con ESCO-XLM")

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
                            ) VALUES (?, ?, ?, ?, ?, 'esco-xlm')
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
        print("REPORTE FINAL DE MATCHING ESCO (Pipeline Híbrido)")
        print("=" * 70)

        print(f"\n[STATS] ESTADÍSTICAS:")
        print(f"  - Ocupaciones ESCO:           {self.stats['esco_ocupaciones']:,}")
        print(f"  - Skills ESCO:                {self.stats['esco_skills']:,}")
        print(f"  - Ofertas procesadas:         {self.stats['ofertas_procesadas']:,}")
        print(f"  - Matches ocupaciones:        {self.stats['matches_ocupaciones']:,}")
        print(f"  - Ofertas re-rankeadas:       {self.stats['reranked']:,}")
        print(f"  - Matches skills:             {self.stats['matches_skills']:,}")

        if self.stats['errores']:
            print(f"\n[WARNING] ERRORES: {len(self.stats['errores'])}")
            for error in self.stats['errores'][:10]:
                print(f"  - {error}")

        # Consultar estadísticas finales
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT id_oferta) FROM ofertas_esco_matching")
        ofertas_con_match = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(occupation_match_score) FROM ofertas_esco_matching")
        avg_similarity = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(rerank_score) FROM ofertas_esco_matching WHERE rerank_score IS NOT NULL")
        avg_rerank = cursor.fetchone()[0] or 0

        # Distribución de ocupaciones (verificar que no se concentre en una sola)
        cursor.execute("""
            SELECT esco_occupation_label, COUNT(*) as cnt
            FROM ofertas_esco_matching
            GROUP BY esco_occupation_label
            ORDER BY cnt DESC
            LIMIT 10
        """)
        top_ocupaciones = cursor.fetchall()

        print(f"\n[CHART] MÉTRICAS DE CALIDAD:")
        print(f"  - Ofertas con match:          {ofertas_con_match:,}")
        print(f"  - Score similarity promedio:  {avg_similarity:.4f}")
        if avg_rerank:
            print(f"  - Score rerank promedio:      {avg_rerank:.4f}")

        print(f"\n[DISTRIBUTION] TOP 10 OCUPACIONES:")
        for label, cnt in top_ocupaciones:
            pct = cnt / ofertas_con_match * 100 if ofertas_con_match else 0
            print(f"  - {label[:50]:50s} {cnt:5,} ({pct:5.1f}%)")

        print("\n" + "=" * 70)
        print("[OK] PROCESO COMPLETADO")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta proceso completo de matching híbrido"""
        print("\n" + "=" * 70)
        print("MATCHING SEMÁNTICO OFERTAS-ESCO (Pipeline Híbrido BGE-M3 + ESCO-XLM)")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.conectar_db():
            return False

        if not self.cargar_modelos():
            return False

        # Generar embeddings ESCO con BGE-M3
        esco_occ_embeddings, esco_occ_metadata = self.generar_embeddings_ocupaciones()
        if esco_occ_embeddings is None:
            print("[ERROR] Error generando embeddings de ocupaciones")
            return False

        esco_skills_embeddings, esco_skills_metadata = self.generar_embeddings_skills()
        if esco_skills_embeddings is None:
            print("[ERROR] Error generando embeddings de skills")
            return False

        # Matching híbrido
        self.matchear_ofertas_a_ocupaciones(esco_occ_embeddings, esco_occ_metadata)

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
