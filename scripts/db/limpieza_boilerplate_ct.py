#!/usr/bin/env python3
"""[FRENTE J follow-up, 2026-08-06] Limpieza retroactiva del boilerplate SEO de CT.

El scraper guardo la meta-description de CT ("¿Buscas trabajo de X? Crea tu CV
gratis...") como descripcion real (may-ago/2026, ver
exports/reportes/J_fix_scraper_ct_2026-08-05.md). Este script:

  1. Detecta las ofertas cuya descripcion matchea EL MISMO regex de la guarda del
     scraper (una sola fuente del patron: ComputRabajoScraper.BOILERPLATE_RE).
  2. Excluye cualquier oferta con validacion HUMANA (estado 'validado' /
     'validado_humano') — el trabajo humano jamas se borra por barrido.
  3. Anula la descripcion (NULL) dejando registro trazable con el texto original
     en la tabla `descripcion_anulada_log` (auditable y reversible).
  4. Invalida la segunda generacion: borra sus filas de ofertas_nlp,
     ofertas_esco_matching y ofertas_esco_skills_detalle (derivadas de basura).
     DELETE es el mecanismo idiomatico: el pipeline las regenera si la
     descripcion vuelve; con NULL no re-entran al backlog (filtro desc>100).

Uso: python scripts/db/limpieza_boilerplate_ct.py [--dry-run] [--db PATH]
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / '01_sources' / 'computrabajo' / 'scrapers'))
from computrabajo_scraper import ComputRabajoScraper  # noqa: E402

BOILERPLATE_RE = ComputRabajoScraper.BOILERPLATE_RE  # fuente unica del patron
ESTADOS_HUMANOS = ('validado', 'validado_humano')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--db', default=str(REPO / 'database' / 'bumeran_scraping.db'))
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=120)
    cur = conn.cursor()

    # 1. deteccion (regex compartido, en Python — LIKE no alcanza para el patron)
    candidatas = []
    for oid, desc in cur.execute(
            "SELECT id_oferta, descripcion FROM ofertas "
            "WHERE descripcion IS NOT NULL AND LENGTH(descripcion) < 400"):
        if desc and BOILERPLATE_RE.search(desc):
            candidatas.append((oid, desc))
    print(f'detectadas con patron boilerplate: {len(candidatas)}')

    # 2. guarda del trabajo humano
    ids = [str(o) for o, _ in candidatas]
    humanas = set()
    for i in range(0, len(ids), 500):
        q = ','.join(ids[i:i + 500])
        for (o,) in cur.execute(
                f"SELECT id_oferta FROM ofertas_esco_matching "
                f"WHERE id_oferta IN ({q}) AND estado_validacion IN {ESTADOS_HUMANOS}"):
            humanas.add(str(o))
    if humanas:
        print(f'⚠ EXCLUIDAS por validacion humana (intocables): {len(humanas)}')
        for h in sorted(humanas):
            print(f'   {h}')
    a_limpiar = [(o, d) for o, d in candidatas if str(o) not in humanas]
    print(f'a limpiar: {len(a_limpiar)}')

    if args.dry_run:
        n_nlp = n_m = n_s = 0
        idsl = [str(o) for o, _ in a_limpiar]
        for i in range(0, len(idsl), 500):
            q = ','.join(idsl[i:i + 500])
            n_nlp += cur.execute(f"SELECT COUNT(*) FROM ofertas_nlp WHERE id_oferta IN ({q})").fetchone()[0]
            n_m += cur.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({q})").fetchone()[0]
            n_s += cur.execute(f"SELECT COUNT(*) FROM ofertas_esco_skills_detalle WHERE id_oferta IN ({q})").fetchone()[0]
        print(f'[dry] se anularian {len(a_limpiar)} descripciones; se borrarian '
              f'{n_nlp} filas NLP, {n_m} matching, {n_s} skills')
        return

    # 3. registro trazable + anulacion
    cur.execute("""CREATE TABLE IF NOT EXISTS descripcion_anulada_log (
        id_oferta TEXT PRIMARY KEY,
        descripcion_original TEXT,
        motivo TEXT,
        anulada_en TEXT)""")
    ahora = datetime.now().isoformat()
    n_desc = n_nlp = n_m = n_s = 0
    for i in range(0, len(a_limpiar), 500):
        lote = a_limpiar[i:i + 500]
        cur.executemany(
            "INSERT OR REPLACE INTO descripcion_anulada_log VALUES (?,?,?,?)",
            [(str(o), d, 'boilerplate_seo_ct', ahora) for o, d in lote])
        q = ','.join(str(o) for o, _ in lote)
        n_desc += cur.execute(
            f"UPDATE ofertas SET descripcion=NULL, descripcion_utf8=NULL "
            f"WHERE id_oferta IN ({q})").rowcount
        # 4. segunda generacion
        n_nlp += cur.execute(f"DELETE FROM ofertas_nlp WHERE id_oferta IN ({q})").rowcount
        n_s += cur.execute(f"DELETE FROM ofertas_esco_skills_detalle WHERE id_oferta IN ({q})").rowcount
        n_m += cur.execute(f"DELETE FROM ofertas_esco_matching WHERE id_oferta IN ({q})").rowcount
        conn.commit()
    print(f'descripciones anuladas: {n_desc}')
    print(f'filas NLP invalidadas: {n_nlp}')
    print(f'filas matching invalidadas: {n_m}')
    print(f'filas skills invalidadas: {n_s}')

    # 5. verificacion: cero boilerplate vivo
    quedan = 0
    for oid, desc in cur.execute(
            "SELECT id_oferta, descripcion FROM ofertas "
            "WHERE descripcion IS NOT NULL AND LENGTH(descripcion) < 400"):
        if desc and BOILERPLATE_RE.search(desc):
            quedan += 1
    print(f'verificacion post: boilerplate vivo restante = {quedan}')
    conn.close()


if __name__ == '__main__':
    main()
