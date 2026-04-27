"""
Propagator de Skills filtrado.

Caso de uso: Cyn detecta que skills alucinadas (peces, javanés, sánscrito)
caen sobre ofertas de un patrón específico. Propagamos: re-extracción de
skills sobre todas las ofertas con la regla aplicada o el ESCO específico,
aplicando los filtros SPEC G+K (que limpian alucinadas).

Este propagator NO modifica skills_rules.json — solo dispara re-extracción
sobre ofertas afectadas para que los filtros SPEC G+K limpien las skills.
"""
import sqlite3
from typing import List

from .base import PropagatorBase, PropagationResult


class SkillsFiltroPropagator(PropagatorBase):
    """
    Patrón aceptado:
    {
      "tipo": "skills_filtro",
      "campo": "skills_oferta",
      "condicion": {
        "tipo": "regla_aplicada" | "titulo_esco_code" | "id_oferta_lista",
        "valor_unico": "..." | "valores": [...]
      },
      "valor_anterior": "skills alucinadas",
      "valor_nuevo": null  (no aplica para skills_filtro)
    }
    """

    TIPO = "skills_filtro"

    def identify(self, patron: dict) -> List[int]:
        cond = patron["condicion"]
        cond_tipo = cond["tipo"]

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        if cond_tipo == "regla_aplicada":
            regla = cond.get("valor_unico")
            cur.execute("SELECT id_oferta FROM ofertas_esco_matching WHERE regla_aplicada = ?", (regla,))
        elif cond_tipo == "titulo_esco_code":
            code = cond.get("valor_unico")
            cur.execute("SELECT id_oferta FROM ofertas_esco_matching WHERE titulo_esco_code = ?", (code,))
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
            return result

        # Re-extracción via retropropagar_skills_spec_e (que aplica SPEC G+K)
        try:
            import subprocess
            # Limpiar progreso previo para los IDs específicos
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            ph = ",".join("?" for _ in ids)
            cur.execute(
                f"DELETE FROM spec_e_retro_progress WHERE id_oferta IN ({ph})",
                [str(i) for i in ids],
            )
            conn.commit()
            conn.close()

            cmd = [
                "python3",
                "scripts/embeddings/retropropagar_skills_spec_e.py",
                "--ids",
                ",".join(str(i) for i in ids),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if proc.returncode == 0:
                # Parsear cuántas se procesaron del stdout
                # Format esperado: "OK: N  Sin NLP: X  Errores: Y"
                import re
                m = re.search(r"OK:\s*(\d+)", proc.stdout)
                ok = int(m.group(1)) if m else len(ids)
                result.ofertas_actualizadas = ok
                result.ids_tocados = ids[:ok] if ok < len(ids) else ids[:]
                result.detalles["stdout_tail"] = proc.stdout[-500:]
            else:
                result.errores.append(f"retro script falló: {proc.stderr[-500:]}")
        except Exception as e:
            result.errores.append(f"Error: {str(e)[:200]}")

        return result

    def verify(self, patron: dict, ids: list) -> dict:
        """Verifica que skills_count post-fix sea razonable (>0, no vacío)."""
        if not ids:
            return {"verificadas_ok": 0, "vacias": []}

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            ph = ",".join("?" for _ in ids)
            cur.execute(
                f"SELECT id_oferta, skills_demandados_total FROM ofertas_esco_matching "
                f"WHERE id_oferta IN ({ph})",
                ids,
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        ok = sum(1 for _, n in rows if n and n > 0)
        vacias = [int(oid) for oid, n in rows if not n or n == 0]
        return {"verificadas_ok": ok, "vacias": vacias[:20]}
