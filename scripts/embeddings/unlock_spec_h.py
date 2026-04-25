#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC H — Unlock batch de ofertas validadas estrictas antes del rematch.

Desbloquea ofertas con estado_validacion='validado' (las 3,364 protegidas por
el trigger protect_validated_matching) para permitir update de isco_code.
Cambia estado a 'en_revision' temporalmente. Después del rematch se puede
relockear con --relock.

Uso:
    python3 scripts/embeddings/unlock_spec_h.py           # unlock todas del scope
    python3 scripts/embeddings/unlock_spec_h.py --ids 123,456
    python3 scripts/embeddings/unlock_spec_h.py --relock  # volver a 'validado'
    python3 scripts/embeddings/unlock_spec_h.py --status  # ver qué está unlocked
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MOTIVO = 'SPEC H: rematch ISCO con embeddings enriquecidos SPEC E'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default=str(ROOT / 'database/bumeran_scraping.db'))
    p.add_argument('--ids', help='IDs específicos separados por coma')
    p.add_argument('--relock', action='store_true', help='Volver a validado')
    p.add_argument('--status', action='store_true', help='Solo mostrar stats')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    c = conn.cursor()

    # Tabla de tracking de unlocks
    c.execute('''CREATE TABLE IF NOT EXISTS spec_h_unlock_tracking (
        id_oferta TEXT PRIMARY KEY,
        estado_original TEXT,
        unlock_at TEXT,
        relock_at TEXT,
        motivo TEXT
    )''')
    conn.commit()

    if args.status:
        c.execute('SELECT COUNT(*) FROM spec_h_unlock_tracking WHERE relock_at IS NULL')
        unlocked = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM spec_h_unlock_tracking WHERE relock_at IS NOT NULL')
        relocked = c.fetchone()[0]
        c.execute('''SELECT COUNT(*) FROM ofertas_esco_matching
                     WHERE decision_metodo='semantico_unico' AND estado_validacion='validado' ''')
        restantes = c.fetchone()[0]
        print(f'Unlocked activos (en_revision): {unlocked}')
        print(f'Relocked (vueltos a validado): {relocked}')
        print(f'Con estado_validacion=validado + semantico_unico (scope candidato): {restantes}')
        conn.close(); return

    nowiso = datetime.now(timezone.utc).isoformat()

    if args.relock:
        # Relockear: volver los en_revision a validado
        c.execute('''SELECT id_oferta, estado_original FROM spec_h_unlock_tracking
                     WHERE relock_at IS NULL''')
        rows = c.fetchall()
        print(f'Relockeando {len(rows)} ofertas...')
        if args.dry_run:
            print('DRY-RUN')
            conn.close(); return
        for oid, estado_orig in rows:
            # Volver al estado original
            c.execute('UPDATE ofertas_esco_matching SET estado_validacion = ? WHERE id_oferta = ?',
                      (estado_orig, str(oid)))
            c.execute('UPDATE spec_h_unlock_tracking SET relock_at = ? WHERE id_oferta = ?',
                      (nowiso, str(oid)))
        conn.commit()
        print(f'✓ Relockeadas {len(rows)}')
        conn.close(); return

    # Unlock: pasar 'validado' → 'en_revision'
    if args.ids:
        ids_list = args.ids.split(',')
        placeholders = ','.join('?' for _ in ids_list)
        c.execute(f'''SELECT id_oferta, estado_validacion FROM ofertas_esco_matching
                      WHERE id_oferta IN ({placeholders})
                        AND estado_validacion = 'validado' ''', ids_list)
    else:
        # Scope completo: todas las semantico_unico + validado
        c.execute('''SELECT id_oferta, estado_validacion FROM ofertas_esco_matching
                     WHERE decision_metodo = 'semantico_unico'
                       AND estado_validacion = 'validado' ''')
    rows = c.fetchall()
    print(f'Ofertas a unlockear: {len(rows)}')
    if args.dry_run:
        print('DRY-RUN — no persiste')
        conn.close(); return

    for oid, estado in rows:
        c.execute('''INSERT OR REPLACE INTO spec_h_unlock_tracking
                     (id_oferta, estado_original, unlock_at, motivo)
                     VALUES (?, ?, ?, ?)''',
                  (str(oid), estado, nowiso, MOTIVO))
        # Cambiar estado (el trigger permite validado → en_revision)
        c.execute('''UPDATE ofertas_esco_matching SET estado_validacion = 'en_revision'
                     WHERE id_oferta = ? AND estado_validacion = 'validado' ''', (str(oid),))
    conn.commit()
    print(f'✓ Unlocked {len(rows)} ofertas (motivo: {MOTIVO})')
    conn.close()


if __name__ == '__main__':
    main()
