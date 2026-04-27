"""
Propagator de Matching ESCO.

Caso de uso: cambio de target en una regla de matching_rules_business.json.
Propaga: re-rematch de las ofertas que matchean esa regla.

Ejemplo SPEC P: R236_analista_marketing target 2431.6 → 2431.10.
Todas las ofertas con regla_aplicada=R236 deben re-rematcharse.
"""
import sqlite3
from typing import List

from .base import PropagatorBase, PropagationResult


class MatchingESCOPropagator(PropagatorBase):
    """
    Patrón aceptado:
    {
      "tipo": "matching_esco",
      "campo": "esco_label",
      "condicion": {
        "tipo": "regla_aplicada",
        "valor_unico": "R236_analista_marketing"
      },
      "valor_anterior": "2431.6",
      "valor_nuevo": "2431.10"
    }

    O con condición por título:
    {
      "tipo": "matching_esco",
      "campo": "esco_label",
      "condicion": {
        "tipo": "titulo_contiene_alguno",
        "keywords": ["ensamble de armas", "tecnico armero"]
      },
      "valor_anterior": "7223.7",
      "valor_nuevo": "7222.2"
    }

    Nota: este propagator NO modifica el JSON de reglas — eso debe hacerse
    aparte. Este propagator solo identifica las ofertas afectadas y dispara
    re-rematch.
    """

    TIPO = "matching_esco"

    def identify(self, patron: dict) -> List[int]:
        cond = patron["condicion"]
        cond_tipo = cond["tipo"]

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        if cond_tipo == "regla_aplicada":
            regla = cond.get("valor_unico")
            if not regla:
                conn.close()
                raise ValueError("condicion.valor_unico requerido para regla_aplicada")
            cur.execute(
                """SELECT id_oferta FROM ofertas_esco_matching WHERE regla_aplicada = ?""",
                (regla,),
            )

        elif cond_tipo == "titulo_contiene_alguno":
            keywords = cond.get("keywords") or []
            if not keywords:
                conn.close()
                return []
            where_kw = " OR ".join("LOWER(o.titulo) LIKE ?" for _ in keywords)
            params = [f"%{k.lower()}%" for k in keywords]
            sql = f"""
                SELECT m.id_oferta FROM ofertas_esco_matching m
                JOIN ofertas o USING(id_oferta)
                WHERE ({where_kw})
                  AND m.estado_validacion IN ('validado','validado_claude','validado_humano')
            """
            cur.execute(sql, params)

        else:
            conn.close()
            raise ValueError(f"condicion.tipo='{cond_tipo}' no soportado por MatchingESCOPropagator")

        ids = [int(r[0]) for r in cur.fetchall()]
        conn.close()
        return ids

    def apply(self, patron: dict, ids: list, dry_run: bool = True) -> PropagationResult:
        """Re-rematch usando rematch_isco_spec_h.persist_matching_result.

        Por simplicidad, importa y reusa el flujo del rematcher existente.
        """
        result = PropagationResult(
            tipo=self.TIPO,
            ofertas_identificadas=len(ids),
            dry_run=dry_run,
        )

        if not ids:
            return result

        if dry_run:
            result.ofertas_actualizadas = len(ids)
            result.ids_tocados = ids[:]
            return result

        # Ejecutar re-rematch real
        try:
            import sys
            sys.path.insert(0, "."); sys.path.insert(0, "database")
            from match_ofertas_v3 import MatcherV3
            import importlib.util
            import json
            from datetime import datetime, timezone

            spec = importlib.util.spec_from_file_location(
                "rematch_h", "scripts/embeddings/rematch_isco_spec_h.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            meta = json.load(open("database/embeddings/esco_occupations_metadata.json"))
            uri_to_code = {m["uri"]: m.get("esco_code") for m in meta if m.get("esco_code")}

            conn = sqlite3.connect(self.db_path)
            matcher = MatcherV3(db_conn=conn, verbose=self.verbose)
            run_id = f"spec_t_propagation_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

            ok = 0
            errores_caso = []
            for oid in ids:
                estado = mod.get_estado_actual(conn, oid)
                nlp = mod.get_oferta_nlp(conn, oid)
                if not estado or not nlp:
                    continue
                match_result = matcher.match(nlp)
                try:
                    mod.persist_matching_result(
                        conn, oid, match_result, estado, run_id, uri_to_code
                    )
                    ok += 1
                    result.ids_tocados.append(oid)
                except sqlite3.IntegrityError as e:
                    if "validada" in str(e).lower():
                        result.ids_skipped.append(oid)
                    else:
                        errores_caso.append((oid, str(e)))
            conn.commit()
            conn.close()

            result.ofertas_actualizadas = ok
            if errores_caso:
                result.errores = [f"{oid}: {err[:100]}" for oid, err in errores_caso[:10]]
        except Exception as e:
            result.errores.append(f"Error global: {str(e)[:200]}")

        return result

    def verify(self, patron: dict, ids: list) -> dict:
        """Verifica que el target esco_code de las ofertas sea valor_nuevo."""
        if not ids:
            return {"verificadas_ok": 0, "fallidas": []}

        valor_nuevo = patron.get("valor_nuevo")
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            ph = ",".join("?" for _ in ids)
            cur.execute(
                f"SELECT id_oferta, titulo_esco_code FROM ofertas_esco_matching "
                f"WHERE id_oferta IN ({ph})",
                ids,
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        # Aceptar valor_nuevo exacto o sub-código (ej: 2411 acepta 2411.1.1)
        ok = sum(
            1 for _, code in rows
            if code and (code == valor_nuevo or (valor_nuevo and code.startswith(valor_nuevo)))
        )
        fallidas = [
            int(oid) for oid, code in rows
            if not code or (valor_nuevo and not code.startswith(valor_nuevo))
        ]
        return {"verificadas_ok": ok, "fallidas": fallidas[:20]}
