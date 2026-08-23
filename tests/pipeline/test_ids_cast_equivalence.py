"""Equivalencia de conjuntos: las queries nuevas (NOT EXISTS/NOT IN con CAST)
de get_ids_without_nlp / get_ids_with_nlp_errors devuelven EXACTAMENTE el mismo
conjunto que los LEFT JOIN originales, sobre una fixture que cubre los casos
limite del cruce de afinidades (ofertas.id_oferta INTEGER vs TEXT en el resto).

Hallazgo de origen: backlog NLP 2026-08-20 — el LEFT JOIN sin CAST degeneraba
en nested loop >15 min; el rewrite es por performance, no puede cambiar el set.
"""
import sqlite3

import pytest

OLD_WITHOUT_NLP = '''
    SELECT o.id_oferta FROM ofertas o
    LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
    LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
    WHERE n.id_oferta IS NULL
    AND (m.estado_validacion IS NULL OR m.estado_validacion != 'validado')
'''
NEW_WITHOUT_NLP = '''
    SELECT o.id_oferta FROM ofertas o
    WHERE NOT EXISTS (
        SELECT 1 FROM ofertas_nlp n
        WHERE n.id_oferta = CAST(o.id_oferta AS TEXT))
    AND CAST(o.id_oferta AS TEXT) NOT IN (
        SELECT id_oferta FROM ofertas_esco_matching
        WHERE estado_validacion = 'validado')
'''
OLD_NLP_ERRORS = '''
    SELECT DISTINCT ve.id_oferta FROM validation_errors ve
    LEFT JOIN ofertas_esco_matching m ON ve.id_oferta = m.id_oferta
    WHERE ve.resuelto = 0
    AND ve.error_tipo LIKE 'error_nlp_%'
    AND (m.estado_validacion IS NULL OR m.estado_validacion != 'validado')
'''
NEW_NLP_ERRORS = '''
    SELECT DISTINCT ve.id_oferta FROM validation_errors ve
    WHERE ve.resuelto = 0
    AND ve.error_tipo LIKE 'error_nlp_%'
    AND ve.id_oferta NOT IN (
        SELECT id_oferta FROM ofertas_esco_matching
        WHERE estado_validacion = 'validado')
'''


@pytest.fixture()
def db():
    con = sqlite3.connect(':memory:')
    con.executescript('''
        CREATE TABLE ofertas (id_oferta INTEGER PRIMARY KEY);
        CREATE TABLE ofertas_nlp (id_oferta TEXT PRIMARY KEY);
        CREATE TABLE ofertas_esco_matching (id_oferta TEXT PRIMARY KEY, estado_validacion TEXT);
        CREATE TABLE validation_errors (id_oferta TEXT, error_tipo TEXT, resuelto INTEGER);
    ''')
    # Casos: 1 sin nada · 2 con NLP · 3 sin NLP + matching validado ·
    # 4 sin NLP + matching pendiente · 5 sin NLP + matching estado NULL ·
    # 6 con NLP + validado · 7 id gigante (prefijo 8_000M, TEXT largo) sin NLP
    con.executescript('''
        INSERT INTO ofertas VALUES (1),(2),(3),(4),(5),(6),(8000000001);
        INSERT INTO ofertas_nlp VALUES ('2'),('6');
        INSERT INTO ofertas_esco_matching VALUES
            ('3','validado'),('4','pendiente'),('5',NULL),('6','validado');
        INSERT INTO validation_errors VALUES
            ('4','error_nlp_seniority',0),   -- pendiente, matching no validado -> entra
            ('3','error_nlp_area',0),        -- matching validado -> NO entra
            ('1','error_nlp_ubicacion',0),   -- sin matching -> entra
            ('4','error_matching_isco',0),   -- no es error_nlp_% -> NO entra
            ('5','error_nlp_tareas',1);      -- resuelto -> NO entra
    ''')
    return con


def sets(con, q):
    return {str(r[0]) for r in con.execute(q)}


def test_without_nlp_equivalencia(db):
    viejo = sets(db, OLD_WITHOUT_NLP)
    nuevo = sets(db, NEW_WITHOUT_NLP)
    assert nuevo == viejo
    # y el conjunto es el esperado: sin NLP y no-validadas
    assert nuevo == {'1', '4', '5', '8000000001'}


def test_nlp_errors_equivalencia(db):
    viejo = sets(db, OLD_NLP_ERRORS)
    nuevo = sets(db, NEW_NLP_ERRORS)
    assert nuevo == viejo
    assert nuevo == {'1', '4'}


def test_produccion_usa_queries_nuevas():
    """Las queries del modulo en produccion son las validadas aca."""
    src = open('scripts/run_validated_pipeline.py', encoding='utf-8').read()
    assert 'n.id_oferta = CAST(o.id_oferta AS TEXT)' in src
    assert 've.id_oferta NOT IN' in src
    # y los LEFT JOIN viejos ya no existen
    assert 'LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta' not in src
    assert 'LEFT JOIN ofertas_esco_matching m ON ve.id_oferta = m.id_oferta' not in src
