# Tests de la extracción de descripción de ComputRabajo (fix FRENTE J, 2026-08-05).
# Cubre la cadena de selectores y la guarda anti-boilerplate:
#   - JSON-LD JobPosting (método 0, el estable)
#   - p.mbB (variante clásica) y div anidado (variante ~mayo/2026)
#   - selector-falla + meta boilerplate → None (JAMÁS guardar el SEO)
#   - aviso genuinamente corto → se guarda corto legítimo
#   - redirect a listado → None
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '01_sources' / 'computrabajo' / 'scrapers'))
from bs4 import BeautifulSoup
from computrabajo_scraper import ComputRabajoScraper

BOILER = "¿Buscas trabajo de Vendedor? Crea tu CV gratis y aplica a los empleos disponibles. Computrabajo publica nuevos empleos cada día."
DESC_REAL = ("Nos encontramos en la búsqueda de un vendedor para importante comercio. "
             "Tareas: atención al cliente, reposición de mercadería, manejo de caja, "
             "control de stock y armado de vidriera según lineamientos de la marca.")


def _soup(body: str, title: str = 'Trabajos de Vendedor - Buenos Aires') -> BeautifulSoup:
    return BeautifulSoup(f'<html><head><title>{title}</title>'
                         f'<meta name="description" content="{BOILER}"></head>'
                         f'<body>{body}</body></html>', 'html.parser')


def _scraper() -> ComputRabajoScraper:
    return ComputRabajoScraper(delay_between_requests=0)


def test_metodo0_jsonld_jobposting():
    body = ('<script type="application/ld+json">'
            '{"@context":"https://schema.org","@graph":[{"@type":"JobPosting",'
            f'"title":"Vendedor","description":"<p>{DESC_REAL}</p>"}}]}}'
            '</script><div class="box_detail"></div>')
    desc = _scraper()._extraer_descripcion(_soup(body), 'http://test/aviso')
    assert desc is not None and 'reposición de mercadería' in desc
    assert '<p>' not in desc  # HTML stripped


def test_metodo1_p_mbB_variante_clasica():
    body = f'<div class="box_detail"><p class="mbB">{DESC_REAL}</p></div>'
    desc = _scraper()._extraer_descripcion(_soup(body), 'http://test/aviso')
    assert desc == DESC_REAL


def test_metodo2_div_anidado_variante_mayo():
    # variante ~mayo/2026: sin p.mbB, descripción en div anidado (no hijo directo)
    body = (f'<div class="box_detail"><div class="wrap"><div class="mb40 pb40 bb1">'
            f'{DESC_REAL}</div></div></div>')
    desc = _scraper()._extraer_descripcion(_soup(body), 'http://test/aviso')
    assert desc == DESC_REAL


def test_guarda_boilerplate_devuelve_none():
    # selector falla (box_detail vacío) y la meta es el SEO → None, jamás el boilerplate
    body = '<div class="box_detail"><p class="fs13">ruido</p></div>'
    desc = _scraper()._extraer_descripcion(_soup(body), 'http://test/aviso')
    assert desc is None


def test_meta_no_boilerplate_si_es_legitima():
    # meta con contenido real (no matchea el patrón SEO) sí puede usarse
    soup = BeautifulSoup('<html><head><title>Trabajos de Vendedor</title>'
                         f'<meta name="description" content="{DESC_REAL}"></head>'
                         '<body><div class="box_detail"></div></body></html>', 'html.parser')
    desc = _scraper()._extraer_descripcion(soup, 'http://test/aviso')
    assert desc == DESC_REAL


def test_aviso_genuinamente_corto_se_guarda():
    corto = 'Se busca vendedor con experiencia para local en Palermo. Jornada completa.'
    body = f'<div class="box_detail"><p class="mbB">{corto}</p></div>'
    desc = _scraper()._extraer_descripcion(_soup(body), 'http://test/aviso')
    assert desc == corto  # corto legítimo NO se descarta


def test_redirect_a_listado_devuelve_none():
    body = f'<div class="box_detail"><p class="mbB">{DESC_REAL}</p></div>'
    soup = _soup(body, title='Empleos en Buenos Aires-GBA | Ofertas de trabajo')
    desc = _scraper()._extraer_descripcion(soup, 'http://test/aviso')
    assert desc is None
