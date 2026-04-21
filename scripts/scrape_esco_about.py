#!/usr/bin/env python3
"""
Scrapea todas las páginas de "About ESCO" y genera un PDF compilado en español.
Fuente: https://esco.ec.europa.eu/es/node/178
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from datetime import datetime

# ── URLs organizadas por sección ──────────────────────────────────────────────

SECTIONS = [
    {
        "section": "1. Introducción a ESCO",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/509", "¿Qué es ESCO y cómo usarlo?"),
            ("https://esco.ec.europa.eu/es/node/178", "Idiomas de ESCO"),
            ("https://esco.ec.europa.eu/es/node/240", "Visión de ESCO"),
            ("https://esco.ec.europa.eu/es/node/144", "Proceso de mejora continua"),
        ]
    },
    {
        "section": "2. Estructura y características de la clasificación ESCO",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/214", "Pilar de Ocupaciones"),
            ("https://esco.ec.europa.eu/es/node/111", "Pilar de Competencias"),
            ("https://esco.ec.europa.eu/es/node/230", "Contextualización de competencias"),
            ("https://esco.ec.europa.eu/es/node/235", "Directrices terminológicas"),
            ("https://esco.ec.europa.eu/es/node/237", "Conocimientos, competencias y aptitudes transversales"),
            ("https://esco.ec.europa.eu/es/node/222", "Cualificaciones y ESCO"),
            ("https://esco.ec.europa.eu/es/node/505", "Tablas de la Matriz Competencias-Ocupaciones"),
        ]
    },
    {
        "section": "3. Competencias digitales y verdes",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/492", "Competencias digitales"),
            ("https://esco.ec.europa.eu/es/node/491", "Competencias verdes"),
        ]
    },
    {
        "section": "4. Marcos y clasificaciones relacionados",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/192", "Marco Europeo de Competencia Digital (DigComp)"),
            ("https://esco.ec.europa.eu/es/node/202", "CINE-F 2013 (ISCED-F)"),
            ("https://esco.ec.europa.eu/es/node/203", "Clasificación Internacional de Ocupaciones (ISCO)"),
            ("https://esco.ec.europa.eu/es/node/544", "Relevancia de competencias en perfiles ocupacionales ESCO"),
        ]
    },
    {
        "section": "5. Desarrollo de ESCO",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/518", "Inteligencia artificial para el mantenimiento de ESCO"),
            ("https://esco.ec.europa.eu/es/node/179", "Gobernanza de ESCO"),
            ("https://esco.ec.europa.eu/es/node/304", "Grupo de Trabajo de Estados Miembros"),
            ("https://esco.ec.europa.eu/es/node/317", "Junta de ESCO"),
            ("https://esco.ec.europa.eu/es/node/245", "Comité de Mantenimiento de ESCO"),
            ("https://esco.ec.europa.eu/es/node/224", "Grupos de referencia"),
            ("https://esco.ec.europa.eu/es/node/188", "Versiones de ESCO"),
            ("https://esco.ec.europa.eu/es/node/181", "ESCO v0"),
            ("https://esco.ec.europa.eu/es/node/184", "ESCO v0.8"),
            ("https://esco.ec.europa.eu/es/node/185", "ESCO v0.9"),
            ("https://esco.ec.europa.eu/es/node/186", "ESCO v1"),
            ("https://esco.ec.europa.eu/es/node/187", "ESCO v1.1"),
            ("https://esco.ec.europa.eu/es/node/490", "ESCO v1.1.2"),
            ("https://esco.ec.europa.eu/es/node/503", "ESCO v1.2"),
            ("https://esco.ec.europa.eu/es/node/563", "ESCO v1.2.1"),
            ("https://esco.ec.europa.eu/es/node/210", "Lista de sectores para ESCO v1"),
        ]
    },
    {
        "section": "6. Glosario ESCO",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/120", "Valores separados por comas (CSV)"),
            ("https://esco.ec.europa.eu/es/node/121", "Competencia"),
            ("https://esco.ec.europa.eu/es/node/143", "Concepto"),
            ("https://esco.ec.europa.eu/es/node/147", "Definición"),
            ("https://esco.ec.europa.eu/es/node/148", "Descripción"),
            ("https://esco.ec.europa.eu/es/node/199", "Género"),
            ("https://esco.ec.europa.eu/es/node/200", "Término oculto"),
            ("https://esco.ec.europa.eu/es/node/564", "Interoperabilidad en ESCO"),
            ("https://esco.ec.europa.eu/es/node/206", "Conocimiento"),
            ("https://esco.ec.europa.eu/es/node/208", "Datos abiertos vinculados"),
            ("https://esco.ec.europa.eu/es/node/212", "Término no preferido"),
            ("https://esco.ec.europa.eu/es/node/213", "Ocupación"),
            ("https://esco.ec.europa.eu/es/node/215", "Hoja de cálculo OpenDocument (ODS)"),
            ("https://esco.ec.europa.eu/es/node/218", "Término preferido"),
            ("https://esco.ec.europa.eu/es/node/219", "Cualificación"),
            ("https://esco.ec.europa.eu/es/node/223", "RDF"),
            ("https://esco.ec.europa.eu/es/node/225", "Profesiones reguladas"),
            ("https://esco.ec.europa.eu/es/node/226", "Nota de alcance"),
            ("https://esco.ec.europa.eu/es/node/229", "SKOS"),
            ("https://esco.ec.europa.eu/es/node/231", "Nivel de reutilización de competencias"),
            ("https://esco.ec.europa.eu/es/node/543", "Modelo Europeo de Aprendizaje"),
            ("https://esco.ec.europa.eu/es/node/238", "Identificador Uniforme de Recursos (URI)"),
        ]
    },
    {
        "section": "7. Uso práctico de ESCO",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/353", "ESCO en búsqueda y matching de empleo"),
            ("https://esco.ec.europa.eu/es/node/124", "Matching de empleo basado en competencias"),
            ("https://esco.ec.europa.eu/es/node/204", "Búsqueda de empleo"),
            ("https://esco.ec.europa.eu/es/node/335", "EURES"),
            ("https://esco.ec.europa.eu/es/node/146", "Creación de CV"),
            ("https://esco.ec.europa.eu/es/node/191", "Europass"),
            ("https://esco.ec.europa.eu/es/node/36", "ESCO conecta mercado laboral con educación"),
            ("https://esco.ec.europa.eu/es/node/209", "Vinculación de resultados de aprendizaje con ESCO"),
            ("https://esco.ec.europa.eu/es/node/227", "Búsqueda de oportunidades de aprendizaje"),
            ("https://esco.ec.europa.eu/es/node/175", "ESCO para inteligencia del mercado laboral"),
            ("https://esco.ec.europa.eu/es/node/177", "ESCO en estadísticas"),
        ]
    },
    {
        "section": "8. Implementación y extensión",
        "pages": [
            ("https://esco.ec.europa.eu/es/node/196", "Extensión de ESCO"),
            ("https://esco.ec.europa.eu/es/node/198", "Análisis de brechas"),
            ("https://esco.ec.europa.eu/es/node/519", "Crosswalk entre O*NET y ESCO"),
            ("https://esco.ec.europa.eu/es/node/194", "Marco Europeo de Cualificaciones (EQF)"),
            ("https://esco.ec.europa.eu/es/node/211", "Mapeo hacia ESCO"),
            ("https://esco.ec.europa.eu/es/node/232", "NACE"),
        ]
    },
]


def scrape_page(url, title, session):
    """Scrapea una página ESCO y extrae el contenido principal."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # El contenido principal está en layout__region--second (columna 75%)
        content_area = (
            soup.find('div', class_='layout__region--second') or
            soup.find('div', class_='field--name-body') or
            soup.find('article') or
            soup.find('div', class_='node__content') or
            soup.find('main')
        )

        if not content_area:
            return {"title": title, "url": url, "content": "(Sin contenido extraíble)", "status": "empty"}

        # Limpiar: quitar scripts, styles, nav
        for tag in content_area.find_all(['script', 'style', 'nav', 'footer']):
            tag.decompose()

        # Extraer texto preservando estructura
        lines = []
        for elem in content_area.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'th', 'blockquote', 'figcaption']):
            text = elem.get_text(strip=True)
            if not text:
                continue
            tag = elem.name
            if tag in ('h1', 'h2'):
                lines.append(f"\n{'='*60}\n{text}\n{'='*60}")
            elif tag == 'h3':
                lines.append(f"\n--- {text} ---")
            elif tag == 'h4':
                lines.append(f"\n  {text}")
            elif tag == 'li':
                lines.append(f"  • {text}")
            elif tag in ('td', 'th'):
                lines.append(f"  | {text}")
            else:
                lines.append(text)

        content = '\n'.join(lines).strip()

        # Dedup: quitar líneas repetidas consecutivas
        deduped = []
        for line in content.split('\n'):
            if not deduped or line != deduped[-1]:
                deduped.append(line)
        content = '\n'.join(deduped)

        return {"title": title, "url": url, "content": content, "status": "ok"}

    except Exception as e:
        return {"title": title, "url": url, "content": f"(Error: {e})", "status": "error"}


def main():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) OEDE-Research-Bot/1.0',
        'Accept-Language': 'es-ES,es;q=0.9',
    })

    all_pages = []
    total_urls = sum(len(s['pages']) for s in SECTIONS)
    count = 0

    for section in SECTIONS:
        print(f"\n{'='*60}")
        print(f"  {section['section']}")
        print(f"{'='*60}")

        for url, title in section['pages']:
            count += 1
            print(f"  [{count}/{total_urls}] {title}...", end=' ', flush=True)
            result = scrape_page(url, title, session)
            result['section'] = section['section']
            all_pages.append(result)
            chars = len(result['content'])
            print(f"{'OK' if result['status'] == 'ok' else 'FAIL'} ({chars:,} chars)")
            time.sleep(1.5)  # Rate limiting

    # Guardar JSON intermedio
    os.makedirs('exports', exist_ok=True)
    json_path = 'exports/esco_about_scraped.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'total_pages': len(all_pages),
            'sections': [s['section'] for s in SECTIONS],
            'pages': all_pages
        }, f, ensure_ascii=False, indent=2)
    print(f"\nJSON guardado: {json_path}")

    # Estadísticas
    ok = sum(1 for p in all_pages if p['status'] == 'ok')
    total_chars = sum(len(p['content']) for p in all_pages)
    print(f"Páginas OK: {ok}/{len(all_pages)}")
    print(f"Caracteres totales: {total_chars:,}")

    return all_pages


if __name__ == '__main__':
    pages = main()
