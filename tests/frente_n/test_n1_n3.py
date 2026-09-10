# -*- coding: utf-8 -*-
"""[FRENTE N] Tests deterministas de N1 (limpiar_chrome) y N3 (postfiltrar).
No usan LLM. Fixtures con texto real de portales."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'frente_n'))
from limpiar_chrome import limpiar_chrome           # noqa: E402
from postfiltro_tareas import postfiltrar           # noqa: E402

# ── Fixtures reales (recortados) ──
CT_CON_CHROME = (
    "Ocultaste esta oferta, pulsaRecuperar ofertapara verla de nuevo en los listados\n\n"
    "Buscamos encargados/as para nuestro local. Tareas: manejo de caja y personal.\n\n"
    "Requerimientos\n\nHace 2 días (actualizada)\n\nAcerca de la empresa\n\n"
    "Somos líderes en gastronomía con 50 años de trayectoria...\n\nEvaluación general\n4.3\n"
    "Ofertas similares\n\nOtra empresaVenta de productos, asesoramiento...\n")
PORTALEMPLEO_META = (
    "Recibir y atender clientes, tomar pedidos, servir alimentos y bebidas.\n\n"
    "Tareas principales: Recibir y atender clientes, servir mesas.\n---\n"
    "Estudios requeridos: Secundario\nModalidad: Presencial\nDías laborables: Lunes a Viernes\n")
BUMERAN_LIMPIO = ("Responsabilidades: Asistir a audiencias. Realizar seguimiento de la cartera. "
                  "Requisitos: título habilitante.")
INDEED_NAV = "Portal Empleo Ciudadano Registrate Armá tu CV Buscá empleo Iniciar sesión"


def test_ct_corta_chrome_conserva_cuerpo():
    out = limpiar_chrome(CT_CON_CHROME, 'computrabajo')
    assert 'manejo de caja y personal' in out          # cuerpo sobrevive
    assert 'Acerca de la empresa' not in out            # blurb removido
    assert 'Ofertas similares' not in out               # avisos ajenos removidos
    assert 'Evaluación general' not in out
    assert 'Ocultaste esta oferta' not in out
    assert len(out) < len(CT_CON_CHROME) * 0.6          # removió chrome sustancial


def test_portalempleo_corta_metadata_conserva_tareas():
    out = limpiar_chrome(PORTALEMPLEO_META, 'portalempleo')
    assert 'Tareas principales' in out
    assert 'Recibir y atender clientes' in out
    assert 'Estudios requeridos' not in out             # metadata removida
    assert 'Modalidad: Presencial' not in out


def test_portal_api_no_se_toca():
    # Bumeran/ZonaJobs/Indeed no tienen chrome → el cuerpo queda intacto
    out = limpiar_chrome(BUMERAN_LIMPIO, 'bumeran')
    assert 'Asistir a audiencias' in out
    assert 'Realizar seguimiento de la cartera' in out


def test_nav_menu_es_vacio():
    assert limpiar_chrome(INDEED_NAV, 'indeed') == ''


def test_idempotente():
    out1 = limpiar_chrome(CT_CON_CHROME, 'computrabajo')
    out2 = limpiar_chrome(out1, 'computrabajo')
    assert out1 == out2


def test_none_y_vacio():
    assert limpiar_chrome(None, 'computrabajo') == ''
    assert limpiar_chrome('', 'bumeran') == ''


# ── N3 post-filtro ──
def test_n3_filtra_requisito():
    ok, desc = postfiltrar(['gestionar la facturación', 'experiencia en ventas',
                            'conocimiento de SQL', 'manejo de AutoCAD'])
    assert 'gestionar la facturación' in ok
    assert 'experiencia en ventas' not in ok
    assert 'conocimiento de SQL' not in ok
    assert 'manejo de AutoCAD' not in ok
    assert len(desc) == 3


def test_n3_filtra_beneficio_y_disponibilidad():
    ok, _ = postfiltrar(['brindar atención al cliente', 'disponibilidad para trabajar fines de semana',
                         'obra social', 'horario rotativo'])
    assert ok == ['brindar atención al cliente']


def test_n3_filtra_huerfano_sin_verbo():
    ok, desc = postfiltrar(['asegurar la calidad del producto', 'seguridad y usabilidad'])
    assert 'asegurar la calidad del producto' in ok
    assert 'seguridad y usabilidad' not in ok           # fragmento sin verbo
    assert any(d['motivo'] == 'fragmento_huerfano_sin_verbo' for d in desc)


def test_n3_dedup():
    ok, _ = postfiltrar(['cargar mercadería', 'Cargar mercadería.'])
    assert len(ok) == 1


def test_n3_conserva_tareas_validas():
    tareas = ['reponer productos en góndolas', 'realizar la carga y descarga de mercadería',
              'colaborar con la liquidación de sueldos', 'brindar atención cordial a los clientes']
    ok, desc = postfiltrar(tareas)
    assert ok == tareas
    assert desc == []


# ── N1 guard título-only ──
def test_guard_titulo_only():
    from limpiar_chrome import parece_solo_titulo
    assert parece_solo_titulo('AYUDANTE DE FARMACIA') is True
    assert parece_solo_titulo('administrador/a de redes informáticas') is True
    assert parece_solo_titulo('Ayudante área de logística y despacho') is True
    # con verbo o nominalización → NO es solo título
    assert parece_solo_titulo('Reponer los productos en góndolas') is False
    assert parece_solo_titulo('Instalación y mantenimiento de instalaciones eléctricas') is False
    assert parece_solo_titulo('Liquidación de sueldos y confección de recibos') is False
    # texto largo → NO título aunque sin verbo evidente
    assert parece_solo_titulo('x' * 130) is False
