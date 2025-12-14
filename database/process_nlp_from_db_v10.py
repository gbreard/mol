#!/usr/bin/env python3
"""
NLP Extractor v10.0 - Pipeline Schema v5 Completo (16 Bloques)
==============================================================

VERSION: 10.0.0
FECHA: 2025-12-10
MODELO: Qwen2.5:14b
ISSUE: MOL-62

CAMBIOS v10.0:
  - Schema v5 COMPLETO: 143 columnas en ofertas_nlp
  - Prompt v10 con 16 bloques temáticos
  - Respuesta estructurada por bloques (flatten antes de guardar)
  - Campos críticos para matching ESCO priorizados

ARQUITECTURA DE 3 CAPAS:
========================
CAPA 0 - Regex Determinístico (campos básicos)
CAPA 1 - LLM Restringido (16 bloques temáticos)
CAPA 2 - Verificación Anti-Alucinación (texto_original)

Uso:
    python process_nlp_from_db_v10.py --mode test --limit 5
    python process_nlp_from_db_v10.py --mode production --batch 50
"""

import sys
import sqlite3
import json
import time
import requests
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Agregar paths para imports
scripts_dir = Path(__file__).parent.parent / "02.5_nlp_extraction" / "scripts"
nlp_dir = Path(__file__).parent.parent / "02.5_nlp_extraction"
patterns_dir = scripts_dir / "patterns"
prompts_dir = nlp_dir / "prompts"

sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(nlp_dir))
sys.path.insert(0, str(patterns_dir))
sys.path.insert(0, str(prompts_dir))

# Importar módulos
from patterns.regex_patterns_v4 import extract_all as extract_regex_v4, StructureDetector
from prompts.extraction_prompt_v10 import build_prompt, flatten_response, CAMPOS_DB_MAPPING

# Postprocesador NLP (correcciones validacion humana)
from nlp_postprocessor import NLPPostprocessor


class NLPExtractorV10:
    """
    Extractor NLP v10.0 con Schema v5 Completo (16 Bloques)
    """

    VERSION = "10.0.0"
    EXTRACTION_METHOD = "pipeline_v10_schema_v5"
    OLLAMA_MODEL = "qwen2.5:14b"
    OLLAMA_URL = "http://localhost:11434/api/generate"

    def __init__(self, db_path: str = None, verbose: bool = False):
        if db_path is None:
            db_path = Path(__file__).parent / "bumeran_scraping.db"

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.verbose = verbose

        # Inicializar postprocesador (correcciones validacion humana)
        self.postprocessor = NLPPostprocessor(verbose=verbose)

        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_ms": 0,
            "llm_calls": 0,
            "llm_errors": 0,
            "items_verificados": 0,
            "items_descartados": 0
        }

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    # =========================================================================
    # CAPA 0: REGEX DETERMINÍSTICO
    # =========================================================================

    def _extract_capa0_regex(self, descripcion: str, titulo: str = "", empresa: str = "") -> Dict[str, Any]:
        """CAPA 0: Extracción con regex determinístico"""
        if self.verbose:
            print("[CAPA 0] Ejecutando regex_patterns_v4.extract_all()...")

        resultado = extract_regex_v4(descripcion, titulo, empresa)

        if self.verbose:
            campos_con_valor = sum(1 for v in resultado.values() if v is not None)
            print(f"[CAPA 0] Campos extraídos: {campos_con_valor}")

        return resultado

    # =========================================================================
    # CAPA 1: LLM RESTRINGIDO (16 bloques)
    # =========================================================================

    def _extract_capa1_llm(self, descripcion: str, timeout: int = 240) -> Optional[Dict[str, Any]]:
        """CAPA 1: Extracción con LLM - 16 bloques temáticos"""
        if self.verbose:
            print("[CAPA 1] Llamando a LLM para extracción por bloques...")

        try:
            self.stats["llm_calls"] += 1

            prompt = build_prompt(descripcion)

            if self.verbose:
                print(f"[CAPA 1] Prompt length: {len(prompt):,} chars")

            payload = {
                "model": self.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "num_predict": 8192,  # Más tokens para 16 bloques
                    "num_ctx": 12288,     # Más contexto
                }
            }

            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                print(f"[CAPA 1 ERROR] Status {response.status_code}")
                self.stats["llm_errors"] += 1
                return None

            response_data = response.json()
            llm_output = response_data.get("response", "").strip()

            # Extraer JSON
            json_start = llm_output.find("{")
            json_end = llm_output.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                print("[CAPA 1 ERROR] No se encontró JSON en respuesta")
                self.stats["llm_errors"] += 1
                return None

            json_str = llm_output[json_start:json_end]

            try:
                extracted = json.loads(json_str)
                if self.verbose:
                    bloques = len([k for k in extracted.keys() if isinstance(extracted.get(k), dict)])
                    print(f"[CAPA 1] JSON parseado OK - {bloques} bloques")
                return extracted
            except json.JSONDecodeError as e:
                print(f"[CAPA 1 ERROR] JSON inválido: {e}")
                self.stats["llm_errors"] += 1
                return None

        except requests.exceptions.Timeout:
            print(f"[CAPA 1 ERROR] Timeout después de {timeout}s")
            self.stats["llm_errors"] += 1
            return None
        except requests.exceptions.ConnectionError:
            print("[CAPA 1 ERROR] No se pudo conectar a Ollama")
            self.stats["llm_errors"] += 1
            return None
        except Exception as e:
            print(f"[CAPA 1 ERROR] Error inesperado: {e}")
            self.stats["llm_errors"] += 1
            return None

    # =========================================================================
    # CAPA 2: VERIFICACIÓN ANTI-ALUCINACIÓN
    # =========================================================================

    def _normalizar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        s = unicodedata.normalize("NFKC", texto)
        s = s.lower()
        s = re.sub(r'[\u200b\u00a0\u2060\ufeff]', ' ', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    def _verificar_substring(self, texto_original: str, descripcion: str) -> bool:
        """Verifica que texto_original existe en descripcion"""
        if not texto_original or not descripcion:
            return False

        texto_norm = self._normalizar_texto(texto_original)
        desc_norm = self._normalizar_texto(descripcion)

        return texto_norm in desc_norm

    def _verify_list_items(self, items: List, descripcion: str, campo: str) -> List:
        """Verifica items de una lista contra la descripción"""
        if not isinstance(items, list):
            return []

        verified = []
        for item in items:
            if isinstance(item, dict):
                texto_original = item.get("texto_original", "")
                valor = item.get("valor", "")

                if self._verificar_substring(texto_original, descripcion):
                    self.stats["items_verificados"] += 1
                    verified.append(valor)
                    if self.verbose:
                        print(f"  [OK] {campo}: '{valor}'")
                else:
                    self.stats["items_descartados"] += 1
                    if self.verbose:
                        print(f"  [X] {campo}: '{valor}' - no verificado")
            elif isinstance(item, str):
                # Items simples (días de trabajo, etc.)
                verified.append(item)

        return verified

    def _verify_capa2(self, llm_output: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
        """CAPA 2: Verificación anti-alucinación por bloques"""
        if self.verbose:
            print("[CAPA 2] Verificando items contra descripción...")

        # Flatten la respuesta
        flat = flatten_response(llm_output)

        # Verificar campos lista
        lista_campos = [k for k in flat.keys() if k.endswith('_list')]
        for campo in lista_campos:
            items = flat.get(campo)
            if items:
                verified = self._verify_list_items(items, descripcion, campo)
                flat[campo] = verified if verified else None

        if self.verbose:
            print(f"[CAPA 2] Verificados: {self.stats['items_verificados']}, "
                  f"Descartados: {self.stats['items_descartados']}")

        return flat

    # =========================================================================
    # GUARDAR EN BD
    # =========================================================================

    def _prepare_value_for_db(self, value: Any) -> Any:
        """Prepara un valor para insertar en la BD"""
        if value is None:
            return None
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False) if value else None
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return value

    def _get_valid_columns(self, cursor) -> set:
        """Obtiene las columnas válidas de ofertas_nlp"""
        cursor.execute("PRAGMA table_info(ofertas_nlp)")
        return {row[1] for row in cursor.fetchall()}

    def save_to_ofertas_nlp(self, id_oferta: str, extracted: Dict[str, Any]) -> bool:
        """
        Guarda los datos extraídos en ofertas_nlp

        Args:
            id_oferta: ID de la oferta
            extracted: Dict con todos los campos extraídos

        Returns:
            True si guardó correctamente
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Obtener columnas válidas de la BD
            valid_columns = self._get_valid_columns(cursor)

            # Verificar si existe el registro
            cursor.execute("SELECT 1 FROM ofertas_nlp WHERE id_oferta = ?", (id_oferta,))
            exists = cursor.fetchone() is not None

            # Preparar datos
            data = {
                "id_oferta": id_oferta,
                "nlp_version": self.VERSION,
                "nlp_extraction_timestamp": datetime.now().isoformat(),
                "pasa_a_matching": 1,
            }

            # Mapeo de campos regex a columnas BD
            REGEX_TO_DB = {
                "licencia_conducir_requerida": "licencia_conducir",
                "licencia_conducir_categoria": "tipo_licencia",
                "edad_min": "requisito_edad_min",
                "edad_max": "requisito_edad_max",
            }

            # Agregar campos extraídos (solo si columna existe en BD)
            for campo, valor in extracted.items():
                # Aplicar mapeo si existe
                db_campo = REGEX_TO_DB.get(campo, campo)
                if db_campo in valid_columns:
                    data[db_campo] = self._prepare_value_for_db(valor)
                elif self.verbose:
                    print(f"  [SKIP] Campo '{campo}' no existe en BD")

            # Construir query
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]

            if exists:
                # UPDATE
                set_clause = ", ".join([f"{col} = ?" for col in columns if col != "id_oferta"])
                query = f"UPDATE ofertas_nlp SET {set_clause} WHERE id_oferta = ?"
                values = [data[col] for col in columns if col != "id_oferta"] + [id_oferta]
            else:
                # INSERT
                query = f"INSERT INTO ofertas_nlp ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                values = [data[col] for col in columns]

            cursor.execute(query, values)
            conn.commit()

            if self.verbose:
                print(f"[DB] {'Actualizado' if exists else 'Insertado'}: {id_oferta}")

            return True

        except Exception as e:
            print(f"[DB ERROR] {id_oferta}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # =========================================================================
    # PIPELINE PRINCIPAL
    # =========================================================================

    def process_oferta(self, id_oferta: str, descripcion: str,
                      titulo: str = "", empresa: str = "",
                      ubicacion: str = "") -> Optional[Dict[str, Any]]:
        """
        Procesa una oferta con el pipeline de 3 capas + postprocesamiento

        Pipeline:
          CAPA 0: Regex deterministico
          CAPA 1: LLM (16 bloques)
          CAPA 2: Verificacion anti-alucinacion
          CAPA 3: Postprocesamiento (validacion humana)
        """
        start_time = time.time()

        try:
            # Reset contadores
            self.stats["items_verificados"] = 0
            self.stats["items_descartados"] = 0

            # PREPROCESO: Extraer campos estructurados del scraping
            row_data = {"ubicacion": ubicacion, "empresa": empresa, "titulo": titulo}
            pre_data = self.postprocessor.preprocess(row_data)
            if self.verbose and pre_data:
                print(f"[PREPROC] Campos extraidos: {list(pre_data.keys())}")

            # CAPA 0: REGEX
            regex_data = self._extract_capa0_regex(descripcion, titulo, empresa)

            # CAPA 1: LLM
            llm_data = self._extract_capa1_llm(descripcion)

            # CAPA 2: VERIFICACIÓN
            verified = {}
            if llm_data:
                verified = self._verify_capa2(llm_data, descripcion)

            # MERGE: regex tiene prioridad
            final_data = {}
            final_data.update(verified)

            # Sobrescribir con datos de regex (más precisos)
            for campo, valor in regex_data.items():
                if valor is not None:
                    final_data[campo] = valor

            # Agregar campos preprocesados (solo si no existen)
            for campo, valor in pre_data.items():
                if final_data.get(campo) is None and valor is not None:
                    final_data[campo] = valor

            # CAPA 3: POSTPROCESAMIENTO (correcciones validacion humana)
            # Extraer skills_regex de Capa 0 para fusionar con LLM
            skills_regex = {
                "skills_tecnicas_regex": regex_data.get("skills_tecnicas_regex", []),
                "soft_skills_regex": regex_data.get("soft_skills_regex", []),
            }
            final_data = self.postprocessor.postprocess(final_data, descripcion, skills_regex)
            pp_stats = self.postprocessor.get_stats()
            if self.verbose:
                print(f"[POSTPROC] {pp_stats}")

            # Calcular métricas
            processing_time_ms = int((time.time() - start_time) * 1000)
            total_items = self.stats["items_verificados"] + self.stats["items_descartados"]
            confidence = self.stats["items_verificados"] / total_items if total_items > 0 else 0.5

            # Guardar en BD
            self.save_to_ofertas_nlp(id_oferta, final_data)

            self.stats["total_success"] += 1
            self.stats["total_time_ms"] += processing_time_ms

            return {
                "id_oferta": id_oferta,
                "nlp_version": self.VERSION,
                "extracted_data": final_data,
                "confidence_score": round(confidence, 2),
                "processing_time_ms": processing_time_ms,
                "items_verificados": self.stats["items_verificados"],
                "items_descartados": self.stats["items_descartados"],
            }

        except Exception as e:
            print(f"[ERROR] {id_oferta}: {e}")
            import traceback
            traceback.print_exc()
            self.stats["total_errors"] += 1
            return None

    def process_batch(self, limit: int = 100, ids_especificos: List[str] = None) -> Dict[str, Any]:
        """Procesa un batch de ofertas"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if ids_especificos:
            placeholders = ",".join("?" * len(ids_especificos))
            query = f"""
                SELECT o.id_oferta, o.descripcion, o.titulo, o.empresa, o.localizacion
                FROM ofertas o
                WHERE o.id_oferta IN ({placeholders})
                  AND o.descripcion IS NOT NULL
                  AND LENGTH(o.descripcion) > 100
            """
            cursor.execute(query, ids_especificos)
        else:
            query = f"""
                SELECT o.id_oferta, o.descripcion, o.titulo, o.empresa, o.localizacion
                FROM ofertas o
                WHERE o.descripcion IS NOT NULL
                  AND LENGTH(o.descripcion) > 100
                ORDER BY o.fecha_publicacion_datetime DESC
                LIMIT {limit}
            """
            cursor.execute(query)

        ofertas = cursor.fetchall()
        conn.close()

        total = len(ofertas)
        print(f"\n[BATCH] Procesando {total} ofertas con NLP v{self.VERSION}")
        print(f"[BATCH] Schema v5 completo: 143 columnas")
        print()

        for i, (id_oferta, descripcion, titulo, empresa, localizacion) in enumerate(ofertas, 1):
            print(f"[{i}/{total}] {id_oferta}...", end=" ")

            result = self.process_oferta(
                id_oferta, descripcion,
                titulo or "", empresa or "", localizacion or ""
            )

            if result:
                print(f"OK (C:{result['confidence_score']:.2f}, "
                      f"V:{result['items_verificados']}/D:{result['items_descartados']}, "
                      f"T:{result['processing_time_ms']}ms)")
            else:
                print("ERROR")

            self.stats["total_processed"] += 1
            time.sleep(0.3)

        # Estadísticas
        avg_time = self.stats["total_time_ms"] / max(1, self.stats["total_success"])
        success_rate = (self.stats["total_success"] / max(1, self.stats["total_processed"])) * 100

        print()
        print("=" * 60)
        print("ESTADÍSTICAS")
        print("=" * 60)
        print(f"Total:         {self.stats['total_processed']}")
        print(f"Éxitos:        {self.stats['total_success']} ({success_rate:.1f}%)")
        print(f"Errores:       {self.stats['total_errors']}")
        print(f"Tiempo prom:   {avg_time:.0f}ms")
        print("=" * 60)

        return self.stats


def check_ollama_status():
    """Verifica que Ollama esté corriendo"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"[OK] Ollama corriendo. Modelos: {', '.join(model_names[:3])}")
            return "qwen2.5:14b" in model_names
        return False
    except:
        print("[ERROR] Ollama no disponible")
        return False


def main():
    parser = argparse.ArgumentParser(description="NLP Extractor v10.0 - Schema v5 Completo")
    parser.add_argument("--mode", choices=["test", "production"], default="test")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--ids", type=str, nargs="+")
    parser.add_argument("--db", type=str)
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    print("=" * 60)
    print("NLP EXTRACTOR v10.0 - SCHEMA v5 COMPLETO")
    print("=" * 60)
    print(f"Modo: {args.mode.upper()}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    if not check_ollama_status():
        print("\n[ERROR] Ollama no disponible o modelo qwen2.5:14b no encontrado")
        return 1

    try:
        extractor = NLPExtractorV10(db_path=args.db, verbose=args.verbose)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    if args.mode == "test":
        test_ids = args.ids or ["2163782"]
        print(f"[TEST] Procesando {len(test_ids)} ofertas: {test_ids}")
        extractor.process_batch(ids_especificos=test_ids)
    else:
        print(f"[PRODUCTION] Procesando {args.limit} ofertas")
        extractor.process_batch(limit=args.limit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
