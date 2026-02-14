"""
Auto-corrector del pipeline MOL.
Aplica correcciones automaticas y escala a Claude cuando necesario.

Version: 1.1
Fecha: 2026-02-08

Cambios v1.1:
- Funcion normalizar_ubicacion: aplica normalization config a provincia/localidad
- Funcion reinferir_campo: re-evalua inference rules para seniority/area/modalidad
- Funcion normalizar_formato_tareas: convierte separador comas a punto y coma (V26)
- Verificacion post-correccion: re-evalua regla antes de marcar corregido=1
- Helper _cargar_oferta(): recarga oferta con query expandida completa

Uso:
    from database.auto_corrector import AutoCorrector

    corrector = AutoCorrector(db_conn)
    resultado = corrector.procesar_errores(errores_validacion)
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class AutoCorrector:
    """Corrector automatico basado en auto_correction_map.json."""

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None, config_dir: Optional[Path] = None,
                 validator=None):
        """
        Inicializa el corrector.

        Args:
            db_conn: Conexion a la base de datos SQLite
            config_dir: Directorio de configs. Default: config/
            validator: Validador externo para verificar correcciones.
                       Si None, usa AutoValidator (matching).
                       Pasar NLPValidator para correcciones pre-matching.
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.db_conn = db_conn
        self._external_validator = validator

        # Cargar configs
        self.correction_map = self._load_json("auto_correction_map.json")
        self.diagnostic_patterns = self._load_json("diagnostic_patterns.json")

        # Cola de errores para Claude
        self.cola_claude = defaultdict(list)

        # Historial de correcciones
        self.correcciones_aplicadas = []

    def _load_json(self, filename: str) -> Dict:
        """Carga un archivo JSON de config."""
        path = self.config_dir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def procesar_errores(self, resultados_validacion: Dict) -> Dict[str, Any]:
        """
        Procesa errores de validacion y aplica correcciones.

        Args:
            resultados_validacion: Output de AutoValidator.validar_lote()

        Returns:
            Diccionario con:
            - auto_corregidos: Ofertas corregidas automaticamente
            - escalados_claude: Ofertas que requieren analisis de Claude
            - sin_accion: Ofertas sin accion disponible
            - correcciones_detalle: Detalle de cada correccion
        """
        resultado = {
            "auto_corregidos": [],
            "escalados_claude": [],
            "sin_accion": [],
            "correcciones_detalle": [],
            "timestamp": datetime.now().isoformat()
        }

        errores_detalle = resultados_validacion.get("errores_detalle", [])

        for item in errores_detalle:
            id_oferta = item["id_oferta"]

            for error in item["errores"]:
                diagnostico = error.get("diagnostico")
                correccion_config = self.correction_map.get("correcciones", {}).get(diagnostico)

                if not correccion_config:
                    resultado["sin_accion"].append({
                        "id_oferta": id_oferta,
                        "diagnostico": diagnostico,
                        "motivo": "No hay config de correccion definido"
                    })
                    continue

                tipo_accion = correccion_config.get("tipo_accion")

                if tipo_accion == "auto_corregir":
                    # Aplicar correccion automatica
                    exito = self._aplicar_auto_correccion(id_oferta, error, correccion_config)
                    if exito:
                        resultado["auto_corregidos"].append(id_oferta)
                        resultado["correcciones_detalle"].append({
                            "id_oferta": id_oferta,
                            "tipo": "auto_corregido",
                            "diagnostico": diagnostico,
                            "accion": correccion_config.get("descripcion")
                        })
                    else:
                        resultado["sin_accion"].append({
                            "id_oferta": id_oferta,
                            "diagnostico": diagnostico,
                            "motivo": "Error al aplicar auto-correccion"
                        })

                elif tipo_accion == "aplicar_config":
                    # Buscar config existente o escalar
                    config_existe = self._buscar_config_existente(error, correccion_config)
                    if config_existe:
                        # Marcar para reprocesamiento
                        resultado["correcciones_detalle"].append({
                            "id_oferta": id_oferta,
                            "tipo": "reprocesar",
                            "diagnostico": diagnostico,
                            "config": correccion_config.get("config"),
                            "accion": "Reprocesar con config existente"
                        })
                    else:
                        # Escalar a Claude
                        self._agregar_a_cola_claude(id_oferta, error, correccion_config)
                        resultado["escalados_claude"].append(id_oferta)

                elif tipo_accion == "escalar_claude":
                    # Siempre escalar a Claude
                    self._agregar_a_cola_claude(id_oferta, error, correccion_config)
                    resultado["escalados_claude"].append(id_oferta)

        # Agrupar errores para Claude
        resultado["patrones_para_claude"] = self._generar_patrones_claude()

        return resultado

    def _aplicar_auto_correccion(self, id_oferta: str, error: Dict, config: Dict) -> bool:
        """
        Aplica una correccion automatica a la BD.

        Args:
            id_oferta: ID de la oferta
            error: Error detectado
            config: Config de correccion

        Returns:
            True si se aplico correctamente
        """
        if not self.db_conn:
            return False

        ejecutar = config.get("ejecutar", {})
        funcion = ejecutar.get("funcion")

        try:
            if funcion == "set_campo":
                campo = ejecutar.get("campo")
                valor_template = ejecutar.get("valor_template", ejecutar.get("valor"))

                # Expandir template si es necesario
                if "{" in str(valor_template):
                    # Obtener datos de la oferta para expandir template
                    cursor = self.db_conn.execute(
                        "SELECT localidad FROM ofertas_nlp WHERE id_oferta = ?",
                        (id_oferta,)
                    )
                    row = cursor.fetchone()
                    if row:
                        localidad = row[0] or ""
                        # Detectar pais
                        paises = {
                            "Paraguay": "Paraguay",
                            "Asuncion": "Paraguay",
                            "Asunción": "Paraguay",
                            "Uruguay": "Uruguay",
                            "Montevideo": "Uruguay",
                            "Chile": "Chile",
                            "Santiago": "Chile"
                        }
                        pais_detectado = "Exterior"
                        for patron, pais in paises.items():
                            if patron.lower() in localidad.lower():
                                pais_detectado = pais
                                break
                        valor = valor_template.replace("{pais_detectado}", pais_detectado)
                    else:
                        valor = valor_template
                else:
                    valor = valor_template

                # Actualizar BD
                self.db_conn.execute(
                    f"UPDATE ofertas_nlp SET {campo} = ? WHERE id_oferta = ?",
                    (valor, id_oferta)
                )
                self.db_conn.commit()

                self.correcciones_aplicadas.append({
                    "id_oferta": id_oferta,
                    "campo": campo,
                    "valor_nuevo": valor,
                    "timestamp": datetime.now().isoformat()
                })

                # Verificar que la corrección resolvió el error
                return self._verificar_correccion(id_oferta, error.get("id_regla"))

            elif funcion == "limpiar_booleanos":
                campos = ejecutar.get("campos", [])
                valores_invalidos = ejecutar.get("valores_invalidos", [])

                for campo in campos:
                    cursor = self.db_conn.execute(
                        f"SELECT {campo} FROM ofertas_nlp WHERE id_oferta = ?",
                        (id_oferta,)
                    )
                    row = cursor.fetchone()
                    if row and row[0] in valores_invalidos:
                        self.db_conn.execute(
                            f"UPDATE ofertas_nlp SET {campo} = NULL WHERE id_oferta = ?",
                            (id_oferta,)
                        )

                self.db_conn.commit()

                # Verificar que la corrección resolvió el error
                return self._verificar_correccion(id_oferta, error.get("id_regla"))

            elif funcion == "normalizar_ubicacion":
                return self._normalizar_ubicacion(id_oferta, error)

            elif funcion == "reinferir_campo":
                campo_target = ejecutar.get("campo")
                return self._reinferir_campo(id_oferta, campo_target)

            elif funcion == "normalizar_formato_tareas":
                return self._normalizar_formato_tareas(id_oferta, error)

        except Exception as e:
            print(f"Error aplicando auto-correccion a {id_oferta}: {e}")
            return False

        return False

    def _normalizar_ubicacion(self, id_oferta: str, error: Dict) -> bool:
        """
        Normaliza provincia/localidad usando config/nlp_normalization.json.

        Aplica mapeos de normalización (CABA -> Capital Federal, etc.)
        e infiere provincia desde localidad cuando falta.
        """
        normalization = self._load_json("nlp_normalization.json")
        if not normalization:
            return False

        cursor = self.db_conn.execute(
            "SELECT provincia, localidad FROM ofertas_nlp WHERE id_oferta = ?",
            (id_oferta,)
        )
        row = cursor.fetchone()
        if not row:
            return False

        provincia, localidad = row[0], row[1]
        cambios = {}

        # 1. Normalizar provincia con mapeo
        prov_mapeo = normalization.get("provincia", {}).get("mapeo", {})
        if provincia and provincia in prov_mapeo:
            cambios["provincia"] = prov_mapeo[provincia]

        # 2. Normalizar localidad con mapeo
        loc_mapeo = normalization.get("localidad", {}).get("mapeo", {})
        if localidad and localidad in loc_mapeo:
            cambios["localidad"] = loc_mapeo[localidad]

        # 3. Inferir provincia desde localidad si falta
        if not provincia and localidad:
            prov_desde_loc = normalization.get("provincia_desde_localidad", {})
            # Buscar en reglas
            for regla in prov_desde_loc.get("reglas", []):
                localidades_match = regla.get("localidades", [])
                if localidad.lower() in [l.lower() for l in localidades_match]:
                    cambios["provincia"] = regla.get("provincia")
                    break

        # 4. Aplicar reglas de corrección ubicación
        for regla in normalization.get("correccion_ubicacion", {}).get("reglas", []):
            condicion = regla.get("condicion", {})
            matches = True
            for campo, valor_esperado in condicion.items():
                actual = provincia if campo == "provincia" else localidad
                if actual != valor_esperado:
                    matches = False
                    break
            if matches:
                accion = regla.get("accion", {})
                cambios.update(accion)
                break

        if not cambios:
            return False

        # Aplicar cambios
        for campo, valor in cambios.items():
            self.db_conn.execute(
                f"UPDATE ofertas_nlp SET {campo} = ? WHERE id_oferta = ?",
                (valor, id_oferta)
            )
        self.db_conn.commit()

        self.correcciones_aplicadas.append({
            "id_oferta": id_oferta,
            "campo": "ubicacion",
            "cambios": cambios,
            "timestamp": datetime.now().isoformat()
        })
        return self._verificar_correccion(id_oferta, error.get("id_regla"))

    def _reinferir_campo(self, id_oferta: str, campo: str) -> bool:
        """
        Re-evalúa inference rules para un campo específico (seniority, area, modalidad).

        Lee titulo_limpio y evalúa keywords contra reglas de nlp_inference_rules.json.
        """
        inference_rules = self._load_json("nlp_inference_rules.json")
        if not inference_rules or campo not in inference_rules:
            return False

        cursor = self.db_conn.execute(
            "SELECT titulo_limpio FROM ofertas_nlp WHERE id_oferta = ?",
            (id_oferta,)
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False

        titulo = row[0].lower()
        seccion = inference_rules[campo]

        # Evaluar reglas por keywords
        valor_inferido = None

        # Patron 1: reglas con contiene_cualquiera
        for regla in seccion.get("reglas", []):
            keywords = regla.get("contiene_cualquiera", [])
            if any(kw.lower() in titulo for kw in keywords):
                valor_inferido = regla.get("resultado")
                break

        # Patron 2: diccionario_keywords (para area_funcional)
        if not valor_inferido and "diccionario_keywords" in seccion:
            for area, keywords in seccion["diccionario_keywords"].items():
                if any(kw.lower() in titulo for kw in keywords):
                    valor_inferido = area
                    break

        # Patron 3: prioridad_por_titulo (para area_funcional)
        if not valor_inferido:
            for regla in seccion.get("prioridad_por_titulo", []):
                keywords = regla.get("titulo_contiene_alguno", [])
                if any(kw.lower() in titulo for kw in keywords):
                    valor_inferido = regla.get("forzar_area", regla.get("resultado"))
                    break

        if not valor_inferido:
            return False

        # Actualizar BD
        col_name = {
            "nivel_seniority": "nivel_seniority",
            "area_funcional": "area_funcional",
            "modalidad": "modalidad"
        }.get(campo, campo)

        self.db_conn.execute(
            f"UPDATE ofertas_nlp SET {col_name} = ? WHERE id_oferta = ?",
            (valor_inferido, id_oferta)
        )
        self.db_conn.commit()

        self.correcciones_aplicadas.append({
            "id_oferta": id_oferta,
            "campo": col_name,
            "valor_nuevo": valor_inferido,
            "timestamp": datetime.now().isoformat()
        })
        return True

    def _normalizar_formato_tareas(self, id_oferta: str, error: Dict) -> bool:
        """
        Normaliza separador de tareas de comas a punto y coma (V26).

        Reemplaza ', ' por '; ' en tareas_explicitas.
        """
        cursor = self.db_conn.execute(
            "SELECT tareas_explicitas FROM ofertas_nlp WHERE id_oferta = ?",
            (id_oferta,)
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return False

        tareas = row[0]
        # Solo normalizar si tiene comas pero no punto y coma
        if "," in tareas and ";" not in tareas:
            tareas_normalizado = tareas.replace(", ", "; ")
            self.db_conn.execute(
                "UPDATE ofertas_nlp SET tareas_explicitas = ? WHERE id_oferta = ?",
                (tareas_normalizado, id_oferta)
            )
            self.db_conn.commit()

            self.correcciones_aplicadas.append({
                "id_oferta": id_oferta,
                "campo": "tareas_explicitas",
                "valor_nuevo": tareas_normalizado[:100] + "...",
                "timestamp": datetime.now().isoformat()
            })
            return self._verificar_correccion(id_oferta, error.get("id_regla"))

        return False

    def _marcar_error_corregido(self, id_oferta: str, error_id: str):
        """
        Marca un error como corregido en la tabla validation_errors.

        Args:
            id_oferta: ID de la oferta
            error_id: ID del error (ej: V02_isco_nulo_score_bajo)
        """
        if not self.db_conn:
            return

        try:
            self.db_conn.execute('''
                UPDATE validation_errors
                SET corregido = 1,
                    corregido_timestamp = ?,
                    corregido_metodo = 'auto',
                    resuelto = 1
                WHERE id_oferta = ? AND error_id = ? AND corregido = 0
            ''', (datetime.now().isoformat(), str(id_oferta), error_id))
            self.db_conn.commit()
        except Exception as e:
            print(f"  WARN: Error actualizando validation_errors para {id_oferta}: {e}")

    def _marcar_error_escalado(self, id_oferta: str, error_id: str):
        """
        Marca un error como escalado a Claude en la tabla validation_errors.

        Args:
            id_oferta: ID de la oferta
            error_id: ID del error
        """
        if not self.db_conn:
            return

        try:
            self.db_conn.execute('''
                UPDATE validation_errors
                SET escalado_claude = 1
                WHERE id_oferta = ? AND error_id = ? AND escalado_claude = 0
            ''', (str(id_oferta), error_id))
            self.db_conn.commit()
        except Exception as e:
            print(f"  WARN: Error actualizando escalado_claude para {id_oferta}: {e}")

    def _verificar_correccion(self, id_oferta: str, error_id: str) -> bool:
        """
        Despues de aplicar correccion, re-evalua la regla que detecto el error.
        Solo marca corregido=1 si la regla YA NO dispara.

        Usa el validador externo si fue provisto (NLPValidator para errores NLP,
        AutoValidator para errores matching).

        Args:
            id_oferta: ID de la oferta
            error_id: ID de la regla de validacion (ej: V26_formato_tareas_incorrecto)

        Returns:
            True si la correccion resolvio el error
        """
        if self._external_validator:
            # Usar validador externo (NLPValidator)
            oferta = self._cargar_oferta_nlp(id_oferta)
            if not oferta:
                self._marcar_error_corregido(id_oferta, error_id)
                return True
            result = self._external_validator.validar_oferta(oferta)
            errores = result.get("errores", [])
        else:
            # Usar AutoValidator (matching) - comportamiento original
            from database.auto_validator import AutoValidator
            oferta = self._cargar_oferta(id_oferta)
            if not oferta:
                self._marcar_error_corregido(id_oferta, error_id)
                return True
            validator = AutoValidator(config_dir=self.config_dir)
            errores = validator.validar_oferta(oferta)

        error_resuelto = not any(e.get('id_regla') == error_id for e in errores)

        if error_resuelto:
            self._marcar_error_corregido(id_oferta, error_id)
            return True
        else:
            try:
                self.db_conn.execute('''
                    UPDATE validation_errors
                    SET notas = COALESCE(notas, '') || ' | Correccion fallida'
                    WHERE id_oferta = ? AND error_id = ? AND corregido = 0
                ''', (str(id_oferta), error_id))
                self.db_conn.commit()
            except Exception as e:
                print(f"  WARN: Error actualizando notas para {id_oferta}: {e}")
            return False

    def _cargar_oferta(self, id_oferta: str) -> Optional[Dict]:
        """
        Recarga una oferta desde BD con la misma query expandida del validador.

        Args:
            id_oferta: ID de la oferta

        Returns:
            Dict con datos de la oferta o None si no encontrada
        """
        if not self.db_conn:
            return None

        try:
            self.db_conn.row_factory = sqlite3.Row
            cursor = self.db_conn.execute("""
                SELECT
                    m.id_oferta,
                    o.titulo,
                    n.titulo_limpio,
                    n.provincia,
                    n.localidad,
                    n.sector_empresa,
                    n.sector_confianza,
                    n.sector_fuente,
                    n.es_intermediario,
                    n.clae_code,
                    n.clae_grupo,
                    n.clae_seccion,
                    n.area_funcional,
                    n.nivel_seniority,
                    n.modalidad,
                    n.experiencia_min_anios,
                    n.experiencia_max_anios,
                    n.tareas_explicitas,
                    n.tareas_inferidas,
                    m.isco_code,
                    m.esco_occupation_label as esco_label,
                    m.occupation_match_score as match_score,
                    (SELECT COUNT(*) FROM ofertas_esco_skills_detalle s WHERE s.id_oferta = m.id_oferta) as skills_count,
                    m.dual_coinciden,
                    m.isco_regla,
                    m.isco_semantico,
                    m.score_semantico,
                    m.regla_aplicada,
                    m.decision_metodo,
                    m.skills_matched_essential,
                    m.skills_semantico_json,
                    m.skills_regla_json,
                    m.skills_demandados_total,
                    m.skills_matcheados_esco,
                    m.skills_oferta_json,
                    m.esco_occupation_uri,
                    LENGTH(COALESCE(n.tareas_explicitas, '')) as tareas_explicitas_length,
                    LENGTH(COALESCE(n.tareas_inferidas, '')) as tareas_inferidas_length,
                    (SELECT COUNT(*) FROM esco_associations ea
                     WHERE ea.occupation_uri = m.esco_occupation_uri
                     AND ea.relation_type = 'essential') as occupation_essential_total
                FROM ofertas_esco_matching m
                LEFT JOIN ofertas o ON o.id_oferta = m.id_oferta
                LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
                WHERE m.id_oferta = ?
            """, (id_oferta,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"  WARN: Error cargando oferta {id_oferta}: {e}")
            return None

    def _cargar_oferta_nlp(self, id_oferta: str) -> Optional[Dict]:
        """
        Recarga una oferta desde BD con datos NLP (sin matching).
        Se usa cuando el corrector trabaja con NLPValidator.

        Args:
            id_oferta: ID de la oferta

        Returns:
            Dict con datos NLP de la oferta o None
        """
        if not self.db_conn:
            return None

        try:
            self.db_conn.row_factory = sqlite3.Row
            cursor = self.db_conn.execute("""
                SELECT
                    n.id_oferta,
                    n.titulo_limpio,
                    n.provincia,
                    n.localidad,
                    n.sector_empresa,
                    n.sector_confianza,
                    n.sector_fuente,
                    n.es_intermediario,
                    n.clae_code,
                    n.clae_grupo,
                    n.clae_seccion,
                    n.area_funcional,
                    n.nivel_seniority,
                    n.modalidad,
                    n.tipo_oferta,
                    n.tareas_explicitas,
                    n.tareas_inferidas,
                    n.tiene_gente_cargo,
                    n.skills_tecnicas_list,
                    n.largo_descripcion,
                    LENGTH(COALESCE(n.tareas_explicitas, '')) as tareas_explicitas_length,
                    o.titulo,
                    o.empresa
                FROM ofertas_nlp n
                LEFT JOIN ofertas o ON CAST(n.id_oferta AS INTEGER) = o.id_oferta
                WHERE n.id_oferta = ?
            """, (id_oferta,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"  WARN: Error cargando oferta NLP {id_oferta}: {e}")
            return None

    def _buscar_config_existente(self, error: Dict, config: Dict) -> bool:
        """
        Busca si existe una regla aplicable en el config indicado.

        Args:
            error: Error detectado
            config: Config de correccion con ruta al archivo

        Returns:
            True si existe una regla aplicable
        """
        config_path = self.config_dir.parent / config.get("config", "")
        if not config_path.exists():
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            seccion = config.get("buscar_en", "")
            # Navegar a la seccion
            parts = seccion.split(".")
            data = config_data
            for part in parts:
                if isinstance(data, dict) and part in data:
                    data = data[part]
                else:
                    return False

            # Verificar si hay reglas (simplificado)
            if isinstance(data, list) and len(data) > 0:
                return True

        except Exception:
            pass

        return False

    def _agregar_a_cola_claude(self, id_oferta: str, error: Dict, config: Dict):
        """
        Agrega un error a la cola para analisis de Claude.

        Args:
            id_oferta: ID de la oferta
            error: Error detectado
            config: Config de correccion
        """
        diagnostico = error.get("diagnostico")

        # Obtener datos adicionales si es necesario
        datos = {
            "id_oferta": id_oferta,
            "diagnostico": diagnostico,
            "campo": error.get("campo"),
            "mensaje": error.get("mensaje"),
            "config_afectado": config.get("config"),
            "timestamp": datetime.now().isoformat()
        }

        # Agregar datos extra de la oferta si tenemos conexion BD
        if self.db_conn:
            try:
                cursor = self.db_conn.execute("""
                    SELECT
                        n.titulo_limpio,
                        n.area_funcional,
                        n.nivel_seniority,
                        n.sector_empresa,
                        m.isco_code,
                        m.esco_occupation_label,
                        m.occupation_match_score
                    FROM ofertas_nlp n
                    LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
                    WHERE n.id_oferta = ?
                """, (id_oferta,))
                row = cursor.fetchone()
                if row:
                    datos.update({
                        "titulo_limpio": row[0],
                        "area_funcional": row[1],
                        "nivel_seniority": row[2],
                        "sector_empresa": row[3],
                        "isco_code": row[4],
                        "esco_label": row[5],
                        "match_score": row[6]
                    })
            except Exception:
                pass

        self.cola_claude[diagnostico].append(datos)

        # Marcar como escalado en validation_errors
        self._marcar_error_escalado(id_oferta, error.get("id_regla"))

    def _generar_patrones_claude(self) -> List[Dict]:
        """
        Genera patrones agrupados para presentar a Claude.

        Returns:
            Lista de patrones con ejemplos agrupados
        """
        umbral = self.correction_map.get("umbrales_escalamiento", {}).get("minimo_casos_para_patron", 3)
        patrones = []

        for diagnostico, casos in self.cola_claude.items():
            if len(casos) >= umbral:
                # Agrupar por similitud
                patron = {
                    "diagnostico": diagnostico,
                    "cantidad": len(casos),
                    "ejemplos": casos[:5],  # Max 5 ejemplos
                    "ids": [c["id_oferta"] for c in casos],
                    "config_afectado": casos[0].get("config_afectado") if casos else None,
                    "accion_requerida": f"Crear regla para resolver {len(casos)} casos de {diagnostico}"
                }
                patrones.append(patron)

        return sorted(patrones, key=lambda x: x["cantidad"], reverse=True)

    def obtener_reporte_claude(self) -> str:
        """
        Genera reporte formateado para Claude.

        Returns:
            Texto con patrones agrupados listo para presentar
        """
        patrones = self._generar_patrones_claude()

        if not patrones:
            return "No hay errores que requieran intervencion de Claude."

        lineas = [
            "="*60,
            "PATRONES PARA ANALISIS DE CLAUDE",
            "="*60,
            ""
        ]

        for i, patron in enumerate(patrones, 1):
            lineas.append(f"## PATRON {i}: {patron['diagnostico']}")
            lineas.append(f"   Cantidad: {patron['cantidad']} ofertas")
            lineas.append(f"   Config: {patron['config_afectado']}")
            lineas.append("")
            lineas.append("   Ejemplos:")

            for ej in patron["ejemplos"][:3]:
                lineas.append(f"   - ID {ej['id_oferta']}: {ej.get('titulo_limpio', 'N/A')}")
                if ej.get("isco_code"):
                    lineas.append(f"     ISCO actual: {ej['isco_code']} - {ej.get('esco_label', '')}")

            lineas.append("")
            lineas.append(f"   ACCION: {patron['accion_requerida']}")
            lineas.append("-"*60)
            lineas.append("")

        return "\n".join(lineas)

    def guardar_cola_claude(self, output_path: Optional[Path] = None) -> Path:
        """
        Guarda la cola de errores para Claude en un archivo JSON.

        Args:
            output_path: Path para guardar. Default: metrics/cola_claude_{timestamp}.json

        Returns:
            Path del archivo guardado
        """
        if output_path is None:
            metrics_dir = self.config_dir.parent / "metrics"
            metrics_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = metrics_dir / f"cola_claude_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "patrones": self._generar_patrones_claude(),
            "detalle_por_diagnostico": dict(self.cola_claude),
            "correcciones_aplicadas": self.correcciones_aplicadas
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path


def procesar_validacion_completa(db_path: str = None, limit: int = None, ids: List[str] = None) -> Dict:
    """
    Ejecuta validacion + correccion completa.

    Args:
        db_path: Path a la BD
        limit: Limite de ofertas
        ids: IDs especificos

    Returns:
        Resultados de validacion y correccion
    """
    from database.auto_validator import validar_ofertas_desde_bd

    # Paso 1: Validar
    print("Paso 1: Validando ofertas...")
    resultados_validacion = validar_ofertas_desde_bd(db_path=db_path, limit=limit, ids=ids)

    print(f"  - Total: {resultados_validacion['total']}")
    print(f"  - Con errores: {resultados_validacion['con_errores']}")

    if resultados_validacion['con_errores'] == 0:
        print("\nNo hay errores que corregir.")
        return {"validacion": resultados_validacion, "correccion": None}

    # Paso 2: Corregir
    print("\nPaso 2: Aplicando correcciones...")

    if db_path is None:
        db_path = str(Path(__file__).parent / "bumeran_scraping.db")

    conn = sqlite3.connect(db_path)
    corrector = AutoCorrector(db_conn=conn)

    resultados_correccion = corrector.procesar_errores(resultados_validacion)
    conn.close()

    print(f"  - Auto-corregidos: {len(resultados_correccion['auto_corregidos'])}")
    print(f"  - Escalados a Claude: {len(resultados_correccion['escalados_claude'])}")
    print(f"  - Sin accion: {len(resultados_correccion['sin_accion'])}")

    if resultados_correccion['patrones_para_claude']:
        print("\n" + corrector.obtener_reporte_claude())
        output_path = corrector.guardar_cola_claude()
        print(f"\nCola para Claude guardada en: {output_path}")

    return {
        "validacion": resultados_validacion,
        "correccion": resultados_correccion
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-corrector MOL")
    parser.add_argument("--limit", type=int, help="Limite de ofertas")
    parser.add_argument("--ids", help="IDs separados por coma")

    args = parser.parse_args()
    ids = args.ids.split(",") if args.ids else None

    resultados = procesar_validacion_completa(limit=args.limit, ids=ids)
