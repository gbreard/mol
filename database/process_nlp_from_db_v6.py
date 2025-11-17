#!/usr/bin/env python3
"""
NLP Extractor v6.0 - Hybrid RAG System (24 campos)
===================================================

Sistema híbrido de extracción que combina:
- Regex v3.7 (baseline)
- RAG Context (ESCO + ejemplos + stats)
- Ollama LLM (llama3.1:8b)
- Post-validación

NOVEDAD v6.0: Agregados 6 campos nuevos (24 totales)
- experiencia_cargo_previo
- tecnologias_stack_list
- sector_industria
- nivel_seniority
- modalidad_contratacion
- disponibilidad_viajes

Uso:
    python process_nlp_from_db_v6.py --mode test --limit 10
    python process_nlp_from_db_v6.py --mode production --batch 100
"""

import sys
import sqlite3
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import argparse

# Agregar paths para imports
scripts_dir = Path(__file__).parent.parent / "02.5_nlp_extraction" / "scripts"
nlp_dir = Path(__file__).parent.parent / "02.5_nlp_extraction"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(nlp_dir))

from extractors.bumeran_extractor import BumeranExtractor
from rag.context_builder import RAGContextBuilder
from prompts.extraction_prompt_v6 import generate_extraction_prompt_v6


class NLPExtractorV6:
    """Extractor híbrido NLP v6.0 con RAG + LLM + Inferencia Contextual (24 campos)"""

    VERSION = "6.0.0"
    EXTRACTION_METHOD = "hybrid_rag_llm"
    OLLAMA_MODEL = "llama3.1:8b"
    OLLAMA_URL = "http://localhost:11434/api/generate"

    def __init__(self, db_path: str = None, verbose: bool = False):
        """
        Args:
            db_path: Path a la base de datos SQLite
            verbose: Si True, imprime información de debug
        """
        if db_path is None:
            db_path = Path(__file__).parent / "bumeran_scraping.db"

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.verbose = verbose

        # Inicializar RAG context builder
        self.rag_builder = RAGContextBuilder(str(self.db_path))

        # Inicializar regex extractor (baseline)
        self.regex_extractor = BumeranExtractor(version="3.7.0")

        # Cache para contexto RAG (regenerar cada hora)
        self._rag_context_cache = None
        self._rag_context_timestamp = None

        # Estadísticas de procesamiento
        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_ms": 0,
            "llm_calls": 0,
            "llm_errors": 0
        }

    def _get_connection(self):
        """Retorna conexión a la base de datos"""
        return sqlite3.connect(self.db_path)

    def _get_rag_context(self, force_regenerate: bool = False) -> str:
        """
        Obtiene contexto RAG (con cache de 1 hora)

        Args:
            force_regenerate: Forzar regeneración del contexto

        Returns:
            String con contexto RAG completo
        """
        now = time.time()

        # Verificar si necesitamos regenerar
        if (force_regenerate or
            self._rag_context_cache is None or
            self._rag_context_timestamp is None or
            (now - self._rag_context_timestamp) > 3600):  # 1 hora

            print("[RAG] Generando contexto RAG...")
            self._rag_context_cache = self.rag_builder.build_context(
                include_skills=True,
                include_examples=True,
                include_salaries=True,
                include_education=True,
                max_skills=500,  # Limitar a 500 skills para no saturar el contexto
                max_examples=10
            )
            self._rag_context_timestamp = now
            print(f"[RAG] Contexto generado: {len(self._rag_context_cache):,} caracteres")

        return self._rag_context_cache

    def _call_ollama_llm(self, prompt: str, timeout: int = 120) -> Optional[Dict[str, Any]]:
        """
        Llama a Ollama LLM local

        Args:
            prompt: Prompt completo para el LLM
            timeout: Timeout en segundos

        Returns:
            Dict con respuesta parseada o None si error
        """
        try:
            self.stats["llm_calls"] += 1

            # Debug: Mostrar longitud del prompt
            prompt_tokens_approx = len(prompt) / 4  # Aproximación: 1 token ≈ 4 caracteres
            if self.verbose:
                print(f"[DEBUG] Prompt length: {len(prompt):,} chars (~{prompt_tokens_approx:,.0f} tokens)")

            payload = {
                "model": self.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Baja temperatura para respuestas consistentes
                    "num_predict": 2048,  # Suficiente para JSON completo (~500 tokens típico)
                    "num_ctx": 8192,  # Ventana de contexto (para prompts largos con RAG)
                }
            }

            response = requests.post(
                self.OLLAMA_URL,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                print(f"[LLM ERROR] Status {response.status_code}: {response.text[:200]}")
                self.stats["llm_errors"] += 1
                return None

            # Parsear respuesta
            response_data = response.json()
            llm_output = response_data.get("response", "").strip()

            # Intentar parsear JSON desde la respuesta
            # El LLM puede devolver: ```json {...} ``` o directamente {...}
            json_start = llm_output.find("{")
            json_end = llm_output.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                print(f"[LLM ERROR] No se encontró JSON en respuesta")
                print(f"Respuesta completa: {llm_output[:500]}")
                self.stats["llm_errors"] += 1
                return None

            json_str = llm_output[json_start:json_end]

            # Intentar parsear JSON con múltiples estrategias
            extracted_data = self._parse_json_robust(json_str)

            if extracted_data is None:
                self.stats["llm_errors"] += 1
                return None

            return extracted_data

        except requests.exceptions.Timeout:
            print(f"[LLM ERROR] Timeout después de {timeout}s")
            self.stats["llm_errors"] += 1
            return None
        except requests.exceptions.ConnectionError:
            print(f"[LLM ERROR] No se pudo conectar a Ollama. ¿Está corriendo?")
            self.stats["llm_errors"] += 1
            return None
        except Exception as e:
            print(f"[LLM ERROR] Error inesperado: {e}")
            self.stats["llm_errors"] += 1
            return None

    def _parse_json_robust(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        Parsea JSON con múltiples estrategias de corrección automática

        Args:
            json_str: String JSON potencialmente mal formado

        Returns:
            Dict con datos parseados o None si falla
        """
        import re

        # Estrategia 1: Intentar parsing directo
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Estrategia 1A: Corregir comillas simples EXTERNAS en campos array
        # Patrón común del LLM: "field": '["item"]' → "field": "[\"item\"]"
        try:
            corrected = re.sub(
                r'("(?:skills_tecnicas_list|soft_skills_list|certificaciones_list|beneficios_list|requisitos_excluyentes_list|requisitos_deseables_list)"\s*:\s*)\'(\[.*?\])\'',
                lambda m: m.group(1) + '"' + m.group(2).replace('"', '\\"') + '"',
                json_str
            )
            return json.loads(corrected)
        except json.JSONDecodeError:
            pass

        # Estrategia 2: Corregir comillas sin escapar en arrays JSON string
        # Patrón: "field": "[...  ]"  donde hay comillas sin escapar dentro
        try:
            # Buscar patrones como "field": "[...]"
            corrected = re.sub(
                r'("(?:skills_tecnicas_list|soft_skills_list|certificaciones_list|beneficios_list|requisitos_excluyentes_list|requisitos_deseables_list)"\s*:\s*")(\[.*?\])(")',
                lambda m: m.group(1) + m.group(2).replace('"', '\\"') + m.group(3),
                json_str
            )

            return json.loads(corrected)
        except json.JSONDecodeError:
            pass

        # Estrategia 3: Remover trailing commas (común en respuestas LLM)
        try:
            corrected = re.sub(r',(\s*[}\]])', r'\1', json_str)
            return json.loads(corrected)
        except json.JSONDecodeError:
            pass

        # Estrategia 4: Corregir comillas simples por dobles (global)
        try:
            corrected = json_str.replace("'", '"')
            return json.loads(corrected)
        except json.JSONDecodeError:
            pass

        # Estrategia 5: Corregir "valor1" o "valor2" → "valor1" (elegir primero)
        # Patrón común: "carrera_especifica": "Ingeniería Mecánica" o "Ingeniería Automotriz"
        try:
            corrected = re.sub(
                r':\s*"([^"]+)"\s+o\s+"[^"]+"',  # Captura: ": "valor1" o "valor2"
                r': "\1"',  # Reemplaza: ": "valor1"
                json_str
            )
            return json.loads(corrected)
        except json.JSONDecodeError:
            pass

        # Estrategia 6: Completar JSON truncado (fallback robusto)
        # Si el JSON termina abruptamente (ej: "field": sin valor o sin cierre)
        try:
            # Detectar si termina con "field": (falta valor)
            if re.search(r'"[^"]+"\s*:\s*$', json_str.strip()):
                json_str = json_str.strip() + ' null'

            # Detectar si termina con "field": value (falta cierre)
            # O si simplemente falta el cierre
            if not json_str.rstrip().endswith('}'):
                # Contar llaves abiertas vs cerradas
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                missing_braces = open_braces - close_braces

                if missing_braces > 0:
                    json_str = json_str.rstrip()
                    # Si termina con coma, quitarla
                    if json_str.endswith(','):
                        json_str = json_str[:-1]
                    # Agregar las llaves faltantes
                    json_str += '\n' + '}' * missing_braces

            return json.loads(json_str)
        except (json.JSONDecodeError, Exception):
            pass

        print(f"[LLM ERROR] JSON inválido después de todas las correcciones")
        print(f"JSON string: {json_str[:500]}")
        return None

    def _validate_and_clean(self, extracted_data: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """
        Valida y limpia datos extraídos por el LLM

        Args:
            extracted_data: Datos crudos del LLM

        Returns:
            (datos_limpios, confidence_score)
        """
        cleaned = {}
        issues = []

        # 1. EXPERIENCIA
        exp_min = extracted_data.get("experiencia_min_anios")
        exp_max = extracted_data.get("experiencia_max_anios")

        if isinstance(exp_min, (int, float)) and 0 <= exp_min <= 30:
            cleaned["experiencia_min_anios"] = int(exp_min)
        else:
            cleaned["experiencia_min_anios"] = None
            if exp_min is not None:
                issues.append("experiencia_min fuera de rango")

        if isinstance(exp_max, (int, float)) and 0 <= exp_max <= 30:
            cleaned["experiencia_max_anios"] = int(exp_max)
        else:
            cleaned["experiencia_max_anios"] = None
            if exp_max is not None:
                issues.append("experiencia_max fuera de rango")

        # Validar que min <= max
        if (cleaned["experiencia_min_anios"] is not None and
            cleaned["experiencia_max_anios"] is not None and
            cleaned["experiencia_min_anios"] > cleaned["experiencia_max_anios"]):
            issues.append("experiencia_min > experiencia_max")
            cleaned["experiencia_max_anios"] = None

        # 2. EDUCACIÓN
        niveles_validos = ["primario", "secundario", "terciario", "universitario", "posgrado"]
        estados_validos = ["en_curso", "completo", "incompleto"]

        nivel = extracted_data.get("nivel_educativo")
        cleaned["nivel_educativo"] = nivel if nivel in niveles_validos else None

        estado = extracted_data.get("estado_educativo")
        cleaned["estado_educativo"] = estado if estado in estados_validos else None

        cleaned["carrera_especifica"] = extracted_data.get("carrera_especifica")

        # 3. IDIOMAS
        cleaned["idioma_principal"] = extracted_data.get("idioma_principal")

        niveles_idioma_validos = ["basico", "intermedio", "avanzado", "nativo"]
        nivel_idioma = extracted_data.get("nivel_idioma_principal")
        cleaned["nivel_idioma_principal"] = nivel_idioma if nivel_idioma in niveles_idioma_validos else None

        # 4. SKILLS (validar que sean JSON strings)
        for field in ["skills_tecnicas_list", "soft_skills_list", "certificaciones_list",
                      "beneficios_list", "requisitos_excluyentes_list", "requisitos_deseables_list"]:
            value = extracted_data.get(field)

            if value is None:
                cleaned[field] = None
            elif isinstance(value, str):
                # Ya es string, validar que sea JSON válido
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        cleaned[field] = value
                    else:
                        cleaned[field] = None
                        issues.append(f"{field} no es un array")
                except:
                    cleaned[field] = None
                    issues.append(f"{field} JSON inválido")
            elif isinstance(value, list):
                # Convertir lista a JSON string
                cleaned[field] = json.dumps(value, ensure_ascii=False)
            else:
                cleaned[field] = None
                issues.append(f"{field} tipo inválido")

        # 5. SALARIOS
        salario_min = extracted_data.get("salario_min")
        salario_max = extracted_data.get("salario_max")
        moneda = extracted_data.get("moneda")

        monedas_validas = ["ARS", "USD", "EUR"]

        if isinstance(salario_min, (int, float)) and salario_min > 0:
            cleaned["salario_min"] = float(salario_min)
        else:
            cleaned["salario_min"] = None

        if isinstance(salario_max, (int, float)) and salario_max > 0:
            cleaned["salario_max"] = float(salario_max)
        else:
            cleaned["salario_max"] = None

        cleaned["moneda"] = moneda if moneda in monedas_validas else None

        # Si hay salario pero no moneda, o viceversa → error
        if (cleaned["salario_min"] or cleaned["salario_max"]) and not cleaned["moneda"]:
            issues.append("salario sin moneda")
            cleaned["salario_min"] = None
            cleaned["salario_max"] = None

        # 6. MODALIDAD
        jornadas_validas = ["full_time", "part_time", "por_proyecto", "temporal"]
        jornada = extracted_data.get("jornada_laboral")
        cleaned["jornada_laboral"] = jornada if jornada in jornadas_validas else None

        horario_flex = extracted_data.get("horario_flexible")
        if horario_flex in [0, 1, True, False]:
            cleaned["horario_flexible"] = 1 if horario_flex else 0
        else:
            cleaned["horario_flexible"] = None

        # 7. CAMPOS NUEVOS v6.0

        # experiencia_cargo_previo (string)
        cargo_previo = extracted_data.get("experiencia_cargo_previo")
        if cargo_previo and isinstance(cargo_previo, str):
            cleaned["experiencia_cargo_previo"] = str(cargo_previo)
        else:
            cleaned["experiencia_cargo_previo"] = None

        # tecnologias_stack_list (JSON string array)
        tech_stack = extracted_data.get("tecnologias_stack_list")
        if tech_stack is None:
            cleaned["tecnologias_stack_list"] = None
        elif isinstance(tech_stack, str):
            try:
                parsed = json.loads(tech_stack)
                if isinstance(parsed, list):
                    cleaned["tecnologias_stack_list"] = tech_stack
                else:
                    cleaned["tecnologias_stack_list"] = None
                    issues.append("tecnologias_stack_list no es un array")
            except:
                cleaned["tecnologias_stack_list"] = None
                issues.append("tecnologias_stack_list JSON inválido")
        elif isinstance(tech_stack, list):
            cleaned["tecnologias_stack_list"] = json.dumps(tech_stack, ensure_ascii=False)
        else:
            cleaned["tecnologias_stack_list"] = None

        # sector_industria (string)
        sector = extracted_data.get("sector_industria")
        if sector and isinstance(sector, str):
            cleaned["sector_industria"] = str(sector)
        else:
            cleaned["sector_industria"] = None

        # nivel_seniority (string con valores fijos)
        niveles_seniority_validos = ["trainee", "junior", "semi-senior", "senior", "lead", "manager", "director"]
        seniority = extracted_data.get("nivel_seniority")
        if seniority in niveles_seniority_validos:
            cleaned["nivel_seniority"] = seniority
        else:
            cleaned["nivel_seniority"] = None
            if seniority is not None:
                issues.append("nivel_seniority valor inválido")

        # modalidad_contratacion (string con valores fijos)
        modalidades_validas = ["remoto", "presencial", "hibrido"]
        modalidad = extracted_data.get("modalidad_contratacion")
        if modalidad in modalidades_validas:
            cleaned["modalidad_contratacion"] = modalidad
        else:
            cleaned["modalidad_contratacion"] = None
            if modalidad is not None:
                issues.append("modalidad_contratacion valor inválido")

        # disponibilidad_viajes (0/1)
        disp_viajes = extracted_data.get("disponibilidad_viajes")
        if disp_viajes in [0, 1, True, False]:
            cleaned["disponibilidad_viajes"] = 1 if disp_viajes else 0
        else:
            cleaned["disponibilidad_viajes"] = None

        # Calcular confidence score
        # Penalizar por issues encontrados
        confidence = 1.0 - (len(issues) * 0.05)  # -5% por cada issue
        confidence = max(0.0, min(1.0, confidence))

        if issues:
            print(f"[VALIDATOR] {len(issues)} issues encontrados: {', '.join(issues[:3])}")

        return cleaned, confidence

    def _apply_contextual_inferences(self, extracted_data: Dict[str, Any], titulo: str, descripcion: str) -> Dict[str, Any]:
        """
        Aplica reglas de inferencia contextual para completar campos null

        v5.1: Post-procesamiento que garantiza completitud similar a v4.0
        manteniendo la validación ESCO estricta del LLM

        Args:
            extracted_data: Datos extraídos por el LLM
            titulo: Título de la oferta
            descripcion: Descripción completa

        Returns:
            Datos con inferencias aplicadas
        """
        import re

        data = extracted_data.copy()
        titulo_lower = titulo.lower()

        # REGLA 1: Nivel Educativo (basado en tipo de puesto)
        if data.get("nivel_educativo") is None:
            # Puestos operativos/manuales
            if any(kw in titulo_lower for kw in ["chofer", "repartidor", "repositor", "limpieza", "seguridad", "cadete", "mozo", "ayudante"]):
                data["nivel_educativo"] = "secundario"

            # Puestos de ventas/atención al cliente
            elif any(kw in titulo_lower for kw in ["vendedor", "cajero", "telemarketing", "atencion al cliente", "recepcionista"]):
                data["nivel_educativo"] = "secundario"

            # Puestos administrativos junior
            elif any(kw in titulo_lower for kw in ["auxiliar", "asistente", "administrativo"]):
                data["nivel_educativo"] = "secundario"  # Conservador

            # Puestos técnicos
            elif any(kw in titulo_lower for kw in ["tecnico", "especialista", "instructor", "operario"]):
                data["nivel_educativo"] = "terciario"

            # Puestos profesionales
            elif any(kw in titulo_lower for kw in ["analista", "ingeniero", "desarrollador", "programador", "contador", "abogado"]):
                data["nivel_educativo"] = "universitario"

            # Puestos gerenciales/directivos
            elif any(kw in titulo_lower for kw in ["gerente", "jefe", "coordinador", "director", "supervisor", "responsable"]):
                data["nivel_educativo"] = "universitario"

        # REGLA 2: Idioma Principal (Argentina → español por defecto)
        if data.get("idioma_principal") is None:
            data["idioma_principal"] = "español"

        # REGLA 3: Nivel de idioma principal (si es español y no está especificado)
        if data.get("idioma_principal") == "español" and data.get("nivel_idioma_principal") is None:
            data["nivel_idioma_principal"] = "nativo"

        # REGLA 4: Experiencia (interpretación de términos)
        if data.get("experiencia_min_anios") is None and data.get("experiencia_max_anios") is None:
            if any(kw in titulo_lower for kw in ["junior", "trainee", "sin experiencia"]):
                data["experiencia_min_anios"] = 0
                data["experiencia_max_anios"] = 2
            elif any(kw in titulo_lower for kw in ["semi-senior", "semi senior", "ssr"]):
                data["experiencia_min_anios"] = 2
                data["experiencia_max_anios"] = 4
            elif any(kw in titulo_lower for kw in ["senior", "sr"]):
                data["experiencia_min_anios"] = 4

        return data

    def process_oferta(self,
                      id_oferta: str,
                      descripcion: str,
                      titulo: str = "",
                      use_regex_baseline: bool = True) -> Optional[Dict[str, Any]]:
        """
        Procesa una oferta con el pipeline híbrido v5.1

        Args:
            id_oferta: ID de la oferta
            descripcion: Texto completo de la descripción
            titulo: Título de la oferta (para inferencias contextuales)
            use_regex_baseline: Si usar regex v3.7 como baseline

        Returns:
            Dict con datos extraídos o None si error
        """
        start_time = time.time()

        try:
            # PASO 1: Extracción baseline con regex v3.7 (opcional)
            regex_baseline = None
            if use_regex_baseline:
                try:
                    # Usar BumeranExtractor para baseline
                    baseline_full = self.regex_extractor.extract_all(descripcion, titulo="")

                    # Convertir a formato dict simple (sin metadata)
                    regex_baseline = {}
                    for key, value in baseline_full.items():
                        if isinstance(value, dict) and 'value' in value:
                            regex_baseline[key] = value['value']
                        else:
                            regex_baseline[key] = value

                except Exception as e:
                    print(f"[REGEX ERROR] {id_oferta}: {e}")
                    regex_baseline = None

            # PASO 2: Obtener contexto RAG
            rag_context = self._get_rag_context()

            # PASO 3: Construir prompt completo
            prompt = generate_extraction_prompt_v6(
                job_description=descripcion,
                use_rag=True,
                rag_context=rag_context,
                regex_baseline=regex_baseline
            )

            # PASO 4: Llamar a Ollama LLM
            llm_output = self._call_ollama_llm(prompt)

            if llm_output is None:
                return None

            # PASO 4.5: Aplicar inferencias contextuales (v5.1)
            # Completa campos null con reglas heurísticas basadas en el título
            llm_output_with_inferences = self._apply_contextual_inferences(
                extracted_data=llm_output,
                titulo=titulo,
                descripcion=descripcion
            )

            # PASO 5: Validar y limpiar output
            cleaned_data, confidence = self._validate_and_clean(llm_output_with_inferences)

            # Calcular quality score (campos no-null)
            quality_score = sum(1 for v in cleaned_data.values() if v is not None)

            # Calcular tiempo de procesamiento
            processing_time_ms = int((time.time() - start_time) * 1000)

            result = {
                "id_oferta": id_oferta,
                "nlp_version": self.VERSION,
                "extracted_data": cleaned_data,
                "quality_score": quality_score,
                "confidence_score": confidence,
                "processing_time_ms": processing_time_ms,
                "extraction_method": self.EXTRACTION_METHOD,
                "error_message": None
            }

            # Actualizar estadísticas
            self.stats["total_success"] += 1
            self.stats["total_time_ms"] += processing_time_ms

            return result

        except Exception as e:
            print(f"[ERROR] {id_oferta}: {e}")
            self.stats["total_errors"] += 1
            return {
                "id_oferta": id_oferta,
                "nlp_version": self.VERSION,
                "extracted_data": {},
                "quality_score": 0,
                "confidence_score": 0.0,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "extraction_method": self.EXTRACTION_METHOD,
                "error_message": str(e)
            }

    def save_to_history(self, result: Dict[str, Any]):
        """
        Guarda resultado en ofertas_nlp_history

        Args:
            result: Resultado del procesamiento
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO ofertas_nlp_history (
                    id_oferta,
                    nlp_version,
                    processed_at,
                    extracted_data,
                    quality_score,
                    confidence_score,
                    processing_time_ms,
                    is_active,
                    extraction_method,
                    error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result["id_oferta"],
                result["nlp_version"],
                datetime.now().isoformat(),
                json.dumps(result["extracted_data"], ensure_ascii=False),
                result["quality_score"],
                result["confidence_score"],
                result["processing_time_ms"],
                0,  # No activar automáticamente (requiere validación)
                result["extraction_method"],
                result["error_message"]
            ))

            conn.commit()

        except Exception as e:
            print(f"[DB ERROR] No se pudo guardar {result['id_oferta']}: {e}")
            conn.rollback()
        finally:
            conn.close()

    def process_batch(self,
                     limit: int = 100,
                     only_empty: bool = False,
                     min_quality_score: float = None) -> Dict[str, Any]:
        """
        Procesa un batch de ofertas

        Args:
            limit: Cantidad máxima de ofertas a procesar
            only_empty: Solo procesar ofertas sin versión 5.0.0
            min_quality_score: Solo reprocesar ofertas con quality_score < X

        Returns:
            Dict con estadísticas del batch
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Construir query
        query = """
            SELECT o.id_oferta, o.descripcion
            FROM ofertas o
            WHERE o.descripcion IS NOT NULL
              AND LENGTH(o.descripcion) > 100
        """

        if only_empty:
            query += """
                AND NOT EXISTS (
                    SELECT 1 FROM ofertas_nlp_history h
                    WHERE h.id_oferta = o.id_oferta
                      AND h.nlp_version = '5.0.0'
                )
            """

        if min_quality_score is not None:
            query += f"""
                AND EXISTS (
                    SELECT 1 FROM ofertas_nlp_history h
                    WHERE h.id_oferta = o.id_oferta
                      AND h.is_active = 1
                      AND h.quality_score < {min_quality_score}
                )
            """

        query += f" ORDER BY o.fecha_publicacion_datetime DESC LIMIT {limit}"

        cursor.execute(query)
        ofertas = cursor.fetchall()
        conn.close()

        total_ofertas = len(ofertas)
        print(f"\n[BATCH] Procesando {total_ofertas} ofertas con NLP v5.0")
        print(f"[BATCH] Modelo: {self.OLLAMA_MODEL}")
        print()

        # Reset stats
        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_ms": 0,
            "llm_calls": 0,
            "llm_errors": 0
        }

        for i, (id_oferta, descripcion) in enumerate(ofertas, 1):
            print(f"[{i}/{total_ofertas}] Procesando {id_oferta}...", end=" ")

            result = self.process_oferta(id_oferta, descripcion)

            if result:
                self.save_to_history(result)
                print(f"OK (Quality: {result['quality_score']}, Conf: {result['confidence_score']:.2f}, Time: {result['processing_time_ms']}ms)")
            else:
                print("ERROR")

            self.stats["total_processed"] += 1

            # Pausa breve entre ofertas para no saturar Ollama
            time.sleep(0.5)

        # Calcular estadísticas finales
        avg_time = self.stats["total_time_ms"] / max(1, self.stats["total_success"])
        success_rate = (self.stats["total_success"] / max(1, self.stats["total_processed"])) * 100
        llm_error_rate = (self.stats["llm_errors"] / max(1, self.stats["llm_calls"])) * 100

        print()
        print("=" * 70)
        print("ESTADÍSTICAS DEL BATCH")
        print("=" * 70)
        print(f"Total procesadas:     {self.stats['total_processed']}")
        print(f"Éxitos:               {self.stats['total_success']} ({success_rate:.1f}%)")
        print(f"Errores:              {self.stats['total_errors']}")
        print(f"Llamadas LLM:         {self.stats['llm_calls']}")
        print(f"Errores LLM:          {self.stats['llm_errors']} ({llm_error_rate:.1f}%)")
        print(f"Tiempo promedio:      {avg_time:.0f}ms")
        print(f"Tiempo total:         {self.stats['total_time_ms']/1000:.1f}s")
        print("=" * 70)

        return self.stats


def check_ollama_status():
    """Verifica que Ollama esté corriendo"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"[OK] Ollama está corriendo")
            print(f"[OK] Modelos disponibles: {', '.join(model_names)}")

            if "llama3.1:8b" not in model_names:
                print(f"[WARNING] Modelo llama3.1:8b no encontrado")
                print(f"[WARNING] Ejecuta: ollama pull llama3.1:8b")
                return False

            return True
        else:
            print(f"[ERROR] Ollama responde con status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] No se puede conectar a Ollama en localhost:11434")
        print(f"[ERROR] Inicia Ollama con: ollama serve")
        return False
    except Exception as e:
        print(f"[ERROR] Error al verificar Ollama: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="NLP Extractor v5.0 - Hybrid RAG System")
    parser.add_argument("--mode", choices=["test", "production"], default="test",
                       help="Modo de ejecución (test=10 ofertas, production=batch completo)")
    parser.add_argument("--limit", type=int, default=100,
                       help="Cantidad de ofertas a procesar (default: 100)")
    parser.add_argument("--only-empty", action="store_true",
                       help="Solo procesar ofertas sin versión 5.0.0")
    parser.add_argument("--min-quality", type=float,
                       help="Solo reprocesar ofertas con quality_score < X")
    parser.add_argument("--db", type=str,
                       help="Path a la base de datos (default: ./bumeran_scraping.db)")

    args = parser.parse_args()

    print("=" * 70)
    print("NLP EXTRACTOR v5.0 - HYBRID RAG SYSTEM")
    print("=" * 70)
    print(f"Modo: {args.mode.upper()}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Verificar Ollama
    if not check_ollama_status():
        print("\n[ERROR] Ollama no está disponible. Abortando.")
        return 1

    print()

    # Inicializar extractor
    try:
        extractor = NLPExtractorV5(db_path=args.db)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    # Determinar límite según modo
    if args.mode == "test":
        limit = min(10, args.limit)
        print(f"[TEST MODE] Procesando {limit} ofertas de prueba")
    else:
        limit = args.limit
        print(f"[PRODUCTION MODE] Procesando hasta {limit} ofertas")

    print()

    # Procesar batch
    try:
        stats = extractor.process_batch(
            limit=limit,
            only_empty=args.only_empty,
            min_quality_score=args.min_quality
        )

        print("\n[OK] Procesamiento completado")

        if args.mode == "test":
            print("\nPróximos pasos:")
            print("  1. Verificar resultados: SELECT * FROM ofertas_nlp_history WHERE nlp_version='5.0.0' LIMIT 5;")
            print("  2. Comparar con v4.0.0: Ejecutar análisis A/B")
            print("  3. Si todo OK, ejecutar en modo production")

        return 0

    except KeyboardInterrupt:
        print("\n\n[!] Procesamiento interrumpido por el usuario")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Error durante procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
