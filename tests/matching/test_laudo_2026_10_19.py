# -*- coding: utf-8 -*-
"""[CASCADA cierre P3] Tests de los laudos finales de Cyn (2026-10-19) en el evaluador del árbol:
LAUDO 1 (núcleo funcional: complementarias no cuentan) + LAUDO 2 (D10 no dispara por atención
telefónica) + LAUDO 3 (equivalencias comerciales con matiz). Evaluador con mini-frente ON."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'config'))
sys.path.insert(0, str(ROOT / 'database'))
from traductor_contexto import (TraductorContexto, _NO_NUCLEO, _D10_ATENCION_TEL,  # noqa: E402
                                _sinonimo_comercial_en_texto, _term_equiv_en_texto)


def _tc(equiv):
    base = ROOT / 'config'
    excl = json.load(open(base / 'traductor_exclusiones_trigger.json'))['exclusiones']
    piso = json.load(open(base / 'traductor_piso_satelites.json'))['triggers']
    sats = {}
    for t in piso:
        sats.setdefault(t['trigger'], t['satelite'])
    tc = TraductorContexto(exclusiones_trigger=excl, satelites=sats, equivalencia_funcional=equiv)
    ya = {t for t, _ in tc._triggers}
    tc._triggers += [(t['trigger'], t['hub']) for t in piso if t['trigger'] not in ya]
    return tc


def _cont(tareas):
    return {'tareas_explicitas': tareas, 'skills_habilidades': '', 'conocimientos': '',
            'tecnologias': '', 'sistemas_herramientas': ''}


def test_laudo1_complementarias_en_no_nucleo():
    for t in ['atencion al cliente', 'atender clientes', 'identificar necesidades', 'delivery']:
        assert t in _NO_NUCLEO
    for t in ['por telefono', 'llamadas telefonicas', 'atencion telefonica']:  # LAUDO 2 (set D10)
        assert t in _D10_ATENCION_TEL


def test_laudo1_cajero_nucleo_caja_no_desplazado_por_atencion():
    # ej4: caja + atención telefónica complementaria → CAJERO (5230.1)
    tc = _tc(equiv=True)
    r = tc.evaluar('Cajero', _cont('cobrar productos y servicios; registrar pagos; manejar valores; '
                                   'realizar arqueos; cerrar caja; responder consultas telefónicas'))
    assert r.get('codigo_esco') == '5230.1', r


def test_laudo2_d10_no_dispara_por_atencion_telefonica():
    # ej1: atención telefónica sin televenta → NO teleoperador 5244
    tc = _tc(equiv=True)
    r = tc.evaluar('Operador telefónico',
                   _cont('atender consultas telefónicas; informar sobre productos; orientar a clientes'))
    assert r.get('codigo_esco') != '5244.1', r


def test_laudo2_d10_si_dispara_televenta_explicita():
    # ej2: televenta explícita → teleoperador 5244
    tc = _tc(equiv=True)
    # con un término de televenta que el léxico D10 reconoce (televentas/ventas telefónicas)
    r = tc.evaluar('Vendedor telefónico',
                   _cont('realizar televentas; promocionar productos y cerrar ventas telefonicas; telemarketing'))
    assert r.get('codigo_esco') == '5244.1', r


def test_laudo3_sinonimos_comerciales_aceptados_y_rechazados():
    # prospección: captar nuevos clientes SÍ; identificar oportunidades NO (parcial)
    assert _sinonimo_comercial_en_texto('prospeccion', 'captar nuevos clientes en la zona')
    assert not _sinonimo_comercial_en_texto('prospeccion', 'identificar oportunidades de mejora')
    # establecer objetivos: NO equivale a cumplir objetivos
    assert not _sinonimo_comercial_en_texto('establecer objetivos', 'cumplir objetivos de venta')
    # cotizaciones: presupuestos SÍ; facturación NO
    assert _sinonimo_comercial_en_texto('cotizaciones', 'elaborar presupuestos y propuestas de precios')
    assert not _sinonimo_comercial_en_texto('cotizaciones', 'realizar la facturacion mensual')


def test_produccion_intacta_equiv_off():
    # con el mini-frente OFF (producción), las complementarias NO se excluyen (comportamiento previo)
    tc = _tc(equiv=False)
    assert tc._equiv is False
    # sin equiv, el sinónimo comercial no se evalúa en el matcher (gate en _matches_de)
