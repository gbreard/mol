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
    # v0.3.3: +hit de inclusion para que el guard P2a no intervenga (intencion = orden)
    r = t.evaluar('Analista contable', _c(tareas='analizar estados financieros; emitir facturas y liquidar nomina'))
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
    r = t.evaluar('Analista contable', _c(tareas='analizar estados financieros; registrar operaciones; puesto sin experiencia'))
    # D01 satisfecha pero excluida -> sigue a D02, que decide
    assert r['decide'] and r['regla_id'] == 'D02' and r['codigo_esco'] == '3000.1'


def test_06_convergencia_multi_hub():
    # titulo activa A y B; D01 de A redirige a B; inclusion de B se acepta
    hub_a = _hub('1000.1', 1, ['analista contable bilingue'], ['analizar estados'],
                 [_d('D01', 1, 'alguna', ['registrar operaciones', 'conciliaciones'], '2000.1')])
    hub_b = _hub('2000.1', 2, ['analista contable bilingue'], ['registrar operaciones'], [])
    t = _traductor([hub_a, hub_b])
    r = t.evaluar('Analista contable bilingue', _c(tareas='registrar operaciones diarias; conciliaciones'))
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
    # v0.3.3: +hit de inclusion (el guard no interviene; la intencion es el empate)
    r = t.evaluar('Analista contable', _c(tareas='analizar estados financieros; registrar operaciones; emitir facturas'))
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


def test_13_overlay_lexico_compila_regla_semantica():
    # una regla que llega semantica del JSON 2.0 se vuelve ejecutable via lexico
    hub = _hub('1000.1', 1, ['vendedor'], [], [
        {'regla_id': 'D01', 'orden': 1, 'condicion_prosa': 'prosa de Cyn intacta',
         'condicion_operacional': {'modo': 'evaluacion_semantica_del_nucleo', 'terminos': []},
         'ocupacion_destino': {'codigo_esco': '2000.1'}}])
    lexico = {'hubs': {'1000.1': {'D01': {'modo': 'alguna', 'terminos': ['reposicion'],
                                          'tecnologia_definitoria': False}}}}
    t = TraductorContexto(hubs_data={'ocupaciones': [hub]}, hubs_activos=['1000.1'],
                          exclusiones_trigger=[], catalogo_codes=CATALOGO, lexico=lexico)
    r = t.evaluar('Vendedor', _c(tareas='reposicion de gondolas'))
    assert r['decide'] and r['codigo_esco'] == '2000.1' and r['regla_id'] == 'D01'
    # la prosa sigue intacta en el hub
    assert hub['reglas_desambiguacion'][0]['condicion_prosa'] == 'prosa de Cyn intacta'


# ── LAUDO L1 (H_v032, 2026-08-14): la inclusion participa del comparativo ──

HUB_VND = _hub('5000.1', 51, ['vendedor'],
               ['venta de salon', 'asesorar', 'atencion al cliente', 'concretar ventas'],
               [_d('D07', 7, 'principalmente', ['manejo de caja', 'cobros', 'arqueo'], '2000.1')])


def test_13_L1_caso_testigo_vendedor_con_caja_NO_va_a_cajero():
    """4 tareas de venta + 1 mencion de caja: la actividad principal es venta.
    D07 (principalmente) ya no puede ganar por ser la unica hermana que matcheo —
    la INCLUSION participa del comparativo y domina el conteo."""
    t = _traductor([HUB_VND])
    r = t.evaluar('Vendedor', _c(
        tareas='venta de salon; asesorar clientes; atencion al cliente; concretar ventas; apoyo en manejo de caja'))
    assert r['decide'], r
    assert r['regla_id'] == 'inclusion' and r['codigo_esco'] == '5000.1', r


def test_14_L1_caja_dominante_SI_redirige():
    """El caso inverso: si la caja domina el conteo, D07 redirige como siempre."""
    t = _traductor([HUB_VND])
    r = t.evaluar('Vendedor', _c(
        tareas='manejo de caja; cobros; arqueo diario; venta de salon ocasional'))
    assert r['decide'] and r['regla_id'] == 'D07' and r['codigo_esco'] == '2000.1', r


def test_15_L1_no_toca_solo_estas():
    """solo_estas no cambia (letra del laudo: solo el modo comparativo)."""
    hub = _hub('1000.1', 1, ['analista contable'], ['analizar estados financieros'],
               [_d('D01', 1, 'solo_estas', ['cargar datos', 'archivo'], '2000.1')])
    t = _traductor([hub])
    r = t.evaluar('Analista contable', _c(tareas='cargar datos y archivo'))
    assert r['decide'] and r['regla_id'] == 'D01', r


# ── PRE-v0.3.3: paridad de género «/a» en triggers (bug, no fase 2) ──

def test_16_titulo_con_barra_de_genero_dispara_trigger():
    """«Vendedor/a» (barra compacta, como se escribe en los avisos reales)
    dispara el trigger del hub vendedor igual que «Vendedor»."""
    t = _traductor([HUB_VND])
    r = t.evaluar('Vendedor/a', _c(tareas='venta de salon y atencion al cliente'))
    assert r['telemetria'] != 'no_aplica', r
    assert r['decide'] and r['codigo_esco'] == '5000.1', r


def test_17_barra_compuesta_tambien():
    """«Ejecutivo/a comercial»-style: la barra interna no corta el word-boundary."""
    hub = _hub('3000.1', 16, ['ejecutivo/a comercial'], ['prospeccion'], [])
    t = _traductor([hub])
    r = t.evaluar('Ejecutivo/a comercial B2B', _c(tareas='prospeccion de clientes'))
    assert r['decide'] and r['codigo_esco'] == '3000.1', r


# ── v0.3.3 (laudos H_v033): P1 satelite-exacto + interaccion P1xP2 + guard P2a ──

HUB_V33 = _hub('5000.1', 51, ['vendedor'],
               ['venta de salon', 'asesorar', 'atencion al cliente', 'concretar ventas'],
               [_d('D07', 7, 'alguna', ['manejo de caja', 'cobros', 'arqueo'], '2000.1'),
                _d('D09', 9, 'alguna', ['liquidar sueldos', 'legajos'], '3000.1')])
SATS = {'cajero': '2000.1', 'camarero': '4000.1'}


def _t33(hubs, sats=SATS):
    return TraductorContexto(hubs_data={'ocupaciones': hubs},
                             hubs_activos=[h['codigo_esco'] for h in hubs],
                             exclusiones_trigger=[], catalogo_codes=CATALOGO,
                             satelites=sats)


def _con_trigger_cajero(t):
    t._triggers.append(('cajero', '5000.1'))
    t._triggers.append(('camarero', '5000.1'))
    return t


def test_18_testigo1_satelite_confirmatorio_1_hit():
    """«Cajero/a» + tareas mayormente venta + 1 mencion de caja: D07 (destino ==
    satelite del titulo) redirige con 1 hit — confirmatorio."""
    t = _con_trigger_cajero(_t33([HUB_V33]))
    r = t.evaluar('Cajero/a', _c(
        tareas='venta de salon; asesorar; atencion al cliente; concretar ventas; manejo de caja'))
    assert r['decide'] and r['regla_id'] == 'D07' and r['codigo_esco'] == '2000.1', r


def test_19_testigo2_satelite_d_contraria_necesita_2():
    """«Cajero/a» + 1 mencion de RRHH (D hacia OTRO destino) -> NO redirige -> abstencion."""
    t = _con_trigger_cajero(_t33([HUB_V33]))
    r = t.evaluar('Cajero/a', _c(tareas='legajos del personal'))
    assert not r['decide'] and r['telemetria'] == 'satelite_exacto_abstencion', r
    assert r['satelite'] == '2000.1'


def test_20_testigo3_satelite_sin_D_abstencion():
    """«Camarero/a» sin D matcheada -> abstencion (la inclusion NO participa)."""
    t = _con_trigger_cajero(_t33([HUB_V33]))
    r = t.evaluar('Camarero/a', _c(tareas='atencion al cliente y concretar ventas'))
    assert not r['decide'] and r['telemetria'] == 'satelite_exacto_abstencion', r
    assert r['satelite'] == '4000.1'
    incl = [x for h in r['traza']['hubs_activados'] for x in h['reglas'] if x['regla_id'] == 'inclusion']
    assert incl and incl[0]['estado'] == 'satelite_exacto_no_participa'


def test_21_testigo4_guard_1a0():
    """«vendedor en calle» + 'cobros' (D caja 1 hit, inclusion 0) -> familia_sin_rama + tag."""
    t = _t33([HUB_V33], sats={})
    r = t.evaluar('vendedor en calle', _c(tareas='desarrollar catalogo; saldos y cobros'))
    assert not r['decide'] and r['telemetria'] == 'familia_sin_rama', r
    assert r['traza'].get('tag_guard_1a0') is True
    d07 = [x for h in r['traza']['hubs_activados'] for x in h['reglas'] if x['regla_id'] == 'D07']
    assert d07[0]['estado'] == 'guard_1a0_bloqueo'


def test_22_testigo5_dos_terminos_distintos_redirige():
    """El mismo caso con 2 terminos DISTINTOS de caja -> la D redirige legitimo."""
    t = _t33([HUB_V33], sats={})
    r = t.evaluar('vendedor en calle', _c(tareas='cobros diarios; arqueo de caja'))
    assert r['decide'] and r['regla_id'] == 'D07' and r['codigo_esco'] == '2000.1', r


# ── v0.3.4 (paquete final): A1-bis term-set unico + A2 confirmatorias-primero ──

def test_23_A1bis_identidad_de_objeto_del_term_set():
    """Las dos referencias (D11.terminos y D08/D10.excluye) apuntan al MISMO objeto
    (patron BOILERPLATE_RE): si pueden driftear, driftean."""
    import json as _json
    from pathlib import Path as _P
    lex = _json.load(open(_P(__file__).resolve().parents[2] / 'config' / 'lexico_traductor.json'))
    t = TraductorContexto(hubs_activos=['5223.4'], exclusiones_trigger=[], lexico=lex)
    ds = {r['regla_id']: r['condicion_operacional']
          for r in t.hubs['5223.4']['reglas_desambiguacion']
          if r.get('regla_id') in ('D08', 'D10', 'D11')}
    assert ds['D11']['terminos'] is ds['D08']['excluye']
    assert ds['D08']['excluye'] is ds['D10']['excluye']
    assert ds['D08'].get('excluye_tag') == 'excluye_venta_externa'


HUB_A1B = _hub('5000.1', 51, ['vendedor'],
               ['venta de salon', 'concretar ventas'],
               [_d('D08', 8, 'min_matches', ['reclamos', 'gestion de reclamos'], '2000.1', minimo=2),
                _d('D11', 11, 'min_matches', ['visitas presenciales', 'cartera de clientes'], '3000.1', minimo=2)])
# el set unico, cableado como lo hace el resolver
_SET = ['visitas presenciales', 'cartera de clientes', 'recorrer zonas']
for _r in HUB_A1B['reglas_desambiguacion']:
    if _r['regla_id'] == 'D08':
        _r['condicion_operacional']['excluye'] = _SET
        _r['condicion_operacional']['excluye_tag'] = 'excluye_venta_externa'
    if _r['regla_id'] == 'D11':
        _r['condicion_operacional']['terminos'] = _SET


def test_24_A1bis_testigo_bonus_lubricantes():
    """Vendedor viajante con visitas/cartera + reclamos: el excluye bloquea D08,
    cae a D11 -> 3000.1 (la mejora, no solo la no-regresion)."""
    t = _traductor([HUB_A1B])
    r = t.evaluar('Vendedor', _c(
        tareas='visitas presenciales a clientes; cartera de clientes; atencion de reclamos; gestion de reclamos'))
    assert r['decide'] and r['regla_id'] == 'D11' and r['codigo_esco'] == '3000.1', r
    d08 = [x for h in r['traza']['hubs_activados'] for x in h['reglas'] if x['regla_id'] == 'D08']
    assert d08[0]['estado'] == 'excluye_venta_externa'


def test_25_A1bis_testigo_riesgo_documentado():
    """Teleoperador genuino con 'cartera' al pasar: D08 bloqueada por el set,
    D11 no llega a 2 -> familia_sin_rama (la plana decide por subordinacion) + tag visible."""
    t = _traductor([HUB_A1B])
    r = t.evaluar('Vendedor', _c(tareas='gestion de reclamos; reclamos diarios; cartera de clientes al pasar'))
    assert not r['decide'], r
    d08 = [x for h in r['traza']['hubs_activados'] for x in h['reglas'] if x['regla_id'] == 'D08']
    assert d08[0]['estado'] == 'excluye_venta_externa'


def test_26_A2_confirmatoria_primero_en_modo_satelite():
    """El caso de la v3: la D-contraria (orden 1, 2 hits) ya no gana por orden —
    la confirmatoria (destino == satelite) se evalua primero."""
    hub = _hub('5000.1', 51, ['vendedor'],
               ['venta de salon'],
               [_d('D01', 1, 'alguna', ['reposicion', 'control de stock'], '3000.1'),
                _d('D07', 7, 'alguna', ['cobro en linea de cajas', 'cierre de caja'], '2000.1')])
    t = _t33([hub], sats={'cajera': '2000.1'})
    t._triggers.append(('cajera', '5000.1'))
    r = t.evaluar('Cajera', _c(tareas='cobro en linea de cajas; reposicion de mercaderia; control de stock'))
    assert r['decide'] and r['regla_id'] == 'D07' and r['codigo_esco'] == '2000.1', r
