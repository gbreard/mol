"""
NLP Validator - Pre-matching quality gate.

Evalúa la calidad de extracción NLP ANTES de que la oferta entre a matching.
Severidades critico/alto BLOQUEAN la oferta (no entra a matching).

Version: 1.0.0
Fecha: 2026-02-13

Uso:
    from database.nlp_validator import NLPValidator

    validator = NLPValidator(verbose=True)
    result = validator.validar_desde_bd(limit=50)
    print(f"Pass: {result['gate_pass_count']}, Block: {result['gate_block_count']}")
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class NLPValidator:
    """
    Pre-matching NLP quality gate.

    - Evalúa reglas de config/nlp_validation_rules.json
    - Gate: critico/alto → oferta NO entra a matching
    - Métricas: field completeness para análisis de extracción
    - Persistencia: validation_errors con error_tipo 'nlp_gate_*' / 'nlp_quality_*'
    """

    VERSION = "1.0.0"
    GATE_SEVERITIES = {'critico', 'alto'}

    def __init__(self, config_dir: Optional[Path] = None, verbose: bool = False):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.verbose = verbose

        # Cargar configs
        self.rules_config = self._load_json("nlp_validation_rules.json")
        self.sector_canonico = self._load_json("sector_canonico.json")

        # Cache de regex compilados
        self._compiled_patterns = {}

        # Construir lookup sector → clae_seccion desde sector_canonico
        self._sector_clae_map = {}
        for sector, data in self.sector_canonico.get("sectores", {}).items():
            if data.get("clae_seccion"):
                self._sector_clae_map[sector] = data["clae_seccion"]

        if self.verbose:
            reglas = self.rules_config.get("reglas", [])
            print(f"[NLP Validator v{self.VERSION}] {len(reglas)} reglas cargadas")

    def _load_json(self, filename: str) -> Dict:
        path = self.config_dir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _get_compiled_pattern(self, pattern: str) -> re.Pattern:
        if pattern not in self._compiled_patterns:
            self._compiled_patterns[pattern] = re.compile(pattern)
        return self._compiled_patterns[pattern]

    def _get_field_value(self, oferta: Dict, campo: str) -> Any:
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

    # ─── Operator evaluation (same logic as auto_validator) ───

    def _evaluar_operador(self, valor: Any, operador: str,
                          valor_esperado: Any = None, valores: List = None) -> bool:
        # Nulidad
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

        # Comparación
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

        # Contenido
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

        # Regex
        elif operador == "matches_regex":
            if valor is None:
                return False
            try:
                pattern = self._get_compiled_pattern(valor_esperado)
                return bool(pattern.search(str(valor)))
            except re.error:
                return False

        # Lista
        elif operador == "in_list":
            return valor in (valores or [])
        elif operador == "not_in_list":
            return valor not in (valores or [])

        return False

    def _evaluar_condicion_simple(self, oferta: Dict, regla: Dict) -> bool:
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
        condiciones = regla.get("condiciones", [])
        logica = regla.get("logica", "AND").upper()

        resultados = []
        for cond in condiciones:
            campo = cond.get("campo")
            valor = self._get_field_value(oferta, campo)
            resultado = self._evaluar_operador(
                valor=valor,
                operador=cond.get("operador"),
                valor_esperado=cond.get("valor"),
                valores=cond.get("valores")
            )
            resultados.append(resultado)

        if logica == "AND":
            return all(resultados)
        elif logica == "OR":
            return any(resultados)
        return False

    # ─── Computed fields ───

    def _enrich_computed_fields(self, oferta: Dict) -> Dict:
        """Agrega campos calculados que algunas reglas necesitan."""
        enriched = dict(oferta)

        # sector_coincide_area
        sector = (enriched.get("sector_empresa") or "").strip().lower()
        area = (enriched.get("area_funcional") or "").strip().lower()
        enriched["sector_coincide_area"] = (
            sector != "" and area != "" and sector == area
        )

        # clae_sector_mismatch
        sector_raw = (enriched.get("sector_empresa") or "").strip()
        clae_seccion = enriched.get("clae_seccion")
        expected_seccion = self._sector_clae_map.get(sector_raw)
        enriched["clae_sector_mismatch"] = (
            expected_seccion is not None
            and clae_seccion is not None
            and clae_seccion != expected_seccion
        )

        # tareas_explicitas_length (si no viene de BD)
        if "tareas_explicitas_length" not in enriched:
            tareas = enriched.get("tareas_explicitas") or ""
            enriched["tareas_explicitas_length"] = len(tareas)

        # descripcion_length (si no viene de BD)
        if "descripcion_length" not in enriched:
            desc = enriched.get("descripcion") or enriched.get("largo_descripcion") or ""
            enriched["descripcion_length"] = len(desc) if isinstance(desc, str) else (desc or 0)

        # skills_count: puede venir de BD o calcularlo
        if "skills_count" not in enriched or enriched["skills_count"] is None:
            skills_raw = enriched.get("skills_tecnicas_list") or ""
            if isinstance(skills_raw, str) and skills_raw.strip():
                enriched["skills_count"] = len([s for s in skills_raw.split(";") if s.strip()])
            else:
                enriched["skills_count"] = 0

        return enriched

    # ─── Core validation ───

    def validar_oferta(self, oferta: Dict) -> Dict:
        """
        Valida una oferta NLP contra todas las reglas.

        Returns:
            {
                'errores': [...],
                'gate_pass': bool,
                'gate_blocked_by': [ids de reglas que bloquearon] o []
            }
        """
        enriched = self._enrich_computed_fields(oferta)
        errores = []
        gate_blocked_by = []

        reglas = self.rules_config.get("reglas", [])

        for regla in reglas:
            if "condiciones" in regla:
                aplica = self._evaluar_condiciones_multiples(enriched, regla)
            else:
                aplica = self._evaluar_condicion_simple(enriched, regla)

            if aplica:
                severidad = regla.get("severidad", "medio")
                error = {
                    "id_regla": regla.get("id"),
                    "diagnostico": regla.get("diagnostico"),
                    "severidad": severidad,
                    "mensaje": regla.get("mensaje"),
                    "campo": regla.get("campo"),
                    "id_oferta": enriched.get("id_oferta") or enriched.get("id")
                }
                if "auto_correccion" in regla:
                    error["auto_correccion"] = regla["auto_correccion"]
                errores.append(error)

                if severidad in self.GATE_SEVERITIES:
                    gate_blocked_by.append(regla.get("id"))

        return {
            "errores": errores,
            "gate_pass": len(gate_blocked_by) == 0,
            "gate_blocked_by": gate_blocked_by
        }

    def validar_lote(self, ofertas: List[Dict]) -> Dict:
        """
        Valida un lote de ofertas NLP.

        Returns:
            {
                'total': int,
                'gate_pass_count': int,
                'gate_block_count': int,
                'ids_aprobados': [...],
                'ids_bloqueados': [...],
                'errores_detalle': [...],
                'errores_por_tipo': {...},
                'errores_por_severidad': {...},
                'extraction_report': {...}
            }
        """
        resultado = {
            "total": len(ofertas),
            "gate_pass_count": 0,
            "gate_block_count": 0,
            "ids_aprobados": [],
            "ids_bloqueados": [],
            "errores_detalle": [],
            "errores_por_tipo": defaultdict(int),
            "errores_por_severidad": defaultdict(int),
            "timestamp": datetime.now().isoformat()
        }

        for oferta in ofertas:
            id_oferta = oferta.get("id_oferta") or oferta.get("id")
            val = self.validar_oferta(oferta)

            if val["gate_pass"]:
                resultado["gate_pass_count"] += 1
                resultado["ids_aprobados"].append(id_oferta)
            else:
                resultado["gate_block_count"] += 1
                resultado["ids_bloqueados"].append(id_oferta)

            if val["errores"]:
                for e in val["errores"]:
                    resultado["errores_por_tipo"][e["diagnostico"]] += 1
                    resultado["errores_por_severidad"][e["severidad"]] += 1
                resultado["errores_detalle"].append({
                    "id_oferta": id_oferta,
                    "gate_pass": val["gate_pass"],
                    "gate_blocked_by": val["gate_blocked_by"],
                    "errores": val["errores"]
                })

        # Extraction report
        resultado["extraction_report"] = self.get_extraction_report(ofertas)

        # Convert defaultdicts
        resultado["errores_por_tipo"] = dict(resultado["errores_por_tipo"])
        resultado["errores_por_severidad"] = dict(resultado["errores_por_severidad"])

        return resultado

    def validar_desde_bd(self, db_path=None, ids=None, limit=None,
                         persist=True, run_id=None, update_gate=True) -> Dict:
        """
        Lee ofertas de ofertas_nlp, valida, persiste errores, actualiza gate status.

        Args:
            db_path: Path a BD SQLite
            ids: IDs específicos a validar
            limit: Límite de ofertas
            persist: Persistir errores en validation_errors
            run_id: ID del run para tracking
            update_gate: Actualizar columna nlp_gate_status

        Returns:
            Resultado de validar_lote + errores_persistidos count
        """
        if db_path is None:
            db_path = str(Path(__file__).parent / "bumeran_scraping.db")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        query = """
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
        """

        params = []
        where_clauses = []

        if ids:
            placeholders = ','.join(['?'] * len(ids))
            where_clauses.append(f"n.id_oferta IN ({placeholders})")
            params = list(ids)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        if limit:
            query += f" LIMIT {limit}"

        cur = conn.execute(query, params)
        ofertas = [dict(row) for row in cur.fetchall()]

        if self.verbose:
            print(f"[NLP Gate] Validando {len(ofertas)} ofertas...")

        # Enriquecer con skills_count desde BD (subquery sería lenta)
        # Para ofertas con matching ya hecho, tomar skills_count de ahí
        if ofertas:
            all_ids = [str(o["id_oferta"]) for o in ofertas]
            placeholders = ','.join(['?'] * len(all_ids))
            cur2 = conn.execute(f"""
                SELECT id_oferta, COUNT(*) as cnt
                FROM ofertas_esco_skills_detalle
                WHERE id_oferta IN ({placeholders})
                GROUP BY id_oferta
            """, all_ids)
            skills_counts = {str(row["id_oferta"]): row["cnt"] for row in cur2.fetchall()}

            for oferta in ofertas:
                oid = str(oferta["id_oferta"])
                if oid in skills_counts:
                    oferta["skills_count"] = skills_counts[oid]
                # Si no hay skills en la tabla detalle, usar skills_tecnicas_list
                # (el campo _enrich_computed_fields se encarga)

        # Validar
        resultado = self.validar_lote(ofertas)

        # Persistir errores
        if persist and resultado["errores_detalle"]:
            resultado["errores_persistidos"] = self._persistir_errores(
                conn, resultado["errores_detalle"], run_id
            )
            if self.verbose:
                print(f"[NLP Gate] Errores persistidos: {resultado['errores_persistidos']}")

        # Actualizar gate status
        if update_gate:
            self._actualizar_gate_status(conn, resultado)

        conn.close()
        return resultado

    def _persistir_errores(self, conn, errores_detalle: List[Dict], run_id: str = None) -> int:
        """Persiste errores en validation_errors."""
        timestamp = datetime.now().isoformat()
        insertados = 0

        for item in errores_detalle:
            id_oferta = item["id_oferta"]
            for error in item["errores"]:
                try:
                    error_tipo = error.get("diagnostico")

                    cur = conn.execute('''
                        SELECT 1 FROM validation_errors
                        WHERE id_oferta = ? AND error_tipo = ? AND resuelto = 0
                    ''', (str(id_oferta), error_tipo))

                    if cur.fetchone():
                        conn.execute('''
                            UPDATE validation_errors
                            SET run_id = ?, detectado_timestamp = ?
                            WHERE id_oferta = ? AND error_tipo = ? AND resuelto = 0
                        ''', (run_id, timestamp, str(id_oferta), error_tipo))
                    else:
                        conn.execute('''
                            INSERT INTO validation_errors (
                                id_oferta, run_id, error_id, error_tipo, severidad,
                                mensaje, campo_afectado, detectado_timestamp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(id_oferta), run_id, error.get("id_regla"),
                            error_tipo, error.get("severidad"),
                            error.get("mensaje"), error.get("campo"), timestamp
                        ))
                        insertados += 1
                except Exception as e:
                    if self.verbose:
                        print(f"  WARN: Error insertando validation_error para {id_oferta}: {e}")

        conn.commit()
        return insertados

    def _actualizar_gate_status(self, conn, resultado: Dict):
        """Actualiza nlp_gate_status en ofertas_nlp."""
        updated = 0

        # Aprobados
        for id_oferta in resultado["ids_aprobados"]:
            conn.execute(
                "UPDATE ofertas_nlp SET nlp_gate_status = 'aprobado' WHERE id_oferta = ?",
                (str(id_oferta),)
            )
            updated += 1

        # Bloqueados
        for id_oferta in resultado["ids_bloqueados"]:
            conn.execute(
                "UPDATE ofertas_nlp SET nlp_gate_status = 'bloqueado' WHERE id_oferta = ?",
                (str(id_oferta),)
            )
            updated += 1

        conn.commit()

        if self.verbose:
            print(f"[NLP Gate] Gate status actualizado: "
                  f"{len(resultado['ids_aprobados'])} aprobados, "
                  f"{len(resultado['ids_bloqueados'])} bloqueados")

    # ─── Extraction report ───

    def get_extraction_report(self, ofertas: List[Dict]) -> Dict:
        """
        Métricas de completitud de extracción NLP.

        Returns:
            {
                'field_completeness': {campo: {'filled': N, 'total': N, 'pct_filled': float}},
                'value_distributions': {campo_enum: {valor: count}},
                'summary': {'below_50pct': [...], 'below_80pct': [...]}
            }
        """
        if not ofertas:
            return {"field_completeness": {}, "value_distributions": {}, "summary": {}}

        campos = self.rules_config.get("campos_extraction_report", [
            "titulo_limpio", "provincia", "localidad", "sector_empresa",
            "area_funcional", "nivel_seniority", "modalidad", "tipo_oferta",
            "tareas_explicitas", "tareas_inferidas", "clae_code", "clae_seccion"
        ])

        # Campos enum para distribución de valores
        enum_fields = {
            "sector_empresa", "area_funcional", "nivel_seniority",
            "modalidad", "tipo_oferta", "sector_confianza", "sector_fuente",
            "clae_seccion"
        }

        total = len(ofertas)
        completeness = {}
        distributions = defaultdict(lambda: defaultdict(int))

        for campo in campos:
            filled = 0
            for oferta in ofertas:
                val = oferta.get(campo)
                if val is not None and (not isinstance(val, str) or val.strip() != ""):
                    filled += 1
                    if campo in enum_fields and isinstance(val, str):
                        distributions[campo][val.strip()] += 1
            completeness[campo] = {
                "filled": filled,
                "total": total,
                "pct_filled": round(100 * filled / total, 1) if total > 0 else 0
            }

        # Summary
        below_50 = [c for c, s in completeness.items() if s["pct_filled"] < 50]
        below_80 = [c for c, s in completeness.items() if 50 <= s["pct_filled"] < 80]

        return {
            "field_completeness": completeness,
            "value_distributions": {k: dict(v) for k, v in distributions.items()},
            "summary": {
                "below_50pct": below_50,
                "below_80pct": below_80
            }
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NLP Validator - Pre-matching gate")
    parser.add_argument("--limit", type=int, help="Limite de ofertas")
    parser.add_argument("--ids", help="IDs separados por coma")
    parser.add_argument("--no-persist", action="store_true", help="No persistir errores")
    parser.add_argument("--no-gate", action="store_true", help="No actualizar gate status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--extraction-report", action="store_true", help="Mostrar extraction report")

    args = parser.parse_args()
    ids = args.ids.split(",") if args.ids else None

    validator = NLPValidator(verbose=args.verbose or True)
    result = validator.validar_desde_bd(
        ids=ids,
        limit=args.limit,
        persist=not args.no_persist,
        update_gate=not args.no_gate
    )

    print(f"\nResultados NLP Gate:")
    print(f"  Total: {result['total']}")
    print(f"  Aprobados: {result['gate_pass_count']}")
    print(f"  Bloqueados: {result['gate_block_count']}")

    if result["errores_por_severidad"]:
        print(f"\nErrores por severidad:")
        for sev, count in sorted(result["errores_por_severidad"].items()):
            print(f"  {sev}: {count}")

    if result["errores_por_tipo"]:
        print(f"\nErrores por tipo:")
        for tipo, count in sorted(result["errores_por_tipo"].items(), key=lambda x: -x[1]):
            print(f"  {tipo}: {count}")

    if args.extraction_report and result.get("extraction_report"):
        report = result["extraction_report"]
        print(f"\nExtraction Report:")
        for campo, stats in sorted(
            report["field_completeness"].items(),
            key=lambda x: x[1]["pct_filled"]
        ):
            print(f"  {campo:30s} {stats['pct_filled']:5.1f}% ({stats['filled']}/{stats['total']})")

    # Mostrar primeros bloqueados
    blocked_details = [d for d in result["errores_detalle"] if not d["gate_pass"]]
    if blocked_details[:5]:
        print(f"\nPrimeros bloqueados:")
        for d in blocked_details[:5]:
            reasons = ", ".join(d["gate_blocked_by"])
            print(f"  {d['id_oferta']}: {reasons}")
