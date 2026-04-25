# -*- coding: utf-8 -*-
"""Tests para unlock_spec_h.py — unlock/relock de ofertas validado-estricto."""
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def db_tmp(tmp_path):
    """BD temporal con ofertas de distintos estados."""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    c.execute('''CREATE TABLE ofertas_esco_matching (
        id_oferta TEXT PRIMARY KEY,
        isco_code TEXT,
        decision_metodo TEXT,
        estado_validacion TEXT
    )''')
    c.executemany('''INSERT INTO ofertas_esco_matching VALUES (?,?,?,?)''', [
        ('V1', '5120', 'semantico_unico', 'validado'),       # scope: sí
        ('V2', '7214', 'semantico_unico', 'validado'),       # scope: sí
        ('V3', '8142', 'semantico_unico', 'validado'),       # scope: sí
        ('VC1', '2221', 'semantico_unico', 'validado_claude'),  # NO (ya se puede modificar)
        ('R1', '3322', 'regla_prioridad', 'validado'),       # NO (fuera de scope por regla)
    ])
    conn.commit()
    yield conn, str(db)
    conn.close()


def run_unlock(db_path, *args):
    """Wrapper para invocar el script."""
    script = ROOT / "scripts" / "embeddings" / "unlock_spec_h.py"
    cmd = ['python3', str(script), '--db', db_path, *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class TestUnlock:

    def test_status_vacio(self, db_tmp):
        _, db = db_tmp
        code, out, _ = run_unlock(db, '--status')
        assert code == 0
        assert 'Unlocked activos' in out
        assert 'scope candidato): 3' in out  # V1, V2, V3

    def test_dry_run_no_modifica(self, db_tmp):
        conn, db = db_tmp
        code, out, _ = run_unlock(db, '--dry-run')
        assert code == 0
        assert 'DRY-RUN' in out
        # Verificar que V1 sigue como 'validado'
        c = conn.cursor()
        c.execute('SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta=?', ('V1',))
        assert c.fetchone()[0] == 'validado'

    def test_unlock_cambia_a_en_revision(self, db_tmp):
        conn, db = db_tmp
        code, out, _ = run_unlock(db)
        assert code == 0
        conn2 = sqlite3.connect(db)
        c = conn2.cursor()
        c.execute('SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta IN ("V1","V2","V3")')
        estados = {r[0] for r in c.fetchall()}
        assert estados == {'en_revision'}
        conn2.close()

    def test_unlock_no_toca_validado_claude(self, db_tmp):
        conn, db = db_tmp
        run_unlock(db)
        conn2 = sqlite3.connect(db)
        c = conn2.cursor()
        c.execute('SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta="VC1"')
        assert c.fetchone()[0] == 'validado_claude'
        conn2.close()

    def test_unlock_no_toca_con_regla(self, db_tmp):
        conn, db = db_tmp
        run_unlock(db)
        conn2 = sqlite3.connect(db)
        c = conn2.cursor()
        c.execute('SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta="R1"')
        # R1 tiene decision_metodo=regla_prioridad → fuera de scope
        assert c.fetchone()[0] == 'validado'
        conn2.close()

    def test_unlock_ids_especificos(self, db_tmp):
        conn, db = db_tmp
        code, out, _ = run_unlock(db, '--ids', 'V1,V2')
        assert code == 0
        conn2 = sqlite3.connect(db)
        c = conn2.cursor()
        c.execute('SELECT id_oferta, estado_validacion FROM ofertas_esco_matching WHERE id_oferta IN ("V1","V2","V3")')
        estados = dict(c.fetchall())
        assert estados['V1'] == 'en_revision'
        assert estados['V2'] == 'en_revision'
        assert estados['V3'] == 'validado'  # no se pasó en --ids
        conn2.close()

    def test_relock_vuelve_a_validado(self, db_tmp):
        conn, db = db_tmp
        run_unlock(db)
        code, out, _ = run_unlock(db, '--relock')
        assert code == 0
        conn2 = sqlite3.connect(db)
        c = conn2.cursor()
        c.execute('SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta="V1"')
        assert c.fetchone()[0] == 'validado'
        # Verificar tracking
        c.execute('SELECT relock_at FROM spec_h_unlock_tracking WHERE id_oferta="V1"')
        relock = c.fetchone()[0]
        assert relock is not None
        conn2.close()

    def test_status_tras_unlock(self, db_tmp):
        _, db = db_tmp
        run_unlock(db)
        code, out, _ = run_unlock(db, '--status')
        assert 'Unlocked activos (en_revision): 3' in out

    def test_relock_idempotente(self, db_tmp):
        _, db = db_tmp
        run_unlock(db)
        run_unlock(db, '--relock')
        # Segundo relock no debe fallar
        code, out, _ = run_unlock(db, '--relock')
        assert code == 0
        assert 'Relockeando 0 ofertas' in out
