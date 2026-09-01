#!/usr/bin/env python3
"""[2026-09-01] Limpieza retroactiva de TEXTO DE INTERFAZ guardado como descripcion (CT).

Hermano de limpieza_boilerplate_ct.py. Aquel ataca el SEO ("¿Buscas trabajo
de…? Crea tu CV"); este ataca los textos de UI que el parser tomaba como
descripcion antes del fix del 2026-08-28:

  - modal de denuncias  : "Para denuncias como la tuya recomendamos…"   (221 chars)
  - error de postulacion: "Error al realizar la postulacion…"      (121 / 1806 chars)

El parser de hoy ya no los produce (verificado 5/5 contra el portal), pero los
registros historicos siguen en la BD y, como TIENEN "descripcion", quedan fuera
de la cola del PASO 2: no se reparan solos. Mismo mecanismo por el que las
14.469 del boilerplate no se reparaban.

Igual que el limpiador de boilerplate:
  1. Excluye ofertas con validacion HUMANA (el trabajo humano no se borra).
  2. Anula la descripcion dejando el original en `descripcion_anulada_log`
     (auditable y reversible), con motivo propio 'texto_ui_ct'.
  3. En LOCAL invalida la segunda generacion (NLP/matching/skills derivados de
     basura). En el VPS esas tablas no existen y el paso se omite solo.

Uso:
    python scripts/db/limpieza_ui_ct.py --dry-run
    python scripts/db/limpieza_ui_ct.py --db /opt/mol/database/bumeran_scraping.db
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

MOTIVO = 'texto_ui_ct'
ESTADOS_HUMANOS = ('validado', 'validado_humano')

# Marcadores de texto de interfaz. Se exige que el texto EMPIECE con alguno:
# una descripcion real jamas arranca asi, y evita borrar un aviso legitimo que
# mencione la palabra "denuncia" en el medio.
MARCADORES = (
    'Para denuncias como la tuya',
    'Error al realizar la postulaci',
)
# Ninguno de los textos de UI observados supera los 1.806 chars, y no hay
# descripciones reales >2.500 que los contengan. El techo es una red extra.
LARGO_MAX = 2500


def es_texto_ui(desc: str) -> bool:
    if not desc or len(desc) > LARGO_MAX:
        return False
    limpio = desc.strip()
    return any(limpio.startswith(m) for m in MARCADORES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--db', default=str(
        Path(__file__).resolve().parents[2] / 'database' / 'bumeran_scraping.db'))
    ap.add_argument('--intocables', default=None,
                    help='JSON con ids protegidos calculados en otra BD '
                         '(para el VPS, que no tiene ofertas_esco_matching)')
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=120)
    cur = conn.cursor()
    cur.execute("PRAGMA busy_timeout=60000")

    candidatas = [(o, d) for o, d in cur.execute(
        "SELECT id_oferta, descripcion FROM ofertas "
        "WHERE portal = 'computrabajo' AND descripcion IS NOT NULL")
        if es_texto_ui(d)]
    print(f'detectadas con texto de interfaz: {len(candidatas)}')

    # guarda del trabajo humano
    tablas = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    humanas = set()
    if args.intocables:
        humanas = set(json.load(open(args.intocables)))
        print(f'  intocables recibidos de otra BD: {len(humanas)}')
    elif 'ofertas_esco_matching' in tablas:
        ids = [str(o) for o, _ in candidatas]
        for i in range(0, len(ids), 500):
            q = ','.join(ids[i:i + 500])
            for (o,) in cur.execute(
                    f"SELECT id_oferta FROM ofertas_esco_matching "
                    f"WHERE id_oferta IN ({q}) AND estado_validacion IN {ESTADOS_HUMANOS}"):
                humanas.add(str(o))
        print(f'  excluidas por validacion humana: {len(humanas)}')
    else:
        print('  [i] sin ofertas_esco_matching en esta BD; guarda no aplicable aqui')

    a_limpiar = [(o, d) for o, d in candidatas if str(o) not in humanas]
    print(f'a limpiar: {len(a_limpiar)}')

    if not a_limpiar:
        return

    largos = sorted(len(d) for _, d in a_limpiar)
    print(f'  longitudes: min={largos[0]} p50={largos[len(largos)//2]} max={largos[-1]}')

    if args.dry_run:
        print('[dry-run] no se escribe nada')
        return

    cur.execute("""CREATE TABLE IF NOT EXISTS descripcion_anulada_log (
        id_oferta TEXT PRIMARY KEY,
        descripcion_original TEXT,
        motivo TEXT,
        anulada_en TEXT)""")
    ahora = datetime.now().isoformat()
    cols = {r[1] for r in cur.execute("PRAGMA table_info(ofertas)")}
    set_utf8 = ', descripcion_utf8=NULL' if 'descripcion_utf8' in cols else ''

    n_desc = n_nlp = n_m = n_s = 0
    for i in range(0, len(a_limpiar), 500):
        lote = a_limpiar[i:i + 500]
        cur.executemany(
            "INSERT OR REPLACE INTO descripcion_anulada_log VALUES (?,?,?,?)",
            [(str(o), d, MOTIVO, ahora) for o, d in lote])
        q = ','.join(str(o) for o, _ in lote)
        n_desc += cur.execute(
            f"UPDATE ofertas SET descripcion=NULL{set_utf8} WHERE id_oferta IN ({q})").rowcount
        # segunda generacion: solo donde exista (local)
        if 'ofertas_nlp' in tablas:
            n_nlp += cur.execute(f"DELETE FROM ofertas_nlp WHERE id_oferta IN ({q})").rowcount
        if 'ofertas_esco_skills_detalle' in tablas:
            n_s += cur.execute(f"DELETE FROM ofertas_esco_skills_detalle WHERE id_oferta IN ({q})").rowcount
        if 'ofertas_esco_matching' in tablas:
            n_m += cur.execute(f"DELETE FROM ofertas_esco_matching WHERE id_oferta IN ({q})").rowcount
        conn.commit()

    print(f'descripciones anuladas: {n_desc}')
    if 'ofertas_nlp' in tablas:
        print(f'filas NLP invalidadas: {n_nlp}')
        print(f'filas matching invalidadas: {n_m}')
        print(f'filas skills invalidadas: {n_s}')

    quedan = sum(1 for o, d in cur.execute(
        "SELECT id_oferta, descripcion FROM ofertas "
        "WHERE portal='computrabajo' AND descripcion IS NOT NULL") if es_texto_ui(d))
    print(f'verificacion post: texto de interfaz restante = {quedan}')
    conn.close()


if __name__ == '__main__':
    main()
