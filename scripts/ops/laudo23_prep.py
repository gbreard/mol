# -*- coding: utf-8 -*-
"""[CASCADA — laudos 2 y 3, prep] Un solo scan del corpus:
  - laudo 2: congela los ids del delta contador (vacías con "para+acción" en requisito)
             → exports/cohorts/laudo2_delta_ids.json (reproducible).
  - laudo 3: flagea los 638 multipuesto inline en staging (multipuesto_inline_pendiente=1)
             → auditables y excluibles; el detector es mini-frente post-swap.
"""
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / 'database' / 'cascada_staging.db'
OUT_IDS = ROOT / 'exports' / 'cohorts' / 'laudo2_delta_ids.json'

PARA_RE = re.compile(
    r'\bpara\s+(realizar|gestionar|atender|coordinar|desarrollar|administrar|llevar|ejecutar|'
    r'elaborar|controlar|brindar|asesorar|supervisar|manejar|confeccionar|liquidar|registrar|'
    r'analizar|operar|vender|producir|organizar|planificar)\b', re.I)
REQ_CTX = re.compile(r'(experiencia|requisit|se busca|buscamos|conocimiento)', re.I)
SEGUN = re.compile(r'seg[uú]n el puesto|para cada (puesto|posici[oó]n|perfil|vacante)|'
                   r'seg[uú]n (el|la) (perfil|posici[oó]n)', re.I)
LISTA = re.compile(r'\((?:[A-Za-zÁ-Úá-ú]{4,}\s*/\s*){2,}[A-Za-zÁ-Úá-ú]{4,}\)')


def main():
    con = sqlite3.connect(f'file:{STAGING}', uri=True, timeout=120)
    con.execute('PRAGMA busy_timeout=120000')
    con.execute("ATTACH DATABASE 'file:%s?mode=ro' AS src" % (ROOT / 'database/bumeran_scraping.db'))
    cols = [r[1] for r in con.execute("PRAGMA table_info(ofertas_nlp_tareas_v124)")]
    if 'multipuesto_inline_pendiente' not in cols:
        con.execute("ALTER TABLE ofertas_nlp_tareas_v124 ADD COLUMN multipuesto_inline_pendiente INTEGER DEFAULT 0")
        con.commit()

    # cuerpos de TODO el staging (para laudo 3) + vacías (para laudo 2)
    vac = {r[0] for r in con.execute("SELECT id_oferta FROM ofertas_nlp_tareas_v124 WHERE n_tareas=0")}
    delta2, inline3 = [], []
    ids = [r[0] for r in con.execute("SELECT id_oferta FROM ofertas_nlp_tareas_v124")]
    B = 900
    for i in range(0, len(ids), B):
        ch = ids[i:i + B]
        q = ("SELECT CAST(id_oferta AS TEXT), titulo, COALESCE(descripcion_utf8,descripcion) "
             "FROM src.ofertas WHERE CAST(id_oferta AS TEXT) IN (%s)" % ",".join("?" * len(ch)))
        for oid, tit, d in con.execute(q, ch):
            txt = f"{tit or ''} {d or ''}"
            if oid in vac and d and PARA_RE.search(d) and REQ_CTX.search(d):
                delta2.append(oid)
            if SEGUN.search(txt) or LISTA.search(txt):
                inline3.append(oid)

    OUT_IDS.write_text(json.dumps({'fecha': '2026-10-16', 'n': len(delta2), 'ids': delta2}, ensure_ascii=False))
    # flag laudo 3
    con.execute("UPDATE ofertas_nlp_tareas_v124 SET multipuesto_inline_pendiente=0")
    con.executemany("UPDATE ofertas_nlp_tareas_v124 SET multipuesto_inline_pendiente=1 WHERE id_oferta=?",
                    [(x,) for x in inline3])
    con.commit()
    n_flag = con.execute("SELECT COUNT(*) FROM ofertas_nlp_tareas_v124 WHERE multipuesto_inline_pendiente=1").fetchone()[0]
    print(f"laudo 2 — delta contador ids: {len(delta2)} -> {OUT_IDS.name}")
    print(f"laudo 3 — multipuesto_inline_pendiente flageados en staging: {n_flag}")
    con.close()


if __name__ == '__main__':
    main()
