#!/usr/bin/env python3
"""
NLP Postprocessor v1.1 - Correcciones post-LLM + merge skills regex
====================================================================

VERSION: 1.1.0
FECHA: 2025-12-14
ORIGEN: Excel validacion Gold Set 49 ofertas + skills_database.json

ERRORES CORREGIDOS:
  - ID 1118027243: Campos retornan TRUE en lugar de texto
  - ID 1118026729: provincia = "FALSO\nCapital Federal"
  - ID 1117984105: experiencia_min = 35 (era edad 35-50)
  - ID 1118023904: experiencia_min = 20 (era edad 20-45)
  - ID 1118026700: No lee campos estructurados del scraping

FLUJO:
  1. Preprocesamiento: Extraer campos del scraping (ubicacion -> provincia, localidad)
  2. Validacion: Rechazar booleanos en campos texto
  3. Re-extraccion: Regex experiencia excluyendo patrones de edad
  4. Inferencia: modalidad, seniority, area_funcional
  5. Normalizacion: CABA -> Capital Federal
  6. Defaults: Campos booleanos = 0

Uso:
    from nlp_postprocessor import NLPPostprocessor

    pp = NLPPostprocessor()

    # Pre-LLM
    pre_data = pp.preprocess(row_from_ofertas)

    # Post-LLM
    corrected = pp.postprocess(llm_output, descripcion_texto)
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class NLPPostprocessor:
    """
    Postprocesador NLP basado en configs JSON
    """

    VERSION = "1.1.0"

    def __init__(self, config_dir: str = None, verbose: bool = False):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"

        self.config_dir = Path(config_dir)
        self.verbose = verbose

        # Cargar configs
        self.configs = self._load_configs()

        # Stats
        self.stats = {
            "campos_preprocesados": 0,
            "booleanos_rechazados": 0,
            "experiencia_corregida": 0,
            "campos_inferidos": 0,
            "campos_normalizados": 0,
            "skills_regex_agregadas": 0,
            "defaults_aplicados": 0,
        }

    def _load_configs(self) -> Dict[str, Any]:
        """Carga todos los archivos de configuracion NLP"""
        configs = {}
        config_files = [
            "nlp_preprocessing.json",
            "nlp_validation.json",
            "nlp_extraction_patterns.json",
            "nlp_inference_rules.json",
            "nlp_defaults.json",
            "nlp_normalization.json",
        ]

        for filename in config_files:
            filepath = self.config_dir / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    key = filename.replace(".json", "").replace("nlp_", "")
                    configs[key] = json.load(f)
                    if self.verbose:
                        print(f"[CONFIG] Cargado: {filename}")
            else:
                if self.verbose:
                    print(f"[CONFIG] No encontrado: {filename}")

        return configs

    # =========================================================================
    # PASO 1: PREPROCESAMIENTO (antes del LLM)
    # =========================================================================

    def preprocess(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae campos estructurados del scraping ANTES de llamar al LLM

        Args:
            row: Fila de la tabla ofertas con campos del scraping

        Returns:
            Dict con campos pre-extraidos (localidad, provincia, etc.)
        """
        result = {}
        config = self.configs.get("preprocessing", {})

        # Campos estructurados (ubicacion -> localidad, provincia)
        campos_estructurados = config.get("campos_estructurados", {})

        for campo_config in campos_estructurados.values():
            campo_origen = campo_config.get("campo_origen")
            valor_origen = row.get(campo_origen, "")

            if valor_origen and isinstance(valor_origen, str):
                separador = campo_config.get("separador", ",")
                campos_destino = campo_config.get("campos_destino", [])

                partes = [p.strip() for p in valor_origen.split(separador)]

                for i, campo_destino in enumerate(campos_destino):
                    if i < len(partes) and partes[i]:
                        result[campo_destino] = partes[i]
                        self.stats["campos_preprocesados"] += 1
                        if self.verbose:
                            print(f"[PREPROC] {campo_destino} = '{partes[i]}' (de {campo_origen})")

        # Campos directos
        campos_directos = config.get("campos_directos", {})
        for campo_destino, campo_origen in campos_directos.items():
            valor = row.get(campo_origen)
            if valor:
                result[campo_destino] = valor

        return result

    # =========================================================================
    # PASO 2: VALIDACION (rechazar booleanos)
    # =========================================================================

    def _validate_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida tipos de datos y rechaza booleanos en campos texto

        Corrige errores como:
          - provincia = TRUE -> null
          - localidad = FALSE -> null
        """
        config = self.configs.get("validation", {})
        rechazo = config.get("rechazo_booleanos", {})

        campos_texto = rechazo.get("campos_texto", [])
        valores_rechazados = rechazo.get("valores_rechazados", [
            "TRUE", "FALSE", "true", "false", "True", "False"
        ])

        for campo in campos_texto:
            valor = data.get(campo)
            if valor is not None:
                # Verificar si es booleano Python
                if isinstance(valor, bool):
                    data[campo] = None
                    self.stats["booleanos_rechazados"] += 1
                    if self.verbose:
                        print(f"[VALID] {campo} = {valor} (bool) -> null")

                # Verificar si es string que parece booleano
                elif isinstance(valor, str):
                    valor_limpio = valor.strip()
                    if valor_limpio in valores_rechazados:
                        data[campo] = None
                        self.stats["booleanos_rechazados"] += 1
                        if self.verbose:
                            print(f"[VALID] {campo} = '{valor_limpio}' -> null")

                    # Detectar casos como "FALSO\nCapital Federal"
                    for rechazado in valores_rechazados:
                        if valor_limpio.startswith(rechazado + "\n"):
                            # Extraer el valor real despues del booleano
                            valor_real = valor_limpio.split("\n", 1)[1].strip()
                            if valor_real:
                                data[campo] = valor_real
                                if self.verbose:
                                    print(f"[VALID] {campo} = '{valor_limpio[:20]}...' -> '{valor_real}'")

        # Validar rangos numericos
        rangos = config.get("validacion_rangos", {})
        for campo, rango in rangos.items():
            valor = data.get(campo)
            if valor is not None and isinstance(valor, (int, float)):
                min_val = rango.get("min", float("-inf"))
                max_val = rango.get("max", float("inf"))

                if not (min_val <= valor <= max_val):
                    if self.verbose:
                        print(f"[VALID] {campo} = {valor} fuera de rango [{min_val}, {max_val}] -> null")
                    data[campo] = None

        return data

    # =========================================================================
    # PASO 3: RE-EXTRACCION EXPERIENCIA (excluyendo edad)
    # =========================================================================

    def _extract_experiencia(self, descripcion: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-extrae experiencia_min/max excluyendo patrones de edad

        Corrige errores como:
          - "edad 35-50 anos" -> NO es experiencia
          - "experiencia de 3 anos" -> SI es experiencia
        """
        config = self.configs.get("extraction_patterns", {})
        exp_config = config.get("experiencia", {})

        if not descripcion:
            return data

        texto = descripcion.lower()

        # Paso 1: Encontrar y marcar regiones de EDAD (no extraer)
        patrones_excluir = exp_config.get("patrones_excluir", [])
        regiones_excluidas = []

        for patron_info in patrones_excluir:
            patron = patron_info.get("patron", "")
            if patron:
                try:
                    for match in re.finditer(patron, texto, re.IGNORECASE):
                        regiones_excluidas.append((match.start(), match.end()))
                        if self.verbose:
                            print(f"[EXP] Excluido: '{match.group()}' ({patron_info.get('caso', '')})")
                except re.error:
                    pass

        # Paso 2: Buscar experiencia en texto (fuera de regiones excluidas)
        patrones_validos = exp_config.get("patrones_validos", [])
        experiencia_encontrada = None

        for patron_info in sorted(patrones_validos, key=lambda x: x.get("prioridad", 99)):
            patron = patron_info.get("patron", "")
            if not patron:
                continue

            try:
                for match in re.finditer(patron, texto, re.IGNORECASE):
                    # Verificar que no este en region excluida
                    en_region_excluida = any(
                        start <= match.start() < end or start < match.end() <= end
                        for start, end in regiones_excluidas
                    )

                    if en_region_excluida:
                        continue

                    # Extraer valor
                    grupo_captura = patron_info.get("grupo_captura", 1)
                    if match.lastindex and match.lastindex >= grupo_captura:
                        try:
                            experiencia_encontrada = int(match.group(grupo_captura))
                            if self.verbose:
                                print(f"[EXP] Encontrado: {experiencia_encontrada} anos ('{match.group()}')")
                            break
                        except (ValueError, IndexError):
                            pass
                    elif patron_info.get("valor_default"):
                        experiencia_encontrada = patron_info["valor_default"]
                        if self.verbose:
                            print(f"[EXP] Default: {experiencia_encontrada} ('{match.group()}')")
                        break
            except re.error:
                pass

            if experiencia_encontrada is not None:
                break

        # Actualizar data si encontramos experiencia valida
        if experiencia_encontrada is not None:
            valor_actual = data.get("experiencia_min_anios")

            # Solo actualizar si:
            # 1. No hay valor actual, o
            # 2. El valor actual parece ser edad (>= 18 y <= 70)
            if valor_actual is None or (isinstance(valor_actual, (int, float)) and 18 <= valor_actual <= 70):
                if valor_actual != experiencia_encontrada:
                    if self.verbose and valor_actual is not None:
                        print(f"[EXP] Corrigiendo: {valor_actual} -> {experiencia_encontrada}")
                    data["experiencia_min_anios"] = experiencia_encontrada
                    self.stats["experiencia_corregida"] += 1

        return data

    # =========================================================================
    # PASO 4: INFERENCIA (modalidad, seniority, area)
    # =========================================================================

    def _infer_fields(self, descripcion: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infiere campos faltantes basado en keywords en la descripcion
        """
        config = self.configs.get("inference_rules", {})

        if not descripcion:
            return data

        texto = descripcion.lower()

        # Inferir cada campo configurado
        for campo, campo_config in config.items():
            if campo.startswith("_"):
                continue

            valor_actual = data.get(campo)

            # Solo inferir si esta vacio/null
            if valor_actual is not None and valor_actual != "":
                continue

            reglas = campo_config.get("reglas", [])
            valor_inferido = None

            # Buscar en reglas
            for regla in sorted(reglas, key=lambda x: x.get("prioridad", 99)):
                keywords = regla.get("contiene_cualquiera", regla.get("contiene", []))

                for keyword in keywords:
                    if keyword.lower() in texto:
                        valor_inferido = regla.get("resultado")
                        if self.verbose:
                            print(f"[INFER] {campo} = '{valor_inferido}' (keyword: '{keyword}')")
                        break

                if valor_inferido:
                    break

            # Inferencia especial por experiencia (para seniority)
            if not valor_inferido and campo == "nivel_seniority":
                inferencia_exp = campo_config.get("inferencia_por_experiencia", {})
                rangos = inferencia_exp.get("rangos", [])
                exp_min = data.get("experiencia_min_anios")

                if exp_min is not None and isinstance(exp_min, (int, float)):
                    for rango in rangos:
                        if rango.get("exp_min", 0) <= exp_min <= rango.get("exp_max", 99):
                            valor_inferido = rango.get("resultado")
                            if self.verbose:
                                print(f"[INFER] {campo} = '{valor_inferido}' (exp: {exp_min})")
                            break

            # Aplicar default si no se infirip
            if not valor_inferido:
                default = campo_config.get("default")
                if default is not None:
                    valor_inferido = default
                    if self.verbose:
                        print(f"[INFER] {campo} = '{valor_inferido}' (default)")

            if valor_inferido is not None:
                data[campo] = valor_inferido
                self.stats["campos_inferidos"] += 1

        # Inferencia de area_funcional por diccionario
        if not data.get("area_funcional"):
            area_config = config.get("area_funcional", {})
            diccionario = area_config.get("diccionario_keywords", {})

            for area, keywords in diccionario.items():
                for keyword in keywords:
                    if keyword.lower() in texto:
                        data["area_funcional"] = area
                        self.stats["campos_inferidos"] += 1
                        if self.verbose:
                            print(f"[INFER] area_funcional = '{area}' (keyword: '{keyword}')")
                        break
                if data.get("area_funcional"):
                    break

        return data

    # =========================================================================
    # PASO 5: NORMALIZACION
    # =========================================================================

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza valores (CABA -> Capital Federal, etc.)
        """
        config = self.configs.get("normalization", {})

        for campo, campo_config in config.items():
            if campo.startswith("_"):
                continue

            valor = data.get(campo)
            if valor is None or not isinstance(valor, str):
                continue

            valor = valor.strip()

            # Aplicar mapeo
            mapeo = campo_config.get("mapeo", {})
            if valor in mapeo:
                nuevo_valor = mapeo[valor]
                if nuevo_valor != valor:
                    data[campo] = nuevo_valor
                    self.stats["campos_normalizados"] += 1
                    if self.verbose:
                        print(f"[NORM] {campo}: '{valor}' -> '{nuevo_valor}'")
                continue

            # Limpiar prefijos
            prefijos = campo_config.get("limpiar_prefijos", [])
            for prefijo in prefijos:
                if valor.startswith(prefijo):
                    valor = valor[len(prefijo):].strip()
                    data[campo] = valor
                    self.stats["campos_normalizados"] += 1
                    break

        return data

    # =========================================================================
    # PASO 6: MERGE SKILLS REGEX (NUEVO v1.1)
    # =========================================================================

    def _merge_skills_regex(self, data: Dict[str, Any], skills_regex: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Combina skills extraidas por regex (diccionario) con skills del LLM

        Args:
            data: Dict con campos del LLM
            skills_regex: Dict con skills_tecnicas_regex y soft_skills_regex

        Returns:
            Dict con skills combinadas (sin duplicados)
        """
        if not skills_regex:
            return data

        # Skills tecnicas: combinar regex + LLM
        skills_tecnicas_regex = skills_regex.get("skills_tecnicas_regex", [])
        skills_tecnicas_llm = data.get("skills_tecnicas_list", [])
        tecnologias_llm = data.get("tecnologias_list", [])

        # Normalizar formato (puede ser lista de strings o lista de dicts)
        def extract_valores(lista):
            valores = []
            for item in lista or []:
                if isinstance(item, dict):
                    valores.append(item.get("valor", "").lower())
                elif isinstance(item, str):
                    valores.append(item.lower())
            return valores

        skills_llm_norm = set(extract_valores(skills_tecnicas_llm) + extract_valores(tecnologias_llm))

        # Agregar skills del regex que no estan en LLM
        nuevas_skills = []
        for skill in skills_tecnicas_regex:
            if skill.lower() not in skills_llm_norm:
                nuevas_skills.append({"valor": skill, "texto_original": f"[regex] {skill}"})
                if self.verbose:
                    print(f"[SKILLS] Agregado de regex: {skill}")

        if nuevas_skills:
            if not isinstance(skills_tecnicas_llm, list):
                skills_tecnicas_llm = []
            data["skills_tecnicas_list"] = skills_tecnicas_llm + nuevas_skills
            self.stats["skills_regex_agregadas"] = len(nuevas_skills)

        # Soft skills: combinar regex + LLM
        soft_skills_regex = skills_regex.get("soft_skills_regex", [])
        soft_skills_llm = data.get("soft_skills_list", [])

        soft_llm_norm = set(extract_valores(soft_skills_llm))

        nuevas_soft = []
        for skill in soft_skills_regex:
            if skill.lower() not in soft_llm_norm:
                nuevas_soft.append({"valor": skill, "texto_original": f"[regex] {skill}"})
                if self.verbose:
                    print(f"[SKILLS] Soft agregado de regex: {skill}")

        if nuevas_soft:
            if not isinstance(soft_skills_llm, list):
                soft_skills_llm = []
            data["soft_skills_list"] = soft_skills_llm + nuevas_soft

        return data

    # =========================================================================
    # PASO 7: DEFAULTS
    # =========================================================================

    def _apply_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica valores default para campos no extraidos
        """
        config = self.configs.get("defaults", {})

        # Campos booleanos
        campos_bool = config.get("campos_booleanos", {})
        for campo, campo_config in campos_bool.items():
            # Ignorar claves de metadata
            if campo.startswith("_") or not isinstance(campo_config, dict):
                continue
            if data.get(campo) is None:
                default = campo_config.get("default", 0)
                data[campo] = default
                self.stats["defaults_aplicados"] += 1
                if self.verbose:
                    print(f"[DEFAULT] {campo} = {default}")

        # Campos numericos
        campos_num = config.get("campos_numericos", {})
        for campo, campo_config in campos_num.items():
            if campo.startswith("_") or not isinstance(campo_config, dict):
                continue
            if data.get(campo) is None:
                default = campo_config.get("default")
                if default is not None:
                    data[campo] = default
                    self.stats["defaults_aplicados"] += 1

        # Campos texto
        campos_texto = config.get("campos_texto", {})
        for campo, campo_config in campos_texto.items():
            if campo.startswith("_") or not isinstance(campo_config, dict):
                continue
            if data.get(campo) is None:
                default = campo_config.get("default")
                if default is not None:
                    data[campo] = default
                    self.stats["defaults_aplicados"] += 1

        return data

    # =========================================================================
    # PIPELINE COMPLETO
    # =========================================================================

    def postprocess(self, data: Dict[str, Any], descripcion: str = "",
                    skills_regex: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Aplica todas las correcciones post-LLM

        Args:
            data: Dict con campos extraidos por el LLM
            descripcion: Texto original de la oferta
            skills_regex: Dict con skills_tecnicas_regex y soft_skills_regex de Capa 0

        Returns:
            Dict con campos corregidos
        """
        # Reset stats
        for key in self.stats:
            self.stats[key] = 0

        # Paso 2: Validacion de tipos
        data = self._validate_types(data)

        # Paso 3: Re-extraccion experiencia
        data = self._extract_experiencia(descripcion, data)

        # Paso 4: Inferencia
        data = self._infer_fields(descripcion, data)

        # Paso 5: Normalizacion
        data = self._normalize(data)

        # Paso 6: Merge skills regex (NUEVO v1.1)
        if skills_regex:
            data = self._merge_skills_regex(data, skills_regex)

        # Paso 7: Defaults
        data = self._apply_defaults(data)

        if self.verbose:
            print(f"\n[POSTPROC] Stats: {self.stats}")

        return data

    def process_complete(self, row: Dict[str, Any], llm_output: Dict[str, Any],
                        descripcion: str, skills_regex: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Pipeline completo: preprocesamiento + postprocesamiento

        Args:
            row: Fila original de ofertas (para campos estructurados)
            llm_output: Output del LLM
            descripcion: Texto de la descripcion
            skills_regex: Dict con skills_tecnicas_regex y soft_skills_regex de Capa 0

        Returns:
            Dict final con todos los campos corregidos
        """
        # Preprocesar (campos estructurados)
        pre_data = self.preprocess(row)

        # Postprocesar (correcciones + merge skills)
        post_data = self.postprocess(llm_output.copy(), descripcion, skills_regex)

        # Merge: preprocesados tienen prioridad si LLM no extrajo
        for campo, valor in pre_data.items():
            if post_data.get(campo) is None and valor is not None:
                post_data[campo] = valor

        return post_data

    def get_stats(self) -> Dict[str, int]:
        """Retorna estadisticas del ultimo procesamiento"""
        return self.stats.copy()


# =========================================================================
# CLI para testing
# =========================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="NLP Postprocessor v1.0")
    parser.add_argument("--test", action="store_true", help="Ejecutar tests")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    pp = NLPPostprocessor(verbose=args.verbose)

    if args.test:
        print("=" * 60)
        print("TEST: NLP Postprocessor")
        print("=" * 60)

        # Test 1: Booleanos rechazados
        print("\n[TEST 1] Rechazo de booleanos")
        test_data = {
            "provincia": True,
            "localidad": "FALSE",
            "modalidad": "FALSO\nCapital Federal",
        }
        result = pp._validate_types(test_data.copy())
        print(f"  Input:  {test_data}")
        print(f"  Output: {result}")

        # Test 2: Experiencia vs Edad
        print("\n[TEST 2] Experiencia vs Edad")
        descripcion = "Buscamos persona de 35 a 50 anos de edad con 3 anos de experiencia"
        test_data = {"experiencia_min_anios": 35}
        result = pp._extract_experiencia(descripcion, test_data.copy())
        print(f"  Descripcion: '{descripcion}'")
        print(f"  Input:  {test_data}")
        print(f"  Output: {result}")

        # Test 3: Inferencia modalidad
        print("\n[TEST 3] Inferencia modalidad")
        descripcion = "Trabajo en planta con comedor incluido"
        test_data = {"modalidad": None}
        result = pp._infer_fields(descripcion, test_data.copy())
        print(f"  Descripcion: '{descripcion}'")
        print(f"  Output: {result}")

        # Test 4: Normalizacion
        print("\n[TEST 4] Normalizacion")
        test_data = {"provincia": "CABA", "modalidad": "home office"}
        result = pp._normalize(test_data.copy())
        print(f"  Input:  {test_data}")
        print(f"  Output: {result}")

        print("\n" + "=" * 60)
        print("Tests completados")


if __name__ == "__main__":
    main()
