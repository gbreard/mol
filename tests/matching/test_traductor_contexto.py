# Los 12 casos borde del contrato laudado del traductor (FRENTE H, P1, 2026-08-06).
# Semántica post re-laudo hub-set: combinación por vecindario dinámico (test 8 = 8a/8b).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'database'))
from traductor_contexto import TraductorContexto

CATALOGO = {'1000.1', '2000.1', '3000.1', '4000.1', '5000.1'}


def _hub(codigo, id_, titulos, inclusion_terms, ds):
    return {'id': id_, 'codigo_esco': codigo, 'ocupacion_esco': f'hub {id_}',
            'titulos_aviso': titulos,
            'regla_inclusion': {'condicion_prosa': 'prosa inclusion',
                                'condicion_operacional': {'campo': 'contenidos', 'modo': 'alguna',
                                                          'terminos': inclusion_terms}},
            'reglas_desambiguacion': ds}


def _d(rid, orden, modo, terminos, destino, minimo=2, excluye=None, tec_def=False):
    d = {'regla_id': rid, 'orden': orden, 'condicion_prosa': f'prosa {rid}',
         'condicion_operacional': {'campo': 'contenidos', 'modo': modo, 'terminos': terminos,
                                   'minimo': minimo},
         'ocupacion_destino': {'codigo_esco': destino}}
    if excluye:
        d['condicion_operacional']['excluye'] = excluye
    if tec_def:
        d['tecnologia_definitoria'] = True
    return d


def _traductor(hubs, activos=None):
    return TraductorContexto(hubs_data={'ocupaciones': hubs},
                             hubs_activos=activos or [h['codigo_esco'] for h in hubs],
                             exclusiones_trigger=[],
                             catalogo_codes=CATALOGO)


def _c(tareas='', skills='', conocimientos='', tecnologias='', sistemas=''):
    return {'tareas_explicitas': tareas, 'skills_habilidades': skills,
            'conocimientos': conocimientos, 'tecnologias': tecnologias,
            'sistemas_herramientas': sistemas}


HUB_A = _hub('1000.1', 1, ['analista contable'], ['analizar estados financieros'],
             [_d('D01', 1, 'alguna', ['registrar operaciones'], '2000.1'),
              _d('D02', 2, 'alguna', ['emitir facturas'], '3000.1'),
              _d('D05', 5, 'alguna', ['emitir facturas', 'liquidar nomina'], '4000.1')])
HUB_B = _hub('2000.1', 2, ['administrativo contable'], ['registrar operaciones'], [])


def test_01_sin_contenidos_evaluables_no_forzar():
    t = _traductor([HUB_A])
    r = t.evaluar('Analista contable', _c())
    assert not r['decide'] and r['telemetria'] == 'familia_sin_rama'


def test_02_orden_de_D_es_precedencia():
    # D02 (orden 2) y D05 (orden 5) ambas satisfechas -> decide D02
    t = _traductor([HUB_A])
    r = t.evaluar('Analista contable', _c(tareas='emitir facturas y liquidar nomina'))
    assert r['decide'] and r['regla_id'] == 'D02' and r['codigo_esco'] == '3000.1'


def test_03_inclusion_decide_si_ninguna_D():
    t = _traductor([HUB_A])
    r = t.evaluar('Analista contable', _c(tareas='analizar estados financieros del grupo'))
    assert r['decide'] and r['regla_id'] == 'inclusion' and r['codigo_esco'] == '1000.1'
    assert r['camino'] == 'inclusion'


def test_04_ni_D_ni_inclusion_familia_sin_rama():
    t = _traductor([HUB_A])
    r = t.evaluar('Analista contable', _c(tareas='conducir camiones de larga distancia'))
    assert not r['decide'] and r['telemetria'] == 'familia_sin_rama'


def test_05_excluye_corta_y_la_evaluacion_sigue():
    hub = _hub('1000.1', 1, ['analista contable'], ['analizar estados financieros'],
               [_d('D01', 1, 'alguna', ['registrar operaciones'], '2000.1',
                   excluye=['sin experiencia']),
                _d('D02', 2, 'alguna', ['registrar operaciones'], '3000.1')])
    t = _traductor([hub])
    r = t.evaluar('Analista contable', _c(tareas='registrar operaciones; puesto sin experiencia'))
    # D01 satisfecha pero excluida -> sigue a D02, que decide
    assert r['decide'] and r['regla_id'] == 'D02' and r['codigo_esco'] == '3000.1'


def test_06_convergencia_multi_hub():
    # titulo activa A y B; D01 de A redirige a B; inclusion de B se acepta
    hub_a = _hub('1000.1', 1, ['analista contable bilingue'], ['analizar estados'],
                 [_d('D01', 1, 'alguna', ['registrar operaciones'], '2000.1')])
    hub_b = _hub('2000.1', 2, ['analista contable bilingue'], ['registrar operaciones'], [])
    t = _traductor([hub_a, hub_b])
    r = t.evaluar('Analista contable bilingue', _c(tareas='registrar operaciones diarias'))
    assert r['decide'] and r['codigo_esco'] == '2000.1' and r['camino'] == 'convergencia'


def test_07_divergencia_evidencia_mixta():
    hub_a = _hub('1000.1', 1, ['analista contable'], ['registrar operaciones'], [])
    hub_b = _hub('3000.1', 3, ['analista contable'], ['registrar operaciones'], [])
    t = _traductor([hub_a, hub_b])
    r = t.evaluar('Analista contable', _c(tareas='registrar operaciones'))
    # ambos proponen su propio codigo -> destinos distintos
    assert not r['decide'] and r['telemetria'] == 'evidencia_mixta'
    assert sorted(r['traza']['destinos_en_conflicto']) == ['1000.1', '3000.1']


def test_08a_dos_hubs_sin_relacion_solo_uno_satisface_decide():
    # re-laudo: resolucion por evidencia — el atajo "sin evaluar" NO existe
    hub_a = _hub('1000.1', 1, ['tecnico'], ['reparar tableros electricos'], [])
    hub_b = _hub('4000.1', 4, ['tecnico'], ['cuidar pacientes internados'], [])
    t = _traductor([hub_a, hub_b])
    r = t.evaluar('Tecnico', _c(tareas='reparar tableros electricos en planta'))
    assert r['decide'] and r['codigo_esco'] == '1000.1'
    assert len(r['traza']['hubs_activados']) == 2  # ambos evaluados, con traza


def test_08b_dos_hubs_sin_relacion_ambos_satisfacen_evidencia_mixta():
    hub_a = _hub('1000.1', 1, ['tecnico'], ['reparar tableros'], [])
    hub_b = _hub('4000.1', 4, ['tecnico'], ['cuidar pacientes'], [])
    t = _traductor([hub_a, hub_b])
    r = t.evaluar('Tecnico', _c(tareas='reparar tableros y cuidar pacientes'))
    assert not r['decide'] and r['telemetria'] == 'evidencia_mixta'


def test_09_guarda_a_tecnologia_no_definitoria():
    hub_sin = _hub('1000.1', 1, ['analista contable'], [],
                   [_d('D01', 1, 'alguna', ['sap fi'], '2000.1')])
    t = _traductor([hub_sin])
    r = t.evaluar('Analista contable', _c(tecnologias='sap fi'))
    assert not r['decide']  # matches SOLO en tecnologias, sin declaracion -> no satisface
    hub_con = _hub('1000.1', 1, ['analista contable'], [],
                   [_d('D01', 1, 'alguna', ['sap fi'], '2000.1', tec_def=True)])
    t2 = _traductor([hub_con])
    r2 = t2.evaluar('Analista contable', _c(tecnologias='sap fi'))
    assert r2['decide'] and r2['codigo_esco'] == '2000.1'


def test_10_guarda_b_traza_registra_campo_por_match():
    t = _traductor([HUB_A])
    r = t.evaluar('Analista contable', _c(tareas='emitir facturas'))
    hub_traza = r['traza']['hubs_activados'][0]
    d02 = next(x for x in hub_traza['reglas'] if x['regla_id'] == 'D02')
    assert d02['matches'] == [{'termino': 'emitir facturas', 'campo': 'tareas_explicitas'}]


def test_11_principalmente_empate_no_decide():
    hub = _hub('1000.1', 1, ['analista contable'], ['analizar estados financieros'],
               [_d('D01', 1, 'principalmente', ['registrar operaciones'], '2000.1'),
                _d('D02', 2, 'alguna', ['emitir facturas'], '3000.1')])
    t = _traductor([hub])
    # empate 1-1 entre D01 y su hermana D02 -> D01 no decide; D02 (alguna) si
    r = t.evaluar('Analista contable', _c(tareas='registrar operaciones; emitir facturas'))
    assert r['decide'] and r['regla_id'] == 'D02'


def test_12_regla_sin_compilar_es_inactiva():
    hub = _hub('1000.1', 1, ['analista contable'], ['analizar estados financieros'], [
        {'regla_id': 'D01', 'orden': 1, 'condicion_prosa': 'prosa semantica',
         'condicion_operacional': {'campo': 'contenidos',
                                   'modo': 'evaluacion_semantica_del_nucleo', 'terminos': []},
         'ocupacion_destino': {'codigo_esco': '2000.1'}}])
    t = _traductor([hub])
    r = t.evaluar('Analista contable', _c(tareas='analizar estados financieros'))
    # la D semantica NO evalua ni decide; la inclusion decide
    assert r['decide'] and r['regla_id'] == 'inclusion'
    hub_traza = r['traza']['hubs_activados'][0]
    d01 = next(x for x in hub_traza['reglas'] if x['regla_id'] == 'D01')
    assert d01['estado'] == 'regla_sin_compilar'
