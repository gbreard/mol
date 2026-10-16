# -*- coding: utf-8 -*-
"""[CASCADA mini-frente árbol] Tests de la capa de equivalencia funcional del traductor.
Nominalización↔verbo como frase contigua; sin sobre-disparo de genéricos cortos."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'database'))
from traductor_contexto import _term_equiv_en_texto as eq, _term_en_texto as ex, TraductorContexto  # noqa: E402


def test_nominalizacion_verbo_matchea():
    pares = [
        ('carga de facturas', 'cargar facturas y comprobantes'),
        ('cierre de caja', 'controlar y cerrar caja'),
        ('asesoramiento', 'asesorar sobre la carta'),
        ('conciliaciones', 'conciliar cuentas bancarias'),
        ('armado de balances', 'armar balances mensuales'),
        ('atencion al cliente', 'atender al cliente en el salon'),
        ('facturacion', 'facturar a los clientes'),
        ('arqueo', 'arquear la caja al cierre'),
    ]
    for cond, tarea in pares:
        assert eq(cond, tarea), f'equiv debería matchear {cond!r} ↔ {tarea!r}'
        assert not ex(cond, tarea), f'exacto NO debería (prueba que era regresión): {cond!r}'


def test_no_sobre_dispara_genericos_ni_dispersos():
    # mono-token genérico corto: no rescatar
    assert not eq('cobro', 'cobrar en caja')
    assert not eq('venta', 'vender productos')
    assert not eq('pago', 'pagar a proveedores')
    assert not eq('carga', 'cargar camiones')
    # dispersos (no contiguos) no matchean
    assert not eq('carga de facturas', 'cargar camiones y emitir facturas')
    # no relacionados
    assert not eq('liquidacion de sueldos', 'cargar facturas')
    assert not eq('programacion', 'atender clientes')


def test_capa_off_por_defecto():
    # producción intacta: la capa está OFF salvo que se pida explícitamente
    assert TraductorContexto()._equiv is False
    assert TraductorContexto(equivalencia_funcional=True)._equiv is True


def test_match_exacto_sigue_funcionando():
    # el fallback no rompe el match exacto preexistente
    assert ex('cierre de caja', 'tareas de cierre de caja diario')
    assert eq('cierre de caja', 'tareas de cierre de caja diario')  # exacto ⊆ equiv
