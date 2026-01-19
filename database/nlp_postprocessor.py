#!/usr/bin/env python3
"""
NLP Postprocessor v1.2 - Correcciones post-LLM + merge skills regex
====================================================================

VERSION: 1.2.0
FECHA: 2026-01-03
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
    Usa cache a nivel de clase para evitar recargar configs por oferta
    """

    VERSION = "1.3.0"

    # Valores validos para campos categoricos (Matching v2.1.1)
    VALID_AREA_FUNCIONAL = {
        "IT", "Ventas", "Operaciones", "RRHH", "Administracion",
        "Salud", "Produccion", "Logistica", "Marketing", "Legal", "Finanzas", "Otro",
        # Alias desde inference_rules.json
        "Ventas/Comercial", "IT/Sistemas", "Recursos Humanos", "Finanzas/Contabilidad",
        "Logistica/Operaciones", "Produccion/Manufactura", "Atencion al Cliente", "Ingenieria"
    }
    VALID_SENIORITY = {"trainee", "junior", "semisenior", "senior", "lead", "manager", "director"}
    VALID_TIPO_OFERTA = {"demanda_real", "pasantia", "becario", "freelance"}

    # Cache a nivel de clase (se carga una sola vez)
    _config_cache = None
    _config_loaded = False

    def __init__(self, config_dir: str = None, verbose: bool = False):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"

        self.config_dir = Path(config_dir)
        self.verbose = verbose

        # Cargar configs (usa cache si ya estan cargados)
        self.configs = self._load_configs_cached()

        # Stats
        self.stats = {
            "campos_preprocesados": 0,
            "booleanos_rechazados": 0,
            "experiencia_corregida": 0,
            "campos_inferidos": 0,
            "tareas_extraidas": 0,
            "sector_extraido": 0,
            "clae_clasificado": 0,
            "campos_normalizados": 0,
            "skills_regex_agregadas": 0,
            "defaults_aplicados": 0,
        }

        # Cache para CLAE (se carga una vez)
        self._clae_nomenclador = None
        self._clae_keywords_map = None

        # Cache para catálogo de empresas (sector alta confianza)
        self._empresas_catalogo = None

    def _load_configs_cached(self) -> Dict[str, Any]:
        """Carga configs usando cache a nivel de clase"""
        if NLPPostprocessor._config_loaded and NLPPostprocessor._config_cache:
            if self.verbose:
                print("[CONFIG] Usando cache (configs ya cargados)")
            return NLPPostprocessor._config_cache

        # Primera carga
        configs = self._load_configs_from_disk()

        # Guardar en cache de clase
        NLPPostprocessor._config_cache = configs
        NLPPostprocessor._config_loaded = True

        return configs

    def _load_configs_from_disk(self) -> Dict[str, Any]:
        """Carga todos los archivos de configuracion NLP desde disco"""
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

    @classmethod
    def clear_cache(cls):
        """Limpia el cache de configs (util para tests)"""
        cls._config_cache = None
        cls._config_loaded = False

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

        # GAP-3: Validacion de consistencia - swap min/max si estan invertidos
        consistencia = config.get("validacion_consistencia", {})
        reglas_swap = consistencia.get("reglas", [])

        for regla in reglas_swap:
            campo_min = regla.get("campo_min")
            campo_max = regla.get("campo_max")

            if campo_min and campo_max:
                val_min = data.get(campo_min)
                val_max = data.get(campo_max)

                if val_min is not None and val_max is not None:
                    if isinstance(val_min, (int, float)) and isinstance(val_max, (int, float)):
                        if val_min > val_max:
                            # Swap
                            data[campo_min] = val_max
                            data[campo_max] = val_min
                            self.stats["campos_normalizados"] += 1
                            if self.verbose:
                                print(f"[VALID] Swap {campo_min}={val_min} <-> {campo_max}={val_max}")

        return data

    # =========================================================================
    # PASO 2b: VALIDACION CAMPOS CATEGORICOS (Matching v2.1.1)
    # =========================================================================

    def _validate_categoricos(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida que los campos categóricos tengan valores permitidos.
        Si el valor no es válido, lo pone en null para que se infiera después.
        """
        # area_funcional
        area = data.get("area_funcional")
        if area and area not in self.VALID_AREA_FUNCIONAL:
            if self.verbose:
                print(f"[VALID] area_funcional '{area}' no valido -> null")
            data["area_funcional"] = None

        # Aplicar exclusiones de area_funcional (también sobre valores del LLM)
        area = data.get("area_funcional")
        if area:
            config = self.configs.get("inference_rules", {})
            area_config = config.get("area_funcional", {})
            exclusiones = area_config.get("exclusiones", {})
            excl_area = exclusiones.get(area, {})
            keywords_excluir = excl_area.get("excluir_si_titulo_contiene", [])

            titulo = data.get("titulo_limpio") or data.get("titulo", "") or ""
            titulo_lower = titulo.lower()

            for keyword in keywords_excluir:
                if keyword.lower() in titulo_lower:
                    if self.verbose:
                        print(f"[VALID] area_funcional '{area}' excluida por titulo contiene '{keyword}'")
                    data["area_funcional"] = None
                    break

        # nivel_seniority
        seniority = data.get("nivel_seniority")
        if seniority:
            # Normalizar a minusculas
            seniority_lower = seniority.lower().strip()
            if seniority_lower in self.VALID_SENIORITY:
                data["nivel_seniority"] = seniority_lower
            else:
                if self.verbose:
                    print(f"[VALID] nivel_seniority '{seniority}' no valido -> null")
                data["nivel_seniority"] = None

        # tipo_oferta
        tipo = data.get("tipo_oferta")
        if tipo:
            tipo_lower = tipo.lower().strip()
            if tipo_lower in self.VALID_TIPO_OFERTA:
                data["tipo_oferta"] = tipo_lower
            else:
                if self.verbose:
                    print(f"[VALID] tipo_oferta '{tipo}' no valido -> null")
                data["tipo_oferta"] = None

        # tiene_gente_cargo (convertir a int 0/1 para BD)
        tiene_gente = data.get("tiene_gente_cargo")
        if tiene_gente is not None:
            if isinstance(tiene_gente, bool):
                data["tiene_gente_cargo"] = 1 if tiene_gente else 0
            elif isinstance(tiene_gente, str):
                data["tiene_gente_cargo"] = 1 if tiene_gente.lower() in ("true", "si", "sí", "1") else 0
            elif isinstance(tiene_gente, (int, float)):
                data["tiene_gente_cargo"] = 1 if tiene_gente else 0

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
        area_config = config.get("area_funcional", {})
        diccionario = area_config.get("diccionario_keywords", {})

        if not data.get("area_funcional"):
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

        # Aplicar exclusiones de area_funcional DESPUÉS de inferir
        area_inferida = data.get("area_funcional")
        if area_inferida:
            exclusiones = area_config.get("exclusiones", {})
            excl_area = exclusiones.get(area_inferida, {})
            keywords_excluir = excl_area.get("excluir_si_titulo_contiene", [])

            titulo = data.get("titulo_limpio") or data.get("titulo", "") or ""
            titulo_lower = titulo.lower()

            for keyword in keywords_excluir:
                if keyword.lower() in titulo_lower:
                    if self.verbose:
                        print(f"[EXCL] area_funcional '{area_inferida}' excluida por titulo contiene '{keyword}'")
                    data["area_funcional"] = None
                    # Intentar re-inferir con otra área (excluyendo la actual)
                    for area2, keywords2 in diccionario.items():
                        if area2 == area_inferida:
                            continue
                        for kw in keywords2:
                            if kw.lower() in texto:
                                data["area_funcional"] = area2
                                if self.verbose:
                                    print(f"[INFER] area_funcional re-asignada = '{area2}' (keyword: '{kw}')")
                                break
                        if data.get("area_funcional"):
                            break
                    break

        # v2.2 (2026-01-14): Aplicar reglas de prioridad_por_titulo
        # Estas reglas fuerzan area_funcional basado en el título, con prioridad máxima
        prioridad_reglas = area_config.get("prioridad_por_titulo", {}).get("reglas", [])
        if prioridad_reglas:
            titulo = data.get("titulo_limpio") or data.get("titulo", "") or ""
            titulo_lower = titulo.lower()

            for regla in prioridad_reglas:
                keywords = regla.get("titulo_contiene_alguno", [])
                forzar_area = regla.get("forzar_area")

                if not keywords or not forzar_area:
                    continue

                for keyword in keywords:
                    if keyword.lower() in titulo_lower:
                        area_anterior = data.get("area_funcional")
                        if area_anterior != forzar_area:
                            data["area_funcional"] = forzar_area
                            if self.verbose:
                                print(f"[PRIO] area_funcional '{area_anterior}' -> '{forzar_area}' (prioridad titulo: '{keyword}')")
                        break
                else:
                    continue
                break  # Ya se aplicó una regla de prioridad

        return data

    # =========================================================================
    # PASO 4.4: CORRECCION SENIORITY (si inconsistente con experiencia)
    # =========================================================================

    def _corregir_seniority(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Corrige nivel_seniority si es inconsistente con experiencia_min_anios.

        Ejemplo: Si LLM puso 'junior' pero la oferta pide 7 años, corregir a 'senior'.
        """
        seniority_actual = data.get("nivel_seniority")
        exp_min = data.get("experiencia_min_anios")

        # Solo corregir si hay seniority y experiencia
        if not seniority_actual or exp_min is None:
            return data

        if not isinstance(exp_min, (int, float)):
            return data

        config = self.configs.get("inference_rules", {}).get("nivel_seniority", {})
        correccion_config = config.get("correccion_por_experiencia", {})
        reglas = correccion_config.get("reglas", [])

        if not reglas:
            return data

        seniority_lower = seniority_actual.lower().strip()

        # Las reglas están ordenadas por prioridad (exp mayor primero)
        for regla in reglas:
            seniorities_aplicables = [s.lower() for s in regla.get("seniority_actual", [])]
            exp_requerida = regla.get("exp_min_mayor_igual", 0)
            seniority_correcto = regla.get("seniority_correcto")

            if seniority_lower in seniorities_aplicables and exp_min >= exp_requerida:
                if seniority_lower != seniority_correcto.lower():
                    if self.verbose:
                        print(f"[CORR SENIORITY] {seniority_actual} -> {seniority_correcto} (exp_min={exp_min})")
                    data["nivel_seniority"] = seniority_correcto
                    self.stats["seniority_corregido"] = self.stats.get("seniority_corregido", 0) + 1
                break

        return data

    # =========================================================================
    # PASO 4.4a: FORZAR SENIORITY POR TITULO (prioridad maxima)
    # =========================================================================

    def _forzar_seniority_por_titulo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuerza nivel_seniority si el título contiene keywords de nivel.

        Ejemplo: "JEFE/A DE MANTENIMIENTO" -> manager (sin importar lo que dijo el LLM)
        """
        config = self.configs.get("inference_rules", {}).get("nivel_seniority", {})
        prioridad_config = config.get("prioridad_por_titulo", {})
        reglas = prioridad_config.get("reglas", [])

        if not reglas:
            return data

        titulo = data.get("titulo_limpio") or data.get("titulo", "") or ""
        titulo_lower = titulo.lower()

        seniority_actual = data.get("nivel_seniority")

        for regla in reglas:
            keywords = regla.get("titulo_contiene_alguno", [])
            forzar_seniority = regla.get("forzar_seniority")

            if not keywords or not forzar_seniority:
                continue

            for keyword in keywords:
                if keyword.lower() in titulo_lower:
                    if seniority_actual != forzar_seniority:
                        if self.verbose:
                            print(f"[PRIO] nivel_seniority '{seniority_actual}' -> '{forzar_seniority}' (prioridad titulo: '{keyword}')")
                        data["nivel_seniority"] = forzar_seniority
                        self.stats["seniority_forzado_titulo"] = self.stats.get("seniority_forzado_titulo", 0) + 1
                    return data  # Ya encontró match, salir

        return data

    # =========================================================================
    # PASO 4.4b: CORRECCION SIN EXPERIENCIA (detectar frases anti-experiencia)
    # =========================================================================

    def _corregir_sin_experiencia(self, descripcion: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Si el texto indica que NO se requiere experiencia, forzar exp=0 y seniority=trainee.

        Corrige alucinaciones del LLM que inventa años de experiencia cuando el texto
        dice cosas como "poca experiencia", "primeros trabajos", etc.
        """
        if not descripcion:
            return data

        config = self.configs.get("inference_rules", {}).get("nivel_seniority", {})
        sin_exp_config = config.get("correccion_sin_experiencia", {})
        frases = sin_exp_config.get("frases_sin_experiencia", [])

        if not frases:
            return data

        texto_lower = descripcion.lower()

        # Buscar cualquier frase que indique "sin experiencia"
        frase_encontrada = None
        for frase in frases:
            if frase.lower() in texto_lower:
                frase_encontrada = frase
                break

        if not frase_encontrada:
            return data

        # Aplicar corrección
        accion = sin_exp_config.get("accion", {})
        exp_correcto = accion.get("experiencia_min_anios", 0)
        seniority_correcto = accion.get("nivel_seniority", "trainee")

        # Leer umbrales del config (NO hardcodeados)
        umbral_exp = sin_exp_config.get("umbral_exp_alucinacion", 1)
        seniority_ignorar = [s.lower() for s in sin_exp_config.get("seniority_ignorar", ["trainee", "junior"])]

        exp_actual = data.get("experiencia_min_anios")
        seniority_actual = data.get("nivel_seniority")

        cambios = []

        # Solo corregir si el LLM puso un valor alto (alucinación)
        if exp_actual is not None and exp_actual > umbral_exp:
            data["experiencia_min_anios"] = exp_correcto
            cambios.append(f"exp: {exp_actual} -> {exp_correcto}")

        # Ajustar seniority si corresponde
        if seniority_actual and seniority_actual.lower() not in seniority_ignorar:
            data["nivel_seniority"] = seniority_correcto
            cambios.append(f"seniority: {seniority_actual} -> {seniority_correcto}")

        if cambios and self.verbose:
            print(f"[CORR SIN EXP] Frase '{frase_encontrada}' -> {', '.join(cambios)}")

        if cambios:
            self.stats["sin_experiencia_corregido"] = self.stats.get("sin_experiencia_corregido", 0) + 1

        return data

    # =========================================================================
    # PASO 4.5: EXTRACCION TAREAS (cuando LLM no detecta)
    # =========================================================================

    def _extract_tareas(self, descripcion: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae tareas explicitas cuando el LLM no las detectó.
        Busca frases como "será responsable de", "sus funciones incluyen", etc.
        """
        # Solo procesar si no hay tareas
        tareas_actuales = data.get("tareas_explicitas")
        if tareas_actuales and str(tareas_actuales).strip() not in ["", "null", "None", "[]"]:
            return data

        config = self.configs.get("inference_rules", {}).get("tareas_explicitas", {})
        if not config or not descripcion:
            return data

        texto = descripcion.lower()
        tareas_encontradas = []

        # Buscar patrones de inicio de frase
        patrones_inicio = config.get("patrones_inicio_frase", [])
        for patron in patrones_inicio:
            patron_lower = patron.lower()
            idx = texto.find(patron_lower)
            if idx != -1:
                # Extraer texto después del patrón hasta punto o salto de línea
                inicio = idx + len(patron_lower)
                fin = inicio + 200  # Max 200 caracteres
                resto = descripcion[inicio:fin]

                # Cortar en punto, punto y coma, o salto de línea
                for sep in ['. ', '.\n', ';', '\n\n']:
                    pos = resto.find(sep)
                    if pos > 10:  # Al menos 10 caracteres
                        resto = resto[:pos]
                        break

                resto = resto.strip()
                if len(resto) > 10 and resto not in tareas_encontradas:
                    tareas_encontradas.append(resto)
                    if self.verbose:
                        print(f"[TAREAS] Encontrado: '{resto[:50]}...'")

                if len(tareas_encontradas) >= config.get("max_tareas", 10):
                    break

        # Buscar patrones regex
        patrones_regex = config.get("patrones_regex", [])
        for patron_info in patrones_regex:
            patron = patron_info.get("patron", "")
            if patron and len(tareas_encontradas) < config.get("max_tareas", 10):
                try:
                    matches = re.findall(patron, descripcion, re.IGNORECASE)
                    for match in matches[:3]:  # Max 3 por patrón
                        if isinstance(match, tuple):
                            match = match[0]
                        match = match.strip()
                        if len(match) > 10 and match not in tareas_encontradas:
                            tareas_encontradas.append(match)
                except re.error:
                    pass

        if tareas_encontradas:
            # Formatear como lista separada por punto y coma
            data["tareas_explicitas"] = "; ".join(tareas_encontradas[:5])
            self.stats["tareas_extraidas"] += 1
            if self.verbose:
                print(f"[TAREAS] Total: {len(tareas_encontradas)} tareas extraídas")

        return data

    # =========================================================================
    # PASO 4.5b: COMPLETAR TAREAS (cuando LLM extrajo incompletas)
    # =========================================================================

    def _completar_tareas(self, descripcion: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completa tareas_explicitas cuando el LLM extrajo solo algunas.
        Busca el bloque "Tareas a realizar:" hasta "Requisitos:" y extrae todas.
        """
        if not descripcion:
            return data

        config = self.configs.get("inference_rules", {}).get("completar_tareas", {})
        if not config:
            # Config por defecto si no existe
            config = {
                "marcadores_inicio": ["tareas a realizar", "funciones del puesto", "principales funciones",
                                      "responsabilidades", "actividades principales", "funciones principales",
                                      "tareas principales", "sus tareas seran", "tus tareas seran"],
                "marcadores_fin": ["requisitos", "requerimientos", "perfil", "ofrecemos", "beneficios",
                                   "condiciones", "horario", "jornada", "salario", "remuneracion"],
                "separadores": ["\n", "•", "-", "*", "·", "●", "○"],
                "min_longitud_tarea": 8,
                "max_tareas": 10
            }

        texto_lower = descripcion.lower()

        # Buscar marcador de inicio
        inicio_bloque = -1
        marcador_usado = ""
        for marcador in config.get("marcadores_inicio", []):
            pos = texto_lower.find(marcador.lower())
            if pos != -1:
                if inicio_bloque == -1 or pos < inicio_bloque:
                    inicio_bloque = pos
                    marcador_usado = marcador

        if inicio_bloque == -1:
            return data

        # Buscar marcador de fin (después del inicio)
        fin_bloque = len(descripcion)
        for marcador in config.get("marcadores_fin", []):
            pos = texto_lower.find(marcador.lower(), inicio_bloque + len(marcador_usado))
            if pos != -1 and pos < fin_bloque:
                fin_bloque = pos

        # Extraer bloque de tareas
        bloque = descripcion[inicio_bloque:fin_bloque]

        # Remover el marcador de inicio del bloque
        for marcador in config.get("marcadores_inicio", []):
            if bloque.lower().startswith(marcador.lower()):
                bloque = bloque[len(marcador):].strip()
                # Remover ":" si quedó
                if bloque.startswith(":"):
                    bloque = bloque[1:].strip()
                break

        if not bloque:
            return data

        # Normalizar texto: insertar separadores donde hay punto+mayúscula o minúscula+mayúscula
        # Ejemplo: "cliente.Declaración" -> "cliente. Declaración"
        # Ejemplo: "CuentasGestión" -> "Cuentas; Gestión"
        # Ejemplo: "SEDICoordinación" -> "SEDI; Coordinación"
        bloque_norm = bloque

        # Patrón 1: punto seguido de mayúscula sin espacio -> agregar separador
        # Esto indica cambio de frase/tarea
        bloque_norm = re.sub(r'\.([A-ZÁÉÍÓÚ])', r'; \1', bloque_norm)

        # Patrón 2: minúscula seguida de mayúscula (cambio de palabra/tarea) -> agregar separador
        bloque_norm = re.sub(r'([a-záéíóú])([A-ZÁÉÍÓÚ][a-záéíóú]{2,})', r'\1; \2', bloque_norm)

        # Patrón 3: sigla (mayúsculas) seguida de palabra con mayúscula inicial
        # Ejemplo: "SEDICoordinación" -> "SEDI; Coordinación"
        bloque_norm = re.sub(r'([A-ZÁÉÍÓÚ]{2,})([A-ZÁÉÍÓÚ][a-záéíóú]{2,})', r'\1; \2', bloque_norm)

        bloque = bloque_norm

        # Parsear tareas individuales
        tareas_nuevas = []
        # Usar solo separadores seguros (no incluir "-" que puede estar en texto normal)
        separadores = ["\n", ";", "•", "·", "●", "○"]

        # Primero intentar separar por saltos de línea u otros separadores
        lineas = [bloque]
        for sep in separadores:
            nuevas_lineas = []
            for linea in lineas:
                partes = linea.split(sep)
                nuevas_lineas.extend(partes)
            lineas = nuevas_lineas

        min_len = config.get("min_longitud_tarea", 8)
        for linea in lineas:
            linea = linea.strip()
            # Limpiar bullets y números al inicio
            linea = re.sub(r'^[\d]+[.\)]\s*', '', linea)
            linea = re.sub(r'^[-•*·●○]\s*', '', linea)
            linea = linea.strip()

            if len(linea) >= min_len:
                # Evitar duplicados
                if not any(linea.lower() in t.lower() or t.lower() in linea.lower()
                          for t in tareas_nuevas):
                    tareas_nuevas.append(linea)

        if not tareas_nuevas:
            return data

        # Obtener tareas actuales
        tareas_actuales = data.get("tareas_explicitas", "")
        if isinstance(tareas_actuales, str):
            lista_actuales = [t.strip() for t in tareas_actuales.split(";") if t.strip()]
        else:
            lista_actuales = []

        # Agregar tareas nuevas que no estén en las actuales
        tareas_agregadas = []

        # Normalizar tareas actuales para comparación
        actuales_norm = []
        for actual in lista_actuales:
            # Extraer palabras clave (ignorar signos, normalizar)
            norm = re.sub(r'[^\w\s]', ' ', actual.lower())
            palabras = set(norm.split())
            actuales_norm.append(palabras)

        for tarea in tareas_nuevas:
            # Normalizar tarea nueva
            tarea_norm = re.sub(r'[^\w\s]', ' ', tarea.lower())
            palabras_tarea = set(tarea_norm.split())

            # Verificar si ya existe (overlap significativo de palabras)
            existe = False
            for palabras_actual in actuales_norm:
                if not palabras_actual or not palabras_tarea:
                    continue
                # Si más del 60% de las palabras coinciden, es duplicado
                overlap = len(palabras_tarea & palabras_actual)
                min_len = min(len(palabras_tarea), len(palabras_actual))
                if min_len > 0 and overlap / min_len > 0.6:
                    existe = True
                    break

            if not existe and len(tarea) >= config.get("min_longitud_tarea", 8):
                tareas_agregadas.append(tarea)
                # Agregar a actuales para evitar duplicados entre nuevas
                actuales_norm.append(palabras_tarea)

        if tareas_agregadas:
            # Combinar tareas actuales + nuevas
            todas = lista_actuales + tareas_agregadas
            max_tareas = config.get("max_tareas", 10)
            data["tareas_explicitas"] = "; ".join(todas[:max_tareas])
            self.stats["tareas_completadas"] = self.stats.get("tareas_completadas", 0) + len(tareas_agregadas)
            if self.verbose:
                print(f"[TAREAS] Completadas +{len(tareas_agregadas)}: {[t[:30] for t in tareas_agregadas]}")

        return data

    # =========================================================================
    # PASO 4.5c: EXTRAER TAREAS IMPLICITAS (texto no estructurado)
    # =========================================================================

    def _extraer_tareas_implicitas(self, descripcion: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae tareas de texto no estructurado cuando no hay lista explicita.
        Usa patrones como "dictado de cursos", "capacitaciones en", etc.
        """
        # Solo procesar si no hay tareas
        tareas_actuales = data.get("tareas_explicitas")
        if tareas_actuales and str(tareas_actuales).strip() not in ["", "null", "None"]:
            return data

        if not descripcion:
            return data

        config = self.configs.get("inference_rules", {}).get("tareas_explicitas", {})
        patrones_implicitos = config.get("patrones_implicitos", {})

        if not patrones_implicitos:
            return data

        texto = descripcion.lower()
        tareas_encontradas = []

        # Iterar por categorías de patrones
        for categoria, patrones in patrones_implicitos.items():
            if categoria.startswith("_"):
                continue  # Skip metadata

            for patron_info in patrones:
                patron = patron_info.get("patron", "")
                formato = patron_info.get("tarea_formato", "{1}")

                if not patron:
                    continue

                try:
                    matches = re.finditer(patron, texto, re.IGNORECASE)
                    for match in matches:
                        if match.groups():
                            # Extraer el grupo capturado
                            captura = match.group(1).strip()
                            # Limpiar captura
                            captura = re.sub(r'\s+', ' ', captura)
                            captura = captura.strip('.,;:')

                            if len(captura) >= 5:
                                # Formatear tarea
                                tarea = formato.replace("{1}", captura)
                                tarea = tarea[0].upper() + tarea[1:] if tarea else tarea

                                # Evitar duplicados
                                if tarea.lower() not in [t.lower() for t in tareas_encontradas]:
                                    tareas_encontradas.append(tarea)
                except re.error as e:
                    if self.verbose:
                        print(f"[WARN] Error en patron '{patron}': {e}")

        if tareas_encontradas:
            max_tareas = config.get("max_tareas", 10)
            data["tareas_explicitas"] = "; ".join(tareas_encontradas[:max_tareas])
            self.stats["tareas_implicitas"] = self.stats.get("tareas_implicitas", 0) + len(tareas_encontradas)
            if self.verbose:
                print(f"[TAREAS IMPL] Extraídas {len(tareas_encontradas)}: {tareas_encontradas}")

        return data

    # =========================================================================
    # PASO 4.6: EXTRACCION SECTOR EMPRESA (cuando LLM no detecta)
    # =========================================================================

    def _extract_sector(self, descripcion: str, data: Dict[str, Any], id_empresa: str = None) -> Dict[str, Any]:
        """
        Extrae sector/rubro de la empresa con niveles de confianza.

        IMPORTANTE: El sector debe ser del EMPLEADOR, no del PUESTO.
        - Un banco que contrata un vigilante → sector=Finanzas, NO Seguridad
        - Un hospital que contrata un contador → sector=Salud, NO Finanzas

        Prioridad de fuentes (de mayor a menor confianza):
        0. Catálogo de empresas: empresa conocida por id_empresa → confianza=alta
        1. Frase explícita: "somos una empresa de [sector]" → confianza=alta
        2. LLM extrajo directamente → confianza=media
        3. Keyword en descripción general → confianza=baja (NO USAR)

        Ver docs/guides/METODOLOGIA_SECTOR_EMPRESA.md para detalles.
        """
        import re

        # PASO 0: Buscar en catálogo de empresas (máxima confianza)
        if id_empresa:
            data = self._lookup_empresa_catalogo(id_empresa, data)
            # Si encontró en catálogo con confianza alta, no seguir buscando
            if data.get("sector_confianza") == "alta":
                return data

        config = self.configs.get("inference_rules", {}).get("sector_empresa", {})
        texto = (descripcion or "").lower()

        sector_actual = data.get("sector_empresa")
        tiene_sector = sector_actual and str(sector_actual).strip() not in ["", "null", "None"]

        # PASO 1: Buscar frase explícita "somos empresa de [sector]"
        patrones_inicio = config.get("patrones_inicio", [])
        diccionario = config.get("diccionario_sectores", {})

        for patron in patrones_inicio:
            patron_lower = patron.lower()
            if patron_lower in texto:
                # Encontró patrón, buscar sector en el texto después del patrón
                idx = texto.find(patron_lower)
                texto_despues = texto[idx + len(patron_lower):idx + len(patron_lower) + 100]

                for sector, keywords in diccionario.items():
                    for keyword in keywords:
                        if keyword.lower() in texto_despues:
                            data["sector_empresa"] = sector
                            data["sector_confianza"] = "alta"
                            data["sector_fuente"] = "frase_explicita"
                            self.stats["sector_extraido"] += 1
                            if self.verbose:
                                print(f"[SECTOR] ALTA confianza: '{sector}' (frase: '{patron}...{keyword}')")
                            return data

        # PASO 2: Si LLM ya extrajo sector, marcar confianza media
        if tiene_sector:
            # El LLM extrajo algo, asumimos confianza media
            if not data.get("sector_confianza"):
                data["sector_confianza"] = "media"
                data["sector_fuente"] = "llm"
                if self.verbose:
                    print(f"[SECTOR] MEDIA confianza: '{sector_actual}' (fuente: LLM)")
            return data

        # PASO 3: NO buscar keywords sueltos - genera falsos positivos
        # El sector debe venir de: empresa conocida, frase explícita, o LLM
        # Dejamos sin sector si no hay información confiable

        return data

    def _corregir_sector(self, data: Dict[str, Any], descripcion: str) -> Dict[str, Any]:
        """
        Corrige sector_empresa cuando el LLM clasifico incorrectamente.
        Usa keywords del titulo y descripcion para detectar sectores especificos.

        Ejemplo: Modelista clasificado como "Tecnologia" -> corregir a "Textil/Confeccion"
        """
        sector_actual = data.get("sector_empresa")
        if not sector_actual:
            return data

        config = self.configs.get("inference_rules", {}).get("correccion_sector", {})
        reglas = config.get("reglas", [])

        if not reglas:
            return data

        titulo = data.get("titulo_limpio", "") or ""
        titulo_lower = titulo.lower()
        desc_lower = (descripcion or "").lower()

        for regla in reglas:
            sectores_incorrectos = regla.get("sector_incorrecto", [])

            # Verificar si el sector actual es uno de los incorrectos
            if sector_actual not in sectores_incorrectos:
                continue

            # Buscar keywords en titulo
            keywords_titulo = regla.get("keywords_titulo", [])
            for kw in keywords_titulo:
                if kw.lower() in titulo_lower:
                    sector_correcto = regla.get("sector_correcto")
                    if self.verbose:
                        print(f"[SECTOR] Corregido: '{sector_actual}' -> '{sector_correcto}' (keyword titulo: '{kw}')")
                    data["sector_empresa"] = sector_correcto
                    self.stats["sector_corregido"] = self.stats.get("sector_corregido", 0) + 1
                    return data

            # Buscar keywords en descripcion
            keywords_desc = regla.get("keywords_descripcion", [])
            for kw in keywords_desc:
                if kw.lower() in desc_lower:
                    sector_correcto = regla.get("sector_correcto")
                    if self.verbose:
                        print(f"[SECTOR] Corregido: '{sector_actual}' -> '{sector_correcto}' (keyword desc: '{kw}')")
                    data["sector_empresa"] = sector_correcto
                    self.stats["sector_corregido"] = self.stats.get("sector_corregido", 0) + 1
                    return data

        return data

    # =========================================================================
    # PASO 4c3: CLASIFICACION CLAE (sector -> codigo CLAE oficial Argentina)
    # =========================================================================

    def _load_clae_configs(self):
        """Carga configs CLAE si no están en cache."""
        if self._clae_nomenclador is None:
            nomenclador_path = self.config_dir / "clae_nomenclador.json"
            if nomenclador_path.exists():
                with open(nomenclador_path, 'r', encoding='utf-8') as f:
                    self._clae_nomenclador = json.load(f)

        if self._clae_keywords_map is None:
            keywords_path = self.config_dir / "clae_keywords_map.json"
            if keywords_path.exists():
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    self._clae_keywords_map = json.load(f)

    def _load_empresas_catalogo(self):
        """Carga catálogo de empresas si no está en cache."""
        if self._empresas_catalogo is None:
            catalogo_path = self.config_dir / "empresas_catalogo.json"
            if catalogo_path.exists():
                with open(catalogo_path, 'r', encoding='utf-8') as f:
                    self._empresas_catalogo = json.load(f)
                if self.verbose:
                    empleadores = len(self._empresas_catalogo.get("empleadores", {}))
                    intermediarios = len(self._empresas_catalogo.get("intermediarios", {}))
                    print(f"[CATALOGO] Cargado: {empleadores} empleadores, {intermediarios} intermediarios")

    def _lookup_empresa_catalogo(self, id_empresa: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Busca empresa en catálogo y asigna sector con alta confianza.

        Si es empleador conocido -> sector del catálogo + confianza=alta
        Si es intermediario (consultora) -> es_intermediario=true (sector no confiable)

        Args:
            id_empresa: ID de la empresa (del scraping)
            data: Dict con datos NLP

        Returns:
            Dict actualizado con sector/clae si encontró match
        """
        if not id_empresa:
            return data

        self._load_empresas_catalogo()
        if not self._empresas_catalogo:
            return data

        id_str = str(id_empresa)

        # Buscar en empleadores (empresas con sector conocido)
        empleadores = self._empresas_catalogo.get("empleadores", {})
        if id_str in empleadores:
            emp = empleadores[id_str]
            data["sector_empresa"] = emp.get("sector")
            data["sector_confianza"] = "alta"
            data["sector_fuente"] = "empresa_conocida"
            data["es_intermediario"] = False

            # Si tiene CLAE, asignarlo directamente
            if emp.get("clae_code"):
                data["clae_code"] = emp["clae_code"]
                data["clae_grupo"] = emp["clae_code"][:3]
                data["clae_seccion"] = emp.get("clae_seccion")
                self.stats["clae_clasificado"] += 1

            if self.verbose:
                print(f"[CATALOGO] Empleador: {emp.get('nombre')} -> {emp.get('sector')} (ALTA confianza)")

            self.stats["sector_extraido"] += 1
            return data

        # Buscar en intermediarios (consultoras de RRHH)
        intermediarios = self._empresas_catalogo.get("intermediarios", {})
        if id_str in intermediarios:
            inter = intermediarios[id_str]
            data["es_intermediario"] = True
            # NO asignar sector - el intermediario no representa al empleador real
            if self.verbose:
                print(f"[CATALOGO] Intermediario: {inter.get('nombre')} (sector no confiable)")
            return data

        return data

    def _classify_clae(self, data: Dict[str, Any], titulo: str = "", descripcion: str = "") -> Dict[str, Any]:
        """
        Clasifica sector_empresa a código CLAE oficial.

        CLAE = Clasificador de Actividades Económicas (AFIP Argentina)
        Estructura: 6 dígitos (actividad) -> 3 dígitos (grupo) -> letra (sección)

        Prioridad de clasificación:
        1. sector_empresa (más confiable, ya inferido por NLP)
        2. titulo (específico del puesto)
        3. descripcion (puede tener keywords genéricos)

        Los campos se llenan pero NO reemplazan sector_empresa (conviven).
        """
        self._load_clae_configs()

        if not self._clae_keywords_map:
            return data

        sector_texto = data.get("sector_empresa", "") or ""
        titulo_texto = titulo or data.get("titulo_limpio", "") or ""

        # PASO 1: Buscar en sector_directo (mapeo exacto de sector_empresa)
        sector_directo = self._clae_keywords_map.get("sector_directo", {})

        # Búsqueda exacta
        if sector_texto in sector_directo:
            clae_data = sector_directo[sector_texto]
            data["clae_code"] = clae_data["clae"]
            data["clae_grupo"] = clae_data.get("grupo", clae_data["clae"][:3])
            data["clae_seccion"] = clae_data.get("seccion")
            self.stats["clae_clasificado"] += 1
            if self.verbose:
                print(f"[CLAE] '{sector_texto}' -> {clae_data['clae']} ({clae_data.get('seccion')}) [sector_directo]")
            return data

        # Búsqueda case-insensitive
        sector_lower = sector_texto.lower().strip()
        for key, clae_data in sector_directo.items():
            if key.lower() == sector_lower:
                data["clae_code"] = clae_data["clae"]
                data["clae_grupo"] = clae_data.get("grupo", clae_data["clae"][:3])
                data["clae_seccion"] = clae_data.get("seccion")
                self.stats["clae_clasificado"] += 1
                if self.verbose:
                    print(f"[CLAE] '{sector_texto}' -> {clae_data['clae']} ({clae_data.get('seccion')}) [sector_directo_ci]")
                return data

        # PASO 2: Buscar por keywords en titulo (sin descripcion para evitar falsos positivos)
        texto_busqueda = f"{sector_texto} {titulo_texto}".lower()
        best_match = None
        best_score = 0

        for mapping in self._clae_keywords_map.get("mappings", []):
            score = 0
            for kw in mapping.get("keywords", []):
                if kw.lower() in texto_busqueda:
                    score += len(kw)  # Keywords más largos = más específicos

            if score > best_score:
                best_score = score
                best_match = mapping

        if best_match:
            data["clae_code"] = best_match["clae"]
            data["clae_grupo"] = best_match.get("grupo", best_match["clae"][:3])
            data["clae_seccion"] = best_match.get("seccion")
            self.stats["clae_clasificado"] += 1
            if self.verbose:
                print(f"[CLAE] '{sector_texto}' -> {best_match['clae']} ({best_match.get('seccion')}) [keyword]")
            return data

        # No clasificado - los campos quedan NULL
        if self.verbose:
            print(f"[CLAE] '{sector_texto}' -> Sin clasificar")

        return data

    # =========================================================================
    # PASO 4d: LIMPIEZA TAREAS (eliminar prefijos, bullets, etc.)
    # =========================================================================

    def _limpiar_tareas(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia tareas_explicitas: convierte JSON a texto, elimina prefijos, bullets.
        Lee patrones desde config/nlp_inference_rules.json -> limpieza_tareas
        """
        tareas = data.get("tareas_explicitas")
        if not tareas:
            return data

        config = self.configs.get("inference_rules", {}).get("limpieza_tareas", {})

        # Paso 0: Convertir JSON array a lista de strings
        lista_tareas = []
        if isinstance(tareas, str):
            if tareas.startswith("["):
                # Es JSON array
                try:
                    parsed = json.loads(tareas)
                    for item in parsed:
                        if isinstance(item, dict):
                            valor = item.get("valor") or item.get("texto_original") or ""
                            if valor:
                                lista_tareas.append(valor)
                        elif isinstance(item, str):
                            lista_tareas.append(item)
                except json.JSONDecodeError:
                    # Si falla parsing, tratar como texto
                    lista_tareas = [t.strip() for t in tareas.split(";")]
            else:
                # Es texto separado por punto y coma
                lista_tareas = [t.strip() for t in tareas.split(";")]
        elif isinstance(tareas, list):
            for item in tareas:
                if isinstance(item, dict):
                    valor = item.get("valor") or item.get("texto_original") or ""
                    if valor:
                        lista_tareas.append(valor)
                elif isinstance(item, str):
                    lista_tareas.append(item)

        if not lista_tareas:
            return data

        if not config:
            # Sin config, solo convertir a texto limpio
            data["tareas_explicitas"] = "; ".join(lista_tareas)
            return data
        tareas_limpias = []

        for tarea in lista_tareas:
            if not tarea:
                continue

            # 1. Eliminar prefijos conocidos
            tarea_lower = tarea.lower()
            for prefijo in config.get("prefijos_eliminar", []):
                if tarea_lower.startswith(prefijo.lower()):
                    tarea = tarea[len(prefijo):].strip()
                    tarea_lower = tarea.lower()

            # 2. Aplicar patrones regex
            for patron_info in config.get("patrones_regex_eliminar", []):
                patron = patron_info.get("patron", "")
                if patron:
                    try:
                        tarea = re.sub(patron, "", tarea).strip()
                    except re.error:
                        pass

            # 3. Aplicar reemplazos
            for reemplazo_info in config.get("reemplazos", []):
                buscar = reemplazo_info.get("buscar", "")
                reemplazo = reemplazo_info.get("reemplazo", "")
                if buscar:
                    tarea = tarea.replace(buscar, reemplazo)

            # 4. Validar longitud minima
            min_len = config.get("min_longitud_tarea", 5)
            if len(tarea) >= min_len:
                tareas_limpias.append(tarea.strip())

        # Limitar cantidad
        max_tareas = config.get("max_tareas", 10)
        tareas_limpias = tareas_limpias[:max_tareas]

        if tareas_limpias:
            nuevo_valor = "; ".join(tareas_limpias)
            if nuevo_valor != tareas:
                data["tareas_explicitas"] = nuevo_valor
                self.stats["tareas_limpiadas"] = self.stats.get("tareas_limpiadas", 0) + 1
                if self.verbose:
                    print(f"[TAREAS] Limpiado: '{tareas[:50]}' -> '{nuevo_valor[:50]}'")

        return data

    # =========================================================================
    # PASO 4e: LIMPIEZA SKILLS (JSON a texto, deduplicar, normalizar)
    # =========================================================================

    def _limpiar_skills(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia skills_tecnicas_list y soft_skills_list:
        - Convierte JSON a texto plano
        - Elimina prefijos [regex], [llm]
        - Deduplica y normaliza variantes
        """
        config = self.configs.get("inference_rules", {}).get("limpieza_skills", {})
        if not config:
            return data

        campos_skills = ["skills_tecnicas_list", "soft_skills_list"]

        for campo in campos_skills:
            valor = data.get(campo)
            if not valor:
                continue

            skills_limpias = []
            skills_vistas = set()  # Para deduplicar

            # Intentar parsear como JSON
            try:
                if isinstance(valor, str) and valor.startswith("["):
                    lista = json.loads(valor)
                elif isinstance(valor, list):
                    lista = valor
                else:
                    # Ya es texto, separar por comas
                    lista = [s.strip() for s in valor.split(",")]
            except json.JSONDecodeError:
                # Si falla, tratar como texto separado por comas
                lista = [s.strip() for s in valor.split(",")]

            # Procesar cada skill
            for item in lista:
                skill = None

                if isinstance(item, dict):
                    # Extraer valor del objeto JSON
                    skill = item.get("valor") or item.get("texto_original") or ""
                elif isinstance(item, str):
                    skill = item
                else:
                    continue

                if not skill:
                    continue

                # Eliminar prefijos
                for prefijo in config.get("prefijos_eliminar", []):
                    skill = skill.replace(prefijo, "").strip()

                # Validar longitud minima
                min_len = config.get("min_longitud_skill", 2)
                if len(skill) < min_len:
                    continue

                # Normalizar duplicados
                skill_lower = skill.lower().strip()
                normalizacion = config.get("normalizacion_duplicados", {})

                skill_normalizada = skill_lower
                for forma_canonica, variantes in normalizacion.items():
                    if skill_lower in [v.lower() for v in variantes] or skill_lower == forma_canonica:
                        skill_normalizada = forma_canonica
                        break

                # Deduplicar
                if skill_normalizada not in skills_vistas:
                    skills_vistas.add(skill_normalizada)
                    # Usar la forma original si no fue normalizada, sino la canonica
                    if skill_normalizada != skill_lower:
                        skills_limpias.append(skill_normalizada)
                    else:
                        skills_limpias.append(skill.strip())

            # Limitar cantidad
            max_skills = config.get("max_skills", 15)
            skills_limpias = skills_limpias[:max_skills]

            if skills_limpias:
                separador = config.get("separador_salida", ", ")
                nuevo_valor = separador.join(skills_limpias)
                if nuevo_valor != valor:
                    data[campo] = nuevo_valor
                    self.stats["skills_limpiadas"] = self.stats.get("skills_limpiadas", 0) + 1
                    if self.verbose:
                        print(f"[SKILLS] {campo}: limpiado ({len(skills_limpias)} skills)")

        return data

    def _merge_tools_digitales(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusiona tecnologias_list + herramientas_list en tools_digitales_list

        Creado para análisis de brecha digital donde la distinción
        entre tecnologías y herramientas no es relevante.
        """
        tecnologias = data.get("tecnologias_list") or ""
        herramientas = data.get("herramientas_list") or ""

        # Parsear a listas
        def parse_to_list(valor):
            if not valor:
                return []
            if isinstance(valor, list):
                return valor
            if isinstance(valor, str):
                # Puede ser JSON o texto separado por comas
                try:
                    if valor.startswith("["):
                        return json.loads(valor)
                except json.JSONDecodeError:
                    pass
                # Separar por comas
                return [s.strip() for s in valor.split(",") if s.strip()]
            return []

        tec_list = parse_to_list(tecnologias)
        her_list = parse_to_list(herramientas)

        # Merge sin duplicados (case-insensitive)
        seen = set()
        merged = []

        for item in tec_list + her_list:
            # Extraer valor si es dict
            if isinstance(item, dict):
                valor = item.get("valor", "").strip()
            elif isinstance(item, str):
                valor = item.strip()
            else:
                continue

            if not valor:
                continue

            if valor.lower() not in seen:
                seen.add(valor.lower())
                merged.append(valor)

        # Guardar como string separado por comas (consistente con otros campos)
        if merged:
            data["tools_digitales_list"] = ", ".join(merged)
            if self.verbose:
                print(f"[TOOLS] Merge: {len(merged)} tools digitales")
        else:
            data["tools_digitales_list"] = ""

        return data

    # =========================================================================
    # PASO 5: NORMALIZACION
    # =========================================================================

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza valores (Capital Federal -> CABA, etc.)
        """
        config = self.configs.get("normalization", {})

        # =====================================================================
        # PRIMERO: Correccion de ubicacion (ANTES de mapeos simples)
        # Esto permite que "Capital Federal" en localidad se convierta a CABA
        # =====================================================================

        correccion_config = config.get("correccion_ubicacion", {})
        reglas_ubicacion = correccion_config.get("reglas", [])
        barrios_caba = set(correccion_config.get("barrios_caba", []))

        # GAP-2: Limpiar sufijos de localidad primero
        localidad_config = config.get("localidad", {})
        sufijos = localidad_config.get("limpiar_sufijos", [])

        localidad = data.get("localidad")
        if localidad and isinstance(localidad, str):
            for sufijo in sufijos:
                if localidad.endswith(sufijo):
                    localidad = localidad[:-len(sufijo)].strip()
                    data["localidad"] = localidad
                    self.stats["campos_normalizados"] += 1
                    if self.verbose:
                        print(f"[NORM] localidad: quitado sufijo '{sufijo}'")
                    break

        # GAP-1: Aplicar reglas de correccion_ubicacion
        for regla in reglas_ubicacion:
            condicion = regla.get("condicion", {})
            accion = regla.get("accion", {})

            match = True

            # Evaluar condicion
            if "localidad" in condicion:
                if data.get("localidad") != condicion["localidad"]:
                    match = False

            if "provincia" in condicion:
                if data.get("provincia") != condicion["provincia"]:
                    match = False

            if "localidad_contiene" in condicion:
                loc = data.get("localidad") or ""
                if condicion["localidad_contiene"] not in loc:
                    match = False

            # Aplicar accion si matchea
            if match:
                for campo_acc, valor_acc in accion.items():
                    if campo_acc == "localidad_limpiar_sufijo":
                        loc = data.get("localidad") or ""
                        if loc.endswith(valor_acc):
                            data["localidad"] = loc[:-len(valor_acc)].strip()
                    else:
                        data[campo_acc] = valor_acc
                    self.stats["campos_normalizados"] += 1
                    if self.verbose:
                        print(f"[NORM] Regla ubicacion: {campo_acc} = {valor_acc}")
                break

        # GAP-1 adicional: Si localidad es barrio de CABA y provincia != CABA
        localidad_actual = data.get("localidad")
        provincia_actual = data.get("provincia")

        if localidad_actual and localidad_actual in barrios_caba:
            if provincia_actual != "CABA":
                data["provincia"] = "CABA"
                self.stats["campos_normalizados"] += 1
                if self.verbose:
                    print(f"[NORM] Barrio CABA detectado: provincia -> CABA")

        # =====================================================================
        # SEGUNDO: Mapeos simples (provincia, modalidad, seniority, etc.)
        # =====================================================================

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

        # =====================================================================
        # GAP-4: Validar valores validos (al final, despues de todo lo demas)
        # =====================================================================
        # GAP-4: Validar valores validos
        for campo, campo_config in config.items():
            if campo.startswith("_"):
                continue

            valores_validos = campo_config.get("valores_validos", [])
            if valores_validos:
                valor_actual = data.get(campo)
                if valor_actual and valor_actual not in valores_validos:
                    # Valor no valido, dejarlo null para que se infiera
                    if self.verbose:
                        print(f"[NORM] {campo}='{valor_actual}' no en valores_validos -> null")
                    data[campo] = None

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
                    skills_regex: Dict[str, List[str]] = None,
                    id_empresa: str = None) -> Dict[str, Any]:
        """
        Aplica todas las correcciones post-LLM

        Args:
            data: Dict con campos extraidos por el LLM
            descripcion: Texto original de la oferta
            skills_regex: Dict con skills_tecnicas_regex y soft_skills_regex de Capa 0
            id_empresa: ID de empresa del scraping (para lookup en catálogo)

        Returns:
            Dict con campos corregidos
        """
        # Guardar id_empresa para usarlo en _extract_sector
        self._current_id_empresa = id_empresa
        # Reset stats
        for key in self.stats:
            self.stats[key] = 0

        # Paso 2: Validacion de tipos
        data = self._validate_types(data)

        # Paso 2b: Validacion campos categoricos (Matching v2.1.1)
        data = self._validate_categoricos(data)

        # Paso 3: Re-extraccion experiencia
        data = self._extract_experiencia(descripcion, data)

        # Paso 4: Inferencia
        data = self._infer_fields(descripcion, data)

        # Paso 4a: Correccion "sin experiencia" (detectar frases que indican exp=0)
        data = self._corregir_sin_experiencia(descripcion, data)

        # Paso 4a2: Forzar seniority por titulo (prioridad maxima)
        data = self._forzar_seniority_por_titulo(data)

        # Paso 4a3: Correccion seniority (si inconsistente con experiencia)
        data = self._corregir_seniority(data)

        # Paso 4b: Extraccion tareas explicitas (si LLM no detecto)
        data = self._extract_tareas(descripcion, data)

        # Paso 4b2: Completar tareas (si LLM extrajo incompletas)
        data = self._completar_tareas(descripcion, data)

        # Paso 4b3: Extraer tareas implicitas (texto no estructurado)
        data = self._extraer_tareas_implicitas(descripcion, data)

        # Paso 4c: Extraccion sector empresa (si LLM no detecto)
        # Incluye lookup en catálogo de empresas para alta confianza
        data = self._extract_sector(descripcion, data, self._current_id_empresa)

        # Paso 4c2: Correccion sector (si LLM clasifico mal)
        data = self._corregir_sector(data, descripcion)

        # Paso 4c3: Clasificacion CLAE (sector -> codigo oficial)
        titulo_limpio = data.get("titulo_limpio", "")
        data = self._classify_clae(data, titulo_limpio, descripcion)

        # Paso 4d: Limpieza tareas (prefijos, bullets, etc.)
        data = self._limpiar_tareas(data)

        # Paso 5: Normalizacion
        data = self._normalize(data)

        # Paso 6: Merge skills regex (NUEVO v1.1)
        if skills_regex:
            data = self._merge_skills_regex(data, skills_regex)

        # Paso 7: Limpieza skills (JSON a texto, deduplicar) - DESPUES de merge
        data = self._limpiar_skills(data)

        # Paso 7b: Merge tools digitales (tecnologias + herramientas)
        data = self._merge_tools_digitales(data)

        # Paso 8: Defaults
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

        # Merge: campos de ubicacion del scraping tienen prioridad absoluta
        # porque vienen de datos estructurados, no inferidos del texto
        campos_prioridad_scraping = {"localidad", "provincia"}

        # Normalizar modalidad del scraping antes de mergear
        if "modalidad" in pre_data and pre_data["modalidad"]:
            modalidad_config = self.configs.get("normalization", {}).get("modalidad", {})
            mapeo = modalidad_config.get("mapeo", {})
            valor_original = pre_data["modalidad"]
            pre_data["modalidad"] = mapeo.get(valor_original, valor_original.lower())
            if self.verbose and pre_data["modalidad"] != valor_original:
                print(f"[PREPROC] modalidad: '{valor_original}' -> '{pre_data['modalidad']}' (normalizado)")

        for campo, valor in pre_data.items():
            if valor is not None:
                if campo in campos_prioridad_scraping:
                    # Ubicacion del scraping SIEMPRE tiene prioridad
                    if post_data.get(campo) != valor and self.verbose:
                        print(f"[MERGE] {campo}: '{post_data.get(campo)}' -> '{valor}' (prioridad scraping)")
                    post_data[campo] = valor
                elif post_data.get(campo) is None:
                    # Otros campos: solo si LLM no extrajo
                    post_data[campo] = valor
                    if self.verbose:
                        print(f"[MERGE] {campo}: '{valor}' (de scraping, LLM no extrajo)")

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
