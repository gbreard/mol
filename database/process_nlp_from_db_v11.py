#!/usr/bin/env python3
"""
NLP Extractor v11.2 - Schema Lite + Postprocessor + Skills Implicitas
=====================================================================

VERSION: 11.2.0
FECHA: 2026-01-05
MODELO: Qwen2.5:14b (LLM) + BGE-M3 (skills implicitas)

MEJORA vs v11.1: Integra NLPPostprocessor - usa TODOS los JSONs de config/
MEJORA vs v10: 240s -> ~25s por oferta (10x mas rapido)
ESTRATEGIA: 20 campos normalizables + skills implicitas via embeddings

CAMPOS (20):
  GRUPO 1 - NLP Base (15):
  - titulo_ocupacion, provincia, localidad, sector_empresa
  - tareas_explicitas
  - skills_tecnicas_list, soft_skills_list, tecnologias_list, herramientas_list
  - experiencia_min_anios, experiencia_max_anios
  - nivel_educativo, titulo_requerido
  - requerimiento_edad (0-5), requerimiento_sexo (0-2)

  GRUPO 2 - Matching ESCO (5):
  - area_funcional, nivel_seniority, tiene_gente_cargo, mision_rol, tipo_oferta

ARQUITECTURA:
  CAPA 0: Regex (salarios, jornada, modalidad)
  CAPA 1: LLM (20 campos)
  CAPA 2: Postprocessor (config/nlp_*.json - inferencia, validacion, normalizacion)
  CAPA 3: Skills implicitas (BGE-M3 + ESCO embeddings)

Uso:
    python process_nlp_from_db_v11.py --limit 10
    python process_nlp_from_db_v11.py --benchmark --limit 5
    python process_nlp_from_db_v11.py --ids 1234,5678
    python process_nlp_from_db_v11.py --no-implicit-skills  # Sin skills implicitas
"""

import sys
import sqlite3
import json
import time
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Importar extractor de skills implícitas
from skills_implicit_extractor import SkillsImplicitExtractor

# Importar postprocessor (aplica reglas de config/nlp_*.json)
from nlp_postprocessor import NLPPostprocessor

# Agregar paths para imports
# Prompts y patterns están en database/ (mismo directorio)
database_dir = Path(__file__).parent
sys.path.insert(0, str(database_dir))

# Importar prompt lite v1.1 (20 campos)
from prompts.extraction_prompt_lite_v1 import (
    get_prompt_lite,
    SCHEMA_LITE,
    VALID_EDAD,
    VALID_SEXO,
    VALID_EDUCACION,
    VALID_AREA_FUNCIONAL,
    VALID_SENIORITY,
    VALID_TIPO_OFERTA
)

# Importar regex patterns para CAPA 0 (salarios, jornada, modalidad)
from patterns.regex_patterns_v4 import extract_all as extract_regex_v4

# Limpieza de titulos
from limpiar_titulos import limpiar_titulo


class NLPExtractorV11:
    """
    Extractor NLP v11.0 - Schema Lite (15 campos normalizables)
    Optimizado para velocidad: 18s vs 240s (v10)
    """

    VERSION = "11.3.0"
    NLP_VERSION_TAG = "11.3.0"
    EXTRACTION_METHOD = "pipeline_v11_schema_lite_implicit_skills"
    # Modelo optimizado: 7b es suficiente para extracción JSON (3x más rápido que 14b)
    OLLAMA_MODEL = "qwen2.5:7b"
    OLLAMA_URL = "http://localhost:11434/api/generate"

    # Cache de configs (se cargan una sola vez)
    _config_cache = None

    def __init__(self, db_path: str = None, verbose: bool = False, enable_implicit_skills: bool = True):
        if db_path is None:
            db_path = Path(__file__).parent / "bumeran_scraping.db"

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.verbose = verbose
        self.enable_implicit_skills = enable_implicit_skills

        # Cargar configs una sola vez
        if NLPExtractorV11._config_cache is None:
            self._load_configs()

        # Inicializar extractor de skills implícitas (si está habilitado)
        self.skills_extractor = None
        if enable_implicit_skills:
            try:
                self.skills_extractor = SkillsImplicitExtractor(verbose=verbose)
                if not self.skills_extractor.is_ready():
                    print("[WARN] Skills implícitas deshabilitadas: embeddings no disponibles")
                    self.skills_extractor = None
                elif verbose:
                    print("[SKILLS] Extractor de skills implícitas inicializado")
            except Exception as e:
                print(f"[WARN] Skills implícitas deshabilitadas: {e}")
                self.skills_extractor = None

        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_ms": 0,
            "llm_calls": 0,
            "llm_time_ms": 0,
            "skills_implicitas_extraidas": 0,
        }

        # Inicializar postprocessor (aplica reglas de config/nlp_*.json)
        self.postprocessor = NLPPostprocessor(verbose=verbose)

    def _load_configs(self):
        """Carga configs una sola vez (cache en clase)"""
        config_dir = Path(__file__).parent.parent / "config"

        NLPExtractorV11._config_cache = {
            "schema_lite": self._load_json(config_dir / "nlp_schema_lite.json"),
            "normalization": self._load_json(config_dir / "nlp_normalization.json"),
            "validation": self._load_json(config_dir / "nlp_validation.json"),
        }

        if self.verbose:
            print(f"[CONFIG] Configs cargados en cache")

    def _load_json(self, path: Path) -> dict:
        """Carga un archivo JSON"""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    # =========================================================================
    # CAPA 0: REGEX (solo salarios, jornada, modalidad)
    # =========================================================================

    def _extract_capa0_regex(self, descripcion: str, titulo: str = "") -> Dict[str, Any]:
        """CAPA 0: Extraccion con regex (campos no-LLM)"""
        resultado = extract_regex_v4(descripcion, titulo, "")

        # Solo conservar campos que no van al LLM
        campos_regex = {
            "salario_min": resultado.get("salario_min"),
            "salario_max": resultado.get("salario_max"),
            "moneda": resultado.get("moneda"),
            "jornada_laboral": resultado.get("jornada_laboral"),
            "modalidad": resultado.get("modalidad"),
        }

        return {k: v for k, v in campos_regex.items() if v is not None}

    # =========================================================================
    # CAPA 1: LLM LITE (15 campos)
    # =========================================================================

    def _extract_capa1_llm(self, titulo: str, empresa: str,
                           ubicacion: str, descripcion: str,
                           timeout: int = 60) -> Optional[Dict[str, Any]]:
        """CAPA 1: Extraccion con LLM - 15 campos"""
        try:
            self.stats["llm_calls"] += 1
            llm_start = time.time()

            prompt = get_prompt_lite(titulo, empresa, ubicacion, descripcion)

            if self.verbose:
                print(f"[LLM] Prompt: {len(prompt):,} chars")

            payload = {
                "model": self.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "num_predict": 1024,  # Mucho menos tokens (15 campos)
                    "num_ctx": 4096,      # Menos contexto
                }
            }

            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()

            llm_time = int((time.time() - llm_start) * 1000)
            self.stats["llm_time_ms"] += llm_time

            result = response.json()
            text = result.get("response", "")

            if self.verbose:
                print(f"[LLM] Response: {len(text)} chars, {llm_time}ms")

            # Parsear JSON
            return self._parse_llm_response(text)

        except requests.exceptions.Timeout:
            print(f"[LLM] TIMEOUT despues de {timeout}s")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"[LLM] No se puede conectar a Ollama: {e}")
            return None
        except Exception as e:
            print(f"[LLM ERROR] {type(e).__name__}: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return None

    def _parse_llm_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parsea la respuesta del LLM"""
        if not text or not text.strip():
            if self.verbose:
                print("[PARSE] Respuesta vacia del LLM")
            return None

        try:
            # Limpiar respuesta
            text = text.strip()

            # Si tiene format: json, Ollama ya devuelve JSON limpio
            if text.startswith("{"):
                data = json.loads(text)
                return self._validate_response(data)

            # Buscar JSON en markdown code blocks
            code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if code_match:
                json_text = code_match.group(1).strip()
                data = json.loads(json_text)
                return self._validate_response(data)

            # Buscar JSON en la respuesta
            match = re.search(r'\{[\s\S]*\}', text)
            if not match:
                if self.verbose:
                    print(f"[PARSE] No se encontro JSON en respuesta: {text[:100]}...")
                return None

            data = json.loads(match.group())
            return self._validate_response(data)

        except json.JSONDecodeError as e:
            print(f"[PARSE ERROR] {e}")
            if self.verbose:
                print(f"[PARSE] Texto problematico: {text[:200]}...")
            return None

    def _validate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y normaliza la respuesta del LLM"""
        validated = {}

        for campo, tipo in SCHEMA_LITE.items():
            valor = data.get(campo)

            if valor is None:
                validated[campo] = None
                continue

            # Validar tipo
            if tipo == str:
                validated[campo] = str(valor) if valor else None
            elif tipo == int:
                try:
                    validated[campo] = int(valor) if valor is not None else None
                except (ValueError, TypeError):
                    validated[campo] = None
            elif tipo == list:
                if isinstance(valor, list):
                    validated[campo] = [str(v) for v in valor if v]
                elif isinstance(valor, str):
                    validated[campo] = [v.strip() for v in valor.split(",") if v.strip()]
                else:
                    validated[campo] = []

        # Validar campos categoricos
        if validated.get("requerimiento_edad") not in VALID_EDAD:
            validated["requerimiento_edad"] = 0
        if validated.get("requerimiento_sexo") not in VALID_SEXO:
            validated["requerimiento_sexo"] = 0
        if validated.get("nivel_educativo"):
            if validated["nivel_educativo"].lower() not in VALID_EDUCACION:
                validated["nivel_educativo"] = None
            else:
                validated["nivel_educativo"] = validated["nivel_educativo"].lower()

        # Validar experiencia (max 15, como en config)
        config = NLPExtractorV11._config_cache.get("validation", {})
        exp_config = config.get("validacion_rangos", {}).get("experiencia_min_anios", {})
        max_exp = exp_config.get("max", 15)

        if validated.get("experiencia_min_anios"):
            if validated["experiencia_min_anios"] > max_exp:
                validated["experiencia_min_anios"] = None
        if validated.get("experiencia_max_anios"):
            if validated["experiencia_max_anios"] > 20:
                validated["experiencia_max_anios"] = None

        return validated

    # =========================================================================
    # PIPELINE PRINCIPAL
    # =========================================================================

    def process_oferta(self, id_oferta: str, descripcion: str,
                       titulo: str = "", empresa: str = "",
                       ubicacion: str = "", fecha_publicacion: str = None) -> Optional[Dict[str, Any]]:
        """
        Procesa una oferta con pipeline lite

        Pipeline:
          CAPA 0: Regex (salarios, jornada, modalidad)
          CAPA 1: LLM (15 campos)
          Postprocess: Validacion minima
        """
        start_time = time.time()

        try:
            # CAPA 0: REGEX
            regex_data = self._extract_capa0_regex(descripcion, titulo)

            # CAPA 1: LLM LITE
            llm_data = self._extract_capa1_llm(titulo, empresa, ubicacion, descripcion)

            if llm_data is None:
                print(f"[WARN] {id_oferta}: LLM no retorno datos")
                llm_data = {}

            # MERGE
            final_data = {}
            final_data.update(llm_data)
            final_data.update(regex_data)  # regex tiene prioridad

            # Titulo limpio
            if titulo:
                final_data["titulo_limpio"] = limpiar_titulo(titulo)

            # POSTPROCESSOR: Aplica reglas de config/nlp_*.json
            # - Preprocesa ubicación (parsing provincia/localidad)
            # - Infiere area_funcional, modalidad, seniority desde título
            # - Valida campos categóricos
            # - Aplica exclusiones configuradas
            pre_data = self.postprocessor.preprocess({
                'localizacion': ubicacion,
                'titulo': titulo
            })
            # Merge preprocesamiento (provincia, localidad parseados)
            for key in ['provincia', 'localidad']:
                if pre_data.get(key) and not final_data.get(key):
                    final_data[key] = pre_data[key]

            # Postprocesar (inferencia + validación)
            final_data = self.postprocessor.postprocess(final_data, descripcion)

            # SKILLS IMPLÍCITAS (desde tareas)
            if self.skills_extractor and final_data.get("tareas_explicitas"):
                tareas = final_data["tareas_explicitas"]
                if isinstance(tareas, list):
                    tareas = "; ".join(str(t) for t in tareas)

                skills_declaradas = final_data.get("skills_tecnicas_list", [])
                if isinstance(skills_declaradas, str):
                    skills_declaradas = [s.strip() for s in skills_declaradas.split(",") if s.strip()]

                try:
                    skills_all, skills_implicitas = self.skills_extractor.get_skills_for_offer(
                        skills_declaradas=skills_declaradas,
                        tareas_explicitas=tareas,
                        merge=True
                    )

                    if skills_implicitas:
                        # Agregar skills implícitas al campo skills_tecnicas_list
                        final_data["skills_tecnicas_list"] = skills_all
                        # Guardar detalle de skills implícitas (opcional)
                        final_data["skills_implicitas_count"] = len(skills_implicitas)
                        self.stats["skills_implicitas_extraidas"] += len(skills_implicitas)

                        if self.verbose:
                            print(f"[SKILLS] +{len(skills_implicitas)} implícitas: {[s['skill_esco'][:30] for s in skills_implicitas[:3]]}")
                except Exception as e:
                    if self.verbose:
                        print(f"[WARN] Skills implícitas error: {e}")

            # Metricas
            processing_time_ms = int((time.time() - start_time) * 1000)

            self.stats["total_success"] += 1
            self.stats["total_time_ms"] += processing_time_ms

            return {
                "id_oferta": id_oferta,
                "fecha_publicacion": fecha_publicacion,
                "nlp_version": self.NLP_VERSION_TAG,
                "extracted_data": final_data,
                "processing_time_ms": processing_time_ms,
                "llm_time_ms": self.stats["llm_time_ms"],
            }

        except Exception as e:
            print(f"[ERROR] {id_oferta}: {e}")
            import traceback
            traceback.print_exc()
            self.stats["total_errors"] += 1
            return None

    def save_to_db(self, id_oferta: str, extracted: Dict[str, Any],
                   fecha_publicacion: str = None) -> bool:
        """Guarda en ofertas_nlp (campos lite)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Verificar si existe
            cursor.execute("SELECT 1 FROM ofertas_nlp WHERE id_oferta = ?", (id_oferta,))
            exists = cursor.fetchone() is not None

            # Preparar datos
            data = {
                "id_oferta": id_oferta,
                "nlp_version": self.NLP_VERSION_TAG,
                "nlp_extraction_timestamp": datetime.now().isoformat(),
                "fecha_publicacion": fecha_publicacion,
            }

            # Mapeo de campos lite a columnas BD
            LITE_TO_DB = {
                "titulo_ocupacion": "titulo_limpio",  # Usar titulo_limpio existente
                "titulo_limpio": "titulo_limpio",
            }

            # Agregar campos extraidos
            for campo, valor in extracted.items():
                db_campo = LITE_TO_DB.get(campo, campo)
                if isinstance(valor, list):
                    data[db_campo] = "; ".join(str(v) for v in valor) if valor else None
                else:
                    data[db_campo] = valor

            # Obtener columnas validas
            cursor.execute("PRAGMA table_info(ofertas_nlp)")
            valid_columns = {row[1] for row in cursor.fetchall()}

            # Filtrar solo columnas existentes
            data = {k: v for k, v in data.items() if k in valid_columns}

            # Construir query
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]

            if exists:
                set_clause = ", ".join([f"{col} = ?" for col in columns if col != "id_oferta"])
                query = f"UPDATE ofertas_nlp SET {set_clause} WHERE id_oferta = ?"
                values = [data[col] for col in columns if col != "id_oferta"] + [id_oferta]
            else:
                query = f"INSERT INTO ofertas_nlp ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                values = [data[col] for col in columns]

            cursor.execute(query, values)
            conn.commit()

            if self.verbose:
                print(f"[DB] {'Updated' if exists else 'Inserted'}: {id_oferta}")

            return True

        except Exception as e:
            print(f"[DB ERROR] {id_oferta}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def process_batch(self, limit: int = 10, ids_especificos: List[str] = None,
                      save_to_db: bool = True) -> Dict[str, Any]:
        """Procesa un batch de ofertas"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if ids_especificos:
            # IDs específicos: procesar aunque ya tengan NLP
            placeholders = ",".join("?" * len(ids_especificos))
            query = f"""
                SELECT o.id_oferta, o.descripcion, o.titulo, o.empresa, o.localizacion,
                       o.fecha_publicacion_datetime
                FROM ofertas o
                WHERE o.id_oferta IN ({placeholders})
                  AND o.descripcion IS NOT NULL
                  AND LENGTH(o.descripcion) > 100
            """
            cursor.execute(query, ids_especificos)
        else:
            # Solo ofertas SIN NLP (no reprocesar las existentes)
            query = f"""
                SELECT o.id_oferta, o.descripcion, o.titulo, o.empresa, o.localizacion,
                       o.fecha_publicacion_datetime
                FROM ofertas o
                LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
                WHERE o.descripcion IS NOT NULL
                  AND LENGTH(o.descripcion) > 100
                  AND n.id_oferta IS NULL
                ORDER BY o.fecha_publicacion_datetime DESC
                LIMIT {limit}
            """
            cursor.execute(query)

        ofertas = cursor.fetchall()
        conn.close()

        total = len(ofertas)
        print(f"\n{'='*60}")
        print(f"NLP LITE v{self.VERSION}")
        print(f"{'='*60}")
        print(f"Ofertas a procesar: {total}")
        print(f"Campos: 15 (normalizables)")
        print()

        results = []
        times = []

        for i, (id_oferta, descripcion, titulo, empresa, localizacion, fecha_pub) in enumerate(ofertas, 1):
            print(f"[{i}/{total}] {id_oferta}...", end=" ", flush=True)

            result = self.process_oferta(
                id_oferta=str(id_oferta),
                descripcion=descripcion or "",
                titulo=titulo or "",
                empresa=empresa or "",
                ubicacion=localizacion or "",
                fecha_publicacion=fecha_pub
            )

            if result:
                times.append(result["processing_time_ms"])
                print(f"OK ({result['processing_time_ms']}ms)")

                if save_to_db:
                    self.save_to_db(id_oferta, result["extracted_data"], fecha_pub)

                results.append(result)
            else:
                print("ERROR")

            self.stats["total_processed"] += 1

        # Resumen
        print()
        print("=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"  Procesados: {self.stats['total_processed']}")
        print(f"  Exitosos: {self.stats['total_success']}")
        print(f"  Errores: {self.stats['total_errors']}")

        if times:
            avg_time = sum(times) / len(times)
            print(f"  Tiempo promedio: {avg_time:.0f}ms ({avg_time/1000:.1f}s)")
            print(f"  Tiempo total: {sum(times)/1000:.1f}s")
            print(f"  Tiempo LLM total: {self.stats['llm_time_ms']/1000:.1f}s")

        return {
            "total": total,
            "success": self.stats["total_success"],
            "errors": self.stats["total_errors"],
            "avg_time_ms": sum(times) / len(times) if times else 0,
            "results": results,
        }


def main():
    parser = argparse.ArgumentParser(description="NLP Extractor LITE - Solo campos normalizables")
    parser.add_argument("--limit", type=int, default=10, help="Numero de ofertas a procesar")
    parser.add_argument("--ids", type=str, help="IDs especificos separados por coma")
    parser.add_argument("--benchmark", action="store_true", help="Modo benchmark (no guarda en BD)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar detalles")

    args = parser.parse_args()

    extractor = NLPExtractorV11(verbose=args.verbose)

    ids = None
    if args.ids:
        ids = [id.strip() for id in args.ids.split(",")]

    save_to_db = not args.benchmark

    if args.benchmark:
        print("[BENCHMARK MODE] No se guardaran cambios en BD")

    extractor.process_batch(
        limit=args.limit,
        ids_especificos=ids,
        save_to_db=save_to_db
    )


if __name__ == "__main__":
    main()
