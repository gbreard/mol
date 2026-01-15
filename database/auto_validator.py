"""
Auto-validador del pipeline MOL.
Lee validation_rules.json y evalua ofertas automaticamente.

Version: 1.0
Fecha: 2026-01-14

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

        # Cache de reglas compiladas (regex)
        self._compiled_patterns = {}

    def _load_json(self, filename: str) -> Dict:
        """Carga un archivo JSON de config."""
        path = self.config_dir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

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
def validar_ofertas_desde_bd(db_path: str = None, limit: int = None, ids: List[str] = None) -> Dict:
    """
    Valida ofertas directamente desde la base de datos.

    Args:
        db_path: Path a la BD SQLite
        limit: Limite de ofertas a validar
        ids: IDs especificos a validar

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
            n.area_funcional,
            n.nivel_seniority,
            n.modalidad,
            n.experiencia_min_anios,
            n.experiencia_max_anios,
            n.tareas_explicitas,
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
    conn.close()

    # Validar
    validator = AutoValidator()
    return validator.validar_lote(ofertas)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-validador MOL")
    parser.add_argument("--limit", type=int, help="Limite de ofertas a validar")
    parser.add_argument("--ids", help="IDs separados por coma")
    parser.add_argument("--reporte", action="store_true", help="Generar reporte para Claude")

    args = parser.parse_args()

    ids = args.ids.split(",") if args.ids else None

    print("Ejecutando validacion...")
    resultados = validar_ofertas_desde_bd(limit=args.limit, ids=ids)

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
