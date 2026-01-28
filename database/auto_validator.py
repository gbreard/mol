"""
Auto-validador del pipeline MOL.
Lee validation_rules.json y evalua ofertas automaticamente.

Version: 1.1
Fecha: 2026-01-28

Cambios v1.1:
- Validación automática de títulos usando patrones de nlp_titulo_limpieza.json
- Si un patrón de limpieza matchea en titulo_limpio, se detecta como error

Uso:
    from database.auto_validator import AutoValidator

    validator = AutoValidator()
    errores = validator.validar_oferta(oferta_dict)

    # O validar lote
    resultados = validator.validar_lote(lista_ofertas)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class AutoValidator:
    """Validador automatico basado en reglas JSON."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa el validador cargando configs.

        Args:
            config_dir: Directorio de configs. Default: config/
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"

        # Cargar configs
        self.validation_rules = self._load_json("validation_rules.json")
        self.diagnostic_patterns = self._load_json("diagnostic_patterns.json")
        self.correction_map = self._load_json("auto_correction_map.json")

        # Cargar patrones de limpieza de títulos (para validar que quedaron limpios)
        self.titulo_limpieza_config = self._load_json("nlp_titulo_limpieza.json")

        # Cache de reglas compiladas (regex)
        self._compiled_patterns = {}

        # Compilar patrones de limpieza de títulos
        self._titulo_patterns = self._compilar_patrones_titulo()

    def _load_json(self, filename: str) -> Dict:
        """Carga un archivo JSON de config."""
        path = self.config_dir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _compilar_patrones_titulo(self) -> List[Dict]:
        """
        Compila patrones de nlp_titulo_limpieza.json para validar títulos.

        Los mismos patrones que se usan para LIMPIAR el título,
        se usan para VALIDAR que quedó limpio. Si algún patrón
        matchea en titulo_limpio, significa que la limpieza falló.
        """
        patrones = []
        config = self.titulo_limpieza_config

        # Secciones que contienen patrones de ruido
        secciones_con_patrones = [
            'zonas_ubicaciones',
            'contexto_empresarial_sin_guion',
            'contexto_complejo',
            'parentesis_eliminar',
            'ubicacion_con_guion',
            'modalidad_guion',
            'codigos_final',
            'requisitos_edad',
            'ubicacion_guion_extendido',
            'codigos_empresa',
        ]

        for seccion in secciones_con_patrones:
            if seccion not in config:
                continue
            for patron_info in config[seccion].get('patrones', []):
                patron = patron_info.get('patron')
                if patron:
                    try:
                        compiled = re.compile(patron, re.IGNORECASE)
                        patrones.append({
                            'seccion': seccion,
                            'patron': patron,
                            'compiled': compiled,
                            'ejemplo': patron_info.get('ejemplo', '')
                        })
                    except re.error:
                        pass  # Ignorar patrones inválidos

        # Secciones con listas de palabras (convertir a patrones)
        if 'localidades_final' in config:
            for localidad in config['localidades_final'].get('lista', []):
                patron = rf'\s*[-–—]\s*{re.escape(localidad)}$'
                try:
                    compiled = re.compile(patron, re.IGNORECASE)
                    patrones.append({
                        'seccion': 'localidades_final',
                        'patron': patron,
                        'compiled': compiled,
                        'ejemplo': f'- {localidad}'
                    })
                except re.error:
                    pass

        return patrones

    def _validar_titulo_limpio(self, titulo_limpio: str) -> List[Dict]:
        """
        Valida que el título realmente quedó limpio.

        Usa los patrones de nlp_titulo_limpieza.json.
        Si alguno matchea, significa que la limpieza falló.

        Returns:
            Lista de errores encontrados
        """
        if not titulo_limpio:
            return []

        errores = []
        for patron_info in self._titulo_patterns:
            if patron_info['compiled'].search(titulo_limpio):
                errores.append({
                    'id_regla': f"V_titulo_{patron_info['seccion']}",
                    'diagnostico': 'error_limpieza_titulo',
                    'severidad': 'medio',
                    'mensaje': f"Patrón de ruido '{patron_info['seccion']}' encontrado en título limpio. "
                              f"Ejemplo: '{patron_info['ejemplo']}'. Agregar patrón a nlp_titulo_limpieza.json",
                    'campo': 'titulo_limpio',
                    'patron_encontrado': patron_info['patron'],
                    'valor_actual': titulo_limpio
                })

        return errores

    def _get_compiled_pattern(self, pattern: str) -> re.Pattern:
        """Compila y cachea patrones regex."""
        if pattern not in self._compiled_patterns:
            self._compiled_patterns[pattern] = re.compile(pattern)
        return self._compiled_patterns[pattern]

    def _get_field_value(self, oferta: Dict, campo: str) -> Any:
        """Obtiene valor de un campo, soportando campos anidados."""
        if '.' in campo:
            parts = campo.split('.')
            value = oferta
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return oferta.get(campo)

    def _evaluar_operador(self, valor: Any, operador: str, valor_esperado: Any = None, valores: List = None) -> bool:
        """
        Evalua un operador contra un valor.

        Operadores soportados:
        - is_null, is_empty, is_not_null, is_not_empty
        - eq, neq, lt, gt, lte, gte
        - contains, not_contains, contains_any, contains_all
        - matches_regex, in_list, not_in_list
        """
        # Operadores de nulidad
        if operador == "is_null":
            return valor is None
        elif operador == "is_not_null":
            return valor is not None
        elif operador == "is_empty":
            if valor is None:
                return True
            if isinstance(valor, str):
                return valor.strip() == ""
            if isinstance(valor, (list, dict)):
                return len(valor) == 0
            return False
        elif operador == "is_not_empty":
            if valor is None:
                return False
            if isinstance(valor, str):
                return valor.strip() != ""
            if isinstance(valor, (list, dict)):
                return len(valor) > 0
            return True

        # Operadores de comparacion
        elif operador == "eq":
            return valor == valor_esperado
        elif operador == "neq":
            return valor != valor_esperado
        elif operador == "lt":
            try:
                return float(valor) < float(valor_esperado) if valor is not None else False
            except (TypeError, ValueError):
                return False
        elif operador == "gt":
            try:
                return float(valor) > float(valor_esperado) if valor is not None else False
            except (TypeError, ValueError):
                return False
        elif operador == "lte":
            try:
                return float(valor) <= float(valor_esperado) if valor is not None else False
            except (TypeError, ValueError):
                return False
        elif operador == "gte":
            try:
                return float(valor) >= float(valor_esperado) if valor is not None else False
            except (TypeError, ValueError):
                return False

        # Operadores de contenido
        elif operador == "contains":
            if valor is None:
                return False
            return str(valor_esperado).lower() in str(valor).lower()
        elif operador == "not_contains":
            if valor is None:
                return True
            return str(valor_esperado).lower() not in str(valor).lower()
        elif operador == "contains_any":
            if valor is None or valores is None:
                return False
            valor_str = str(valor).lower()
            return any(str(v).lower() in valor_str for v in valores)
        elif operador == "contains_all":
            if valor is None or valores is None:
                return False
            valor_str = str(valor).lower()
            return all(str(v).lower() in valor_str for v in valores)

        # Operadores de regex
        elif operador == "matches_regex":
            if valor is None:
                return False
            try:
                pattern = self._get_compiled_pattern(valor_esperado)
                return bool(pattern.search(str(valor)))
            except re.error:
                return False

        # Operadores de lista
        elif operador == "in_list":
            return valor in (valores or [])
        elif operador == "not_in_list":
            return valor not in (valores or [])

        return False

    def _evaluar_condicion_simple(self, oferta: Dict, regla: Dict) -> bool:
        """Evalua una condicion simple (campo + operador)."""
        campo = regla.get("campo")
        operador = regla.get("operador")
        valor = self._get_field_value(oferta, campo)

        return self._evaluar_operador(
            valor=valor,
            operador=operador,
            valor_esperado=regla.get("valor"),
            valores=regla.get("valores")
        )

    def _evaluar_condiciones_multiples(self, oferta: Dict, regla: Dict) -> bool:
        """Evalua multiples condiciones con logica AND/OR."""
        condiciones = regla.get("condiciones", [])
        logica = regla.get("logica", "AND").upper()

        resultados = []
        for cond in condiciones:
            campo = cond.get("campo")
            operador = cond.get("operador")
            valor = self._get_field_value(oferta, campo)

            resultado = self._evaluar_operador(
                valor=valor,
                operador=operador,
                valor_esperado=cond.get("valor"),
                valores=cond.get("valores")
            )
            resultados.append(resultado)

        if logica == "AND":
            return all(resultados)
        elif logica == "OR":
            return any(resultados)

        return False

    def validar_oferta(self, oferta: Dict) -> List[Dict]:
        """
        Valida una oferta contra todas las reglas.

        Args:
            oferta: Diccionario con datos de la oferta

        Returns:
            Lista de errores detectados, cada uno con:
            - id_regla: ID de la regla que fallo
            - diagnostico: Tipo de error
            - severidad: critico, alto, medio, bajo, info
            - mensaje: Descripcion del error
            - auto_correccion: Correccion automatica si existe
        """
        errores = []
        reglas = self.validation_rules.get("reglas_validacion", [])

        for regla in reglas:
            # Determinar si la regla aplica
            if "condiciones" in regla:
                aplica = self._evaluar_condiciones_multiples(oferta, regla)
            else:
                aplica = self._evaluar_condicion_simple(oferta, regla)

            if aplica:
                error = {
                    "id_regla": regla.get("id"),
                    "diagnostico": regla.get("diagnostico"),
                    "severidad": regla.get("severidad", "medio"),
                    "mensaje": regla.get("mensaje"),
                    "campo": regla.get("campo"),
                    "id_oferta": oferta.get("id_oferta") or oferta.get("id")
                }

                # Si hay auto-correccion, incluirla
                if "auto_correccion" in regla:
                    error["auto_correccion"] = regla["auto_correccion"]

                errores.append(error)

        # Validación automática de título limpio usando patrones de nlp_titulo_limpieza.json
        titulo_limpio = oferta.get("titulo_limpio")
        if titulo_limpio:
            errores_titulo = self._validar_titulo_limpio(titulo_limpio)
            for error in errores_titulo:
                error["id_oferta"] = oferta.get("id_oferta") or oferta.get("id")
            errores.extend(errores_titulo)

        return errores

    def validar_lote(self, ofertas: List[Dict]) -> Dict[str, Any]:
        """
        Valida un lote de ofertas.

        Args:
            ofertas: Lista de ofertas a validar

        Returns:
            Diccionario con:
            - total: Total de ofertas
            - sin_errores: Cantidad sin errores
            - con_errores: Cantidad con errores
            - errores_por_tipo: Conteo por tipo de diagnostico
            - errores_detalle: Lista de errores por oferta
            - ofertas_ok: IDs de ofertas sin errores
            - ofertas_error: IDs de ofertas con errores
        """
        resultados = {
            "total": len(ofertas),
            "sin_errores": 0,
            "con_errores": 0,
            "errores_por_tipo": defaultdict(int),
            "errores_por_severidad": defaultdict(int),
            "errores_detalle": [],
            "ofertas_ok": [],
            "ofertas_error": [],
            "timestamp": datetime.now().isoformat()
        }

        for oferta in ofertas:
            id_oferta = oferta.get("id_oferta") or oferta.get("id")
            errores = self.validar_oferta(oferta)

            if errores:
                resultados["con_errores"] += 1
                resultados["ofertas_error"].append(id_oferta)

                for error in errores:
                    resultados["errores_por_tipo"][error["diagnostico"]] += 1
                    resultados["errores_por_severidad"][error["severidad"]] += 1

                resultados["errores_detalle"].append({
                    "id_oferta": id_oferta,
                    "errores": errores
                })
            else:
                resultados["sin_errores"] += 1
                resultados["ofertas_ok"].append(id_oferta)

        # Convertir defaultdicts a dicts normales
        resultados["errores_por_tipo"] = dict(resultados["errores_por_tipo"])
        resultados["errores_por_severidad"] = dict(resultados["errores_por_severidad"])

        return resultados

    def diagnosticar_error(self, oferta: Dict, error: Dict) -> Optional[Dict]:
        """
        Diagnostica un error usando diagnostic_patterns.json.

        Args:
            oferta: Datos de la oferta
            error: Error detectado por validar_oferta()

        Returns:
            Diagnostico detallado con config_afectado y accion_sugerida
        """
        patrones = self.diagnostic_patterns.get("patrones_diagnostico", [])
        diagnostico_tipo = error.get("diagnostico")

        for patron in patrones:
            if patron.get("diagnostico") != diagnostico_tipo:
                continue

            # Evaluar condicion del patron
            condicion = patron.get("condicion", {})

            if "patron_regex" in condicion:
                campo = condicion.get("campo")
                valor = self._get_field_value(oferta, campo)
                if valor and re.search(condicion["patron_regex"], str(valor), re.IGNORECASE):
                    return {
                        "patron_id": patron.get("id"),
                        "diagnostico": diagnostico_tipo,
                        "config_afectado": patron.get("config_afectado"),
                        "seccion": patron.get("seccion"),
                        "accion_sugerida": patron.get("accion_sugerida"),
                        "auto_corregible": patron.get("auto_corregible", False)
                    }

            elif "condiciones" in condicion:
                # Evaluar condiciones multiples
                if self._evaluar_condiciones_multiples(oferta, {"condiciones": condicion.get("condiciones"), "logica": condicion.get("logica", "AND")}):
                    return {
                        "patron_id": patron.get("id"),
                        "diagnostico": diagnostico_tipo,
                        "config_afectado": patron.get("config_afectado"),
                        "seccion": patron.get("seccion"),
                        "accion_sugerida": patron.get("accion_sugerida"),
                        "auto_corregible": patron.get("auto_corregible", False)
                    }

        # Si no hay patron especifico, devolver info basica del error
        return {
            "patron_id": None,
            "diagnostico": diagnostico_tipo,
            "config_afectado": None,
            "seccion": None,
            "accion_sugerida": f"Revisar manualmente error tipo {diagnostico_tipo}",
            "auto_corregible": False
        }

    def obtener_correccion(self, diagnostico: str) -> Optional[Dict]:
        """
        Obtiene la accion de correccion para un diagnostico.

        Args:
            diagnostico: Tipo de diagnostico (ej: "error_limpieza")

        Returns:
            Accion de correccion desde auto_correction_map.json
        """
        correcciones = self.correction_map.get("correcciones", {})
        return correcciones.get(diagnostico)

    def agrupar_errores_por_patron(self, errores_detalle: List[Dict]) -> Dict[str, Dict]:
        """
        Agrupa errores similares para presentar a Claude.

        Esto permite que Claude vea PATRONES en lugar de casos individuales.

        Args:
            errores_detalle: Lista de errores del validar_lote()

        Returns:
            Patrones agrupados con ejemplos
        """
        patrones = defaultdict(lambda: {
            "diagnostico": None,
            "campo": None,
            "ofertas": [],
            "ejemplos_valor": set(),
            "cantidad": 0
        })

        for item in errores_detalle:
            id_oferta = item["id_oferta"]
            for error in item["errores"]:
                diagnostico = error.get("diagnostico")
                campo = error.get("campo", "general")

                # Clave de agrupacion
                clave = f"{diagnostico}_{campo}"

                patrones[clave]["diagnostico"] = diagnostico
                patrones[clave]["campo"] = campo
                patrones[clave]["ofertas"].append(id_oferta)
                patrones[clave]["cantidad"] += 1

                # Intentar capturar valor ejemplo
                if "valor" in error:
                    patrones[clave]["ejemplos_valor"].add(str(error["valor"]))

        # Convertir sets a listas
        resultado = {}
        for clave, data in patrones.items():
            data["ejemplos_valor"] = list(data["ejemplos_valor"])[:5]  # Max 5 ejemplos
            resultado[clave] = data

        return resultado

    def generar_reporte_para_claude(self, resultados_lote: Dict) -> str:
        """
        Genera un reporte formateado para presentar a Claude.

        Args:
            resultados_lote: Output de validar_lote()

        Returns:
            Texto formateado con patrones agrupados
        """
        patrones = self.agrupar_errores_por_patron(resultados_lote["errores_detalle"])

        if not patrones:
            return "No se detectaron errores. Todas las ofertas pasaron validacion."

        lineas = [
            f"PATRONES DETECTADOS ({resultados_lote['con_errores']} ofertas con errores de {resultados_lote['total']} total)",
            ""
        ]

        # Ordenar por cantidad descendente
        patrones_ordenados = sorted(patrones.items(), key=lambda x: x[1]["cantidad"], reverse=True)

        for i, (clave, data) in enumerate(patrones_ordenados, 1):
            pct = (data["cantidad"] / resultados_lote["con_errores"]) * 100

            lineas.append(f"{i}. {data['diagnostico']} ({data['cantidad']} ofertas, {pct:.0f}%)")
            lineas.append(f"   Campo: {data['campo']}")

            if data["ejemplos_valor"]:
                lineas.append(f"   Valores ejemplo: {', '.join(data['ejemplos_valor'][:3])}")

            lineas.append(f"   IDs ejemplo: {', '.join(str(x) for x in data['ofertas'][:3])}")

            # Obtener correccion sugerida
            correccion = self.obtener_correccion(data["diagnostico"])
            if correccion:
                lineas.append(f"   -> Config: {correccion.get('config', 'N/A')}")
                lineas.append(f"   -> Accion: {correccion.get('tipo_accion', 'N/A')}")

            lineas.append("")

        return "\n".join(lineas)


# Funciones de conveniencia
def _persistir_errores_bd(conn, errores_detalle: List[Dict], run_id: str = None) -> int:
    """
    Persiste errores detectados en tabla validation_errors.

    Args:
        conn: Conexion a BD
        errores_detalle: Lista de errores del validar_lote()
        run_id: ID del run actual (opcional)

    Returns:
        Cantidad de errores insertados
    """
    timestamp = datetime.now().isoformat()
    insertados = 0

    for item in errores_detalle:
        id_oferta = item["id_oferta"]
        for error in item["errores"]:
            try:
                error_tipo = error.get("diagnostico")

                # Verificar si ya existe este error para esta oferta (evitar duplicados)
                cur = conn.execute('''
                    SELECT 1 FROM validation_errors
                    WHERE id_oferta = ? AND error_tipo = ? AND resuelto = 0
                ''', (str(id_oferta), error_tipo))

                if cur.fetchone():
                    # Ya existe, actualizar timestamp
                    conn.execute('''
                        UPDATE validation_errors
                        SET run_id = ?, detectado_timestamp = ?
                        WHERE id_oferta = ? AND error_tipo = ? AND resuelto = 0
                    ''', (run_id, timestamp, str(id_oferta), error_tipo))
                else:
                    # No existe, insertar
                    conn.execute('''
                        INSERT INTO validation_errors (
                            id_oferta, run_id, error_id, error_tipo, severidad,
                            mensaje, campo_afectado, detectado_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(id_oferta),
                        run_id,
                        error.get("id_regla"),
                        error_tipo,
                        error.get("severidad"),
                        error.get("mensaje"),
                        error.get("campo"),
                        timestamp
                    ))
                    insertados += 1
            except Exception as e:
                print(f"  WARN: Error insertando validation_error para {id_oferta}: {e}")

    conn.commit()
    return insertados


def validar_ofertas_desde_bd(
    db_path: str = None,
    limit: int = None,
    ids: List[str] = None,
    persist: bool = True,
    run_id: str = None
) -> Dict:
    """
    Valida ofertas directamente desde la base de datos.

    Args:
        db_path: Path a la BD SQLite
        limit: Limite de ofertas a validar
        ids: IDs especificos a validar
        persist: Si True, guarda errores en tabla validation_errors
        run_id: ID del run actual para tracking

    Returns:
        Resultados de validacion
    """
    import sqlite3

    if db_path is None:
        db_path = str(Path(__file__).parent / "bumeran_scraping.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Construir query - partimos de ofertas_esco_matching para solo validar las procesadas
    query = """
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
            (SELECT COUNT(*) FROM ofertas_esco_skills_detalle s WHERE s.id_oferta = m.id_oferta) as skills_count
        FROM ofertas_esco_matching m
        LEFT JOIN ofertas o ON o.id_oferta = m.id_oferta
        LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
    """

    if ids:
        placeholders = ','.join('?' * len(ids))
        query += f" WHERE m.id_oferta IN ({placeholders})"
        params = ids
    else:
        params = []

    if limit:
        query += f" LIMIT {limit}"

    cursor = conn.execute(query, params)
    ofertas = [dict(row) for row in cursor.fetchall()]

    # Validar
    validator = AutoValidator()
    resultados = validator.validar_lote(ofertas)

    # Persistir errores en BD si se solicita
    if persist and resultados.get("errores_detalle"):
        insertados = _persistir_errores_bd(conn, resultados["errores_detalle"], run_id)
        resultados["errores_persistidos"] = insertados
        print(f"  Errores persistidos en BD: {insertados}")

    conn.close()
    return resultados


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-validador MOL")
    parser.add_argument("--limit", type=int, help="Limite de ofertas a validar")
    parser.add_argument("--ids", help="IDs separados por coma")
    parser.add_argument("--reporte", action="store_true", help="Generar reporte para Claude")
    parser.add_argument("--no-persist", action="store_true", help="No persistir errores en BD")
    parser.add_argument("--run-id", help="ID del run para tracking")

    args = parser.parse_args()

    ids = args.ids.split(",") if args.ids else None

    # Generar run_id si no se proporciona
    run_id = args.run_id or f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print("Ejecutando validacion...")
    resultados = validar_ofertas_desde_bd(
        limit=args.limit,
        ids=ids,
        persist=not args.no_persist,
        run_id=run_id
    )

    print(f"\nResultados:")
    print(f"  Total: {resultados['total']}")
    print(f"  Sin errores: {resultados['sin_errores']}")
    print(f"  Con errores: {resultados['con_errores']}")
    print(f"\nErrores por tipo:")
    for tipo, count in resultados['errores_por_tipo'].items():
        print(f"  {tipo}: {count}")

    if args.reporte:
        validator = AutoValidator()
        print("\n" + "="*60)
        print(validator.generar_reporte_para_claude(resultados))
