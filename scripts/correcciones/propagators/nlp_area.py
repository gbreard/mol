"""
Propagator de NLP area_funcional.

Caso de uso: Cyn/Diego corrigen el área de una oferta. Propagamos a todas
las ofertas con título que matchea las mismas keywords.

Este propagator NO modifica configs JSON automáticamente — solo aplica el
cambio en BD. La regla persistente debe agregarse a nlp_inference_rules.json
manualmente o vía un paso posterior (cuando se considera "regla derivada
estable").
"""
import sqlite3
from typing import List

from .base import PropagatorBase, PropagationResult


class NLPAreaPropagator(PropagatorBase):
    """
    Patrón aceptado:
    {
      "tipo": "nlp_area_funcional",
      "campo": "area_funcional",
      "condicion": {
        "tipo": "titulo_contiene_alguno",
        "keywords": ["operario de deposito", "operario de almacén", ...]
      },
      "valor_anterior": "Produccion",
      "valor_nuevo": "Logistica"
    }
    """

    TIPO = "nlp_area_funcional"

    def identify(self, patron: dict) -> List[int]:
        cond = patron["condicion"]
        if cond["tipo"] != "titulo_contiene_alguno":
            raise ValueError(f"Condición {cond['tipo']} no soportada por NLPAreaPropagator")

        keywords = cond.get("keywords") or []
        if not keywords:
            return []

        valor_anterior = patron.get("valor_anterior")

        # Construir cláusula WHERE para keywords (LIKE)
        where_kw = " OR ".join(f"LOWER(o.titulo) LIKE ?" for _ in keywords)
        params = [f"%{k.lower()}%" for k in keywords]

        sql = f"""
            SELECT m.id_oferta FROM ofertas_esco_matching m
            JOIN ofertas o USING(id_oferta)
            JOIN ofertas_nlp n USING(id_oferta)
            WHERE ({where_kw})
              AND m.estado_validacion IN ('validado','validado_claude','validado_humano')
        """

        if valor_anterior:
            sql += " AND n.area_funcional = ?"
            params.append(valor_anterior)

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            ids = [int(r[0]) for r in cur.fetchall()]
        finally:
            conn.close()

        return ids

    def apply(self, patron: dict, ids: list, dry_run: bool = True) -> PropagationResult:
        result = PropagationResult(
            tipo=self.TIPO,
            ofertas_identificadas=len(ids),
            dry_run=dry_run,
        )

        if not ids:
            return result

        valor_nuevo = patron["valor_nuevo"]

        if dry_run:
            result.ofertas_actualizadas = len(ids)
            result.ids_tocados = ids[:]  # solo informativo
            return result

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            ph = ",".join("?" for _ in ids)
            cur.execute(
                f"UPDATE ofertas_nlp SET area_funcional = ? WHERE id_oferta IN ({ph})",
                [valor_nuevo, *[str(i) for i in ids]],
            )
            n = cur.rowcount
            conn.commit()
            result.ofertas_actualizadas = n
            result.ids_tocados = ids[:n] if n < len(ids) else ids[:]
        except Exception as e:
            result.errores.append(str(e))
        finally:
            conn.close()

        return result

    def verify(self, patron: dict, ids: list) -> dict:
        """Verifica que las ofertas tocadas tengan area_funcional = valor_nuevo."""
        if not ids:
            return {"verificadas_ok": 0, "fallidas": []}

        valor_nuevo = patron["valor_nuevo"]
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            ph = ",".join("?" for _ in ids)
            cur.execute(
                f"SELECT id_oferta, area_funcional FROM ofertas_nlp "
                f"WHERE id_oferta IN ({ph})",
                [str(i) for i in ids],
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        ok = sum(1 for _, area in rows if area == valor_nuevo)
        fallidas = [int(oid) for oid, area in rows if area != valor_nuevo]
        return {"verificadas_ok": ok, "fallidas": fallidas}
