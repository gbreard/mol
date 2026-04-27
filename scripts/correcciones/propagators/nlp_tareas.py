"""
Propagator de NLP tareas_explicitas.

Caso de uso: Cyn detecta que el LLM extrajo tareas alucinadas o confundió
encabezados/requisitos como tareas. Propagamos: re-NLP completo con prompt
actual sobre ofertas similares.

A diferencia de los otros propagators, este NO hace un cambio puntual —
dispara re-procesamiento NLP. Es el más caro en tiempo (segundos por oferta).
"""
import sqlite3
from typing import List

from .base import PropagatorBase, PropagationResult


class NLPTareasPropagator(PropagatorBase):
    """
    Patrón aceptado:
    {
      "tipo": "nlp_tareas_explicitas",
      "campo": "tareas_explicitas",
      "condicion": {
        "tipo": "regla_aplicada" | "id_oferta_lista" | "titulo_contiene_alguno",
        ...
      },
      "valor_anterior": "tareas alucinadas / encabezados",
      "valor_nuevo": null  (re-extracción regenera)
    }
    """

    TIPO = "nlp_tareas_explicitas"

    def identify(self, patron: dict) -> List[int]:
        cond = patron["condicion"]
        cond_tipo = cond["tipo"]

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        if cond_tipo == "regla_aplicada":
            regla = cond.get("valor_unico")
            cur.execute(
                "SELECT id_oferta FROM ofertas_esco_matching WHERE regla_aplicada = ?",
                (regla,),
            )
        elif cond_tipo == "id_oferta_lista":
            valores = cond.get("valores") or []
            if not valores:
                conn.close()
                return []
            ph = ",".join("?" for _ in valores)
            cur.execute(
                f"SELECT id_oferta FROM ofertas_esco_matching WHERE id_oferta IN ({ph})",
                [str(v) for v in valores],
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
            raise ValueError(f"condicion.tipo='{cond_tipo}' no soportado")

        ids = [int(r[0]) for r in cur.fetchall()]
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

        if dry_run:
            result.ofertas_actualizadas = len(ids)
            result.ids_tocados = ids[:]
            result.detalles["nota"] = (
                "Re-NLP completo es costoso (~segundos por oferta). "
                "En modo real ejecutará run_validated_pipeline.py."
            )
            return result

        # Ejecutar pipeline completo
        try:
            import subprocess
            cmd = [
                "python3",
                "scripts/run_validated_pipeline.py",
                "--ids",
                ",".join(str(i) for i in ids),
            ]
            env = {"OLLAMA_HOST": "172.17.0.1"}
            import os
            full_env = {**os.environ, **env}
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600, env=full_env
            )
            if proc.returncode == 0:
                result.ofertas_actualizadas = len(ids)
                result.ids_tocados = ids[:]
                result.detalles["stdout_tail"] = proc.stdout[-500:]
            else:
                result.errores.append(f"pipeline falló: {proc.stderr[-500:]}")
        except subprocess.TimeoutExpired:
            result.errores.append("Timeout (>1hr)")
        except Exception as e:
            result.errores.append(f"Error: {str(e)[:200]}")

        return result

    def verify(self, patron: dict, ids: list) -> dict:
        """Verifica que las tareas extraídas no estén vacías post-fix."""
        if not ids:
            return {"verificadas_ok": 0, "vacias": []}

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            ph = ",".join("?" for _ in ids)
            cur.execute(
                f"SELECT id_oferta, tareas_explicitas FROM ofertas_nlp "
                f"WHERE id_oferta IN ({ph})",
                [str(i) for i in ids],
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        ok = sum(1 for _, t in rows if t and len(t) >= 30)
        vacias = [int(oid) for oid, t in rows if not t or len(t) < 30]
        return {"verificadas_ok": ok, "vacias": vacias[:20]}
