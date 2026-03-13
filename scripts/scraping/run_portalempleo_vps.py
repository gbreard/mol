#!/usr/bin/env python3
"""
Portal Empleo Nacional - Scraping para VPS
==========================================

Scrapea portalempleo.gob.ar y guarda en la misma BD SQLite.
Portal del Ministerio de Trabajo con ofertas de todo el pais (~400-500).

Campos mapeados a la tabla ofertas:
  - id_oferta: 7_000_000_000 + CRC32(uuid)
  - titulo, empresa, descripcion (resumen + tareas + metadata)
  - localizacion (provincia - localidad - direccion)
  - modalidad_trabajo (disponibilidad), tipo_trabajo
  - cantidad_vacantes, fecha_publicacion_iso
  - portal = 'portalempleo'

Uso:
    python3 scripts/scraping/run_portalempleo_vps.py
    python3 scripts/scraping/run_portalempleo_vps.py --max-pages 5
    python3 scripts/scraping/run_portalempleo_vps.py --dry-run
    python3 scripts/scraping/run_portalempleo_vps.py --no-details  # solo listado
"""

import sqlite3
import json
import sys
import re
import logging
import argparse
import zlib
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "portalempleo" / "scrapers"))
sys.path.insert(0, str(BASE_DIR))

from portalempleo_scraper import PortalEmpleoScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prefix para IDs de Portal Empleo
# Bumeran: ~1,100,000,000
# ZonaJobs: ~2,100,000
# ComputRabajo: 5,000,000,000+ (CRC32)
# CABA: 6,000,000,000+ (nativo)
# Portal Empleo: 7,000,000,000+ (CRC32 de UUID)
PE_ID_PREFIX = 7_000_000_000


def uuid_to_int(uuid_str: str) -> int:
    """Convierte UUID a entero estable usando CRC32."""
    crc = zlib.crc32(uuid_str.encode('utf-8')) & 0xFFFFFFFF
    return PE_ID_PREFIX + crc


def _build_descripcion(oferta: dict) -> str:
    """
    Construye descripcion extendida incluyendo campos estructurados.
    """
    parts = []

    # Resumen
    resumen = oferta.get('resumen')
    if resumen:
        parts.append(resumen)

    # Tareas (si difiere del resumen)
    tareas = oferta.get('tareas')
    if tareas and tareas != resumen:
        parts.append(f"\nTareas principales: {tareas}")

    # Beneficios
    beneficios = oferta.get('beneficios')
    if beneficios:
        parts.append(f"\nBeneficios: {beneficios}")

    # Metadata estructurada
    metadata = []

    salario = oferta.get('salario')
    if salario and salario.lower() != 'a convenir':
        metadata.append(f"Salario: {salario}")

    estudios = oferta.get('estudios')
    if estudios:
        metadata.append(f"Estudios requeridos: {estudios}")

    experiencia = oferta.get('experiencia')
    if experiencia:
        metadata.append(f"Experiencia requerida: {experiencia}")

    dias = oferta.get('dias_laborables')
    if dias:
        metadata.append(f"Dias laborables: {dias}")

    h_entrada = oferta.get('horario_entrada')
    h_salida = oferta.get('horario_salida')
    if h_entrada and h_salida:
        metadata.append(f"Horario: {h_entrada} a {h_salida}")

    if metadata:
        parts.append("\n---\n" + "\n".join(metadata))

    return "\n".join(parts) if parts else None


def _map_disponibilidad(disp: str) -> str:
    """Mapea disponibilidad a tipo_trabajo."""
    if not disp:
        return None
    disp_lower = disp.lower()
    if 'tiempo completo' in disp_lower:
        return 'full-time'
    elif 'tiempo parcial' in disp_lower:
        return 'part-time'
    elif 'freelance' in disp_lower:
        return 'freelance'
    return disp


def mapear_oferta_para_bd(oferta: dict) -> dict:
    """
    Mapea campos de Portal Empleo al schema de la tabla ofertas.
    """
    id_int = uuid_to_int(oferta['uuid'])

    # Ubicacion: preferir lugar_trabajo (mas detallado)
    ubicacion = oferta.get('lugar_trabajo') or oferta.get('ubicacion')
    # Limpiar separadores
    if ubicacion:
        ubicacion = ubicacion.replace(' - ', ', ')

    return {
        'id_oferta': id_int,
        'id_empresa': None,
        'titulo': oferta.get('titulo'),
        'empresa': oferta.get('empresa'),
        'descripcion': _build_descripcion(oferta),
        'confidencial': None,
        'localizacion': ubicacion,
        'modalidad_trabajo': oferta.get('disponibilidad'),
        'tipo_trabajo': _map_disponibilidad(oferta.get('disponibilidad')),
        'fecha_publicacion_original': oferta.get('fecha_publicacion_raw'),
        'fecha_hora_publicacion_original': None,
        'fecha_modificado_original': None,
        'fecha_publicacion_iso': oferta.get('fecha_publicacion'),
        'fecha_hora_publicacion_iso': None,
        'fecha_modificado_iso': None,
        'fecha_publicacion_datetime': None,
        'fecha_hora_publicacion_datetime': None,
        'fecha_modificado_datetime': None,
        'cantidad_vacantes': oferta.get('vacantes'),
        'apto_discapacitado': None,
        'id_area': None,
        'id_subarea': None,
        'id_pais': None,
        'logo_url': None,
        'empresa_validada': None,
        'empresa_pro': None,
        'promedio_empresa': None,
        'plan_publicacion_id': None,
        'plan_publicacion_nombre': None,
        'portal': 'portalempleo',
        'tipo_aviso': None,
        'tiene_preguntas': None,
        'salario_obligatorio': None,
        'alta_revision_perfiles': None,
        'guardado': None,
        'gptw_url': None,
        'url_oferta': oferta.get('url'),
        'scrapeado_en': oferta.get('scrapeado_en', datetime.now().isoformat()),
    }


COLUMNAS = [
    'id_oferta', 'id_empresa', 'titulo', 'empresa', 'descripcion',
    'confidencial', 'localizacion', 'modalidad_trabajo', 'tipo_trabajo',
    'fecha_publicacion_original', 'fecha_hora_publicacion_original',
    'fecha_modificado_original', 'fecha_publicacion_iso',
    'fecha_hora_publicacion_iso', 'fecha_modificado_iso',
    'fecha_publicacion_datetime', 'fecha_hora_publicacion_datetime',
    'fecha_modificado_datetime', 'cantidad_vacantes', 'apto_discapacitado',
    'id_area', 'id_subarea', 'id_pais', 'logo_url', 'empresa_validada',
    'empresa_pro', 'promedio_empresa', 'plan_publicacion_id',
    'plan_publicacion_nombre', 'portal', 'tipo_aviso', 'tiene_preguntas',
    'salario_obligatorio', 'alta_revision_perfiles', 'guardado', 'gptw_url',
    'url_oferta', 'scrapeado_en'
]


def insertar_en_bd(ofertas_mapeadas: list, db_path: str) -> dict:
    """Inserta ofertas en BD SQLite (INSERT OR IGNORE)."""
    conn = sqlite3.connect(db_path, timeout=30)
    cur = conn.cursor()

    cols_str = ', '.join(COLUMNAS)
    placeholders = ', '.join(['?'] * len(COLUMNAS))
    sql = f"INSERT OR IGNORE INTO ofertas ({cols_str}) VALUES ({placeholders})"

    insertadas = 0
    duplicadas = 0
    errores = 0

    for oferta in ofertas_mapeadas:
        if oferta is None:
            errores += 1
            continue
        try:
            valores = tuple(oferta.get(col) for col in COLUMNAS)
            cur.execute(sql, valores)
            if cur.rowcount > 0:
                insertadas += 1
            else:
                duplicadas += 1
        except Exception as e:
            errores += 1
            if errores <= 5:
                logger.warning(f"Error insertando oferta {oferta.get('id_oferta')}: {e}")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM ofertas")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ofertas WHERE portal = 'portalempleo'")
    total_pe = cur.fetchone()[0]

    conn.close()

    return {
        'insertadas': insertadas,
        'duplicadas': duplicadas,
        'errores': errores,
        'total_bd': total,
        'total_portalempleo': total_pe
    }


def main():
    parser = argparse.ArgumentParser(description='Portal Empleo Nacional Scraper')
    parser.add_argument('--db', type=str, default=None,
                        help='Ruta a la BD SQLite')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Limite de paginas del listado (default: todas)')
    parser.add_argument('--no-details', action='store_true',
                        help='Solo listado, sin fetch de detalle')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='Delay entre requests (default: 1.5)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo scrapear, no insertar en BD')
    args = parser.parse_args()

    db_path = args.db or str(BASE_DIR / "database" / "bumeran_scraping.db")

    logger.info("=" * 60)
    logger.info("Portal Empleo Nacional - Scraping")
    logger.info("=" * 60)
    logger.info(f"BD: {db_path}")
    logger.info(f"Delay: {args.delay}s")
    logger.info(f"Max pages: {args.max_pages or 'todas'}")
    logger.info(f"Fetch details: {not args.no_details}")

    scraper = PortalEmpleoScraper(delay=args.delay)
    ofertas = scraper.scrape_all(
        fetch_details=not args.no_details,
        max_pages=args.max_pages
    )

    if not ofertas:
        logger.warning("No se obtuvieron ofertas")
        return

    logger.info(f"\nOfertas scrapeadas: {len(ofertas)}")

    ofertas_mapeadas = []
    for o in ofertas:
        mapeada = mapear_oferta_para_bd(o)
        if mapeada:
            ofertas_mapeadas.append(mapeada)

    logger.info(f"Ofertas mapeadas: {len(ofertas_mapeadas)}")

    if args.dry_run:
        logger.info("DRY RUN - no se inserta en BD")
        out_path = BASE_DIR / "portalempleo_ofertas_dry_run.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Ofertas guardadas en {out_path}")
        return

    stats = insertar_en_bd(ofertas_mapeadas, db_path)

    logger.info("\n" + "=" * 60)
    logger.info("RESULTADO PORTAL EMPLEO SCRAPING")
    logger.info("=" * 60)
    logger.info(f"  Nuevas insertadas: {stats['insertadas']}")
    logger.info(f"  Duplicadas: {stats['duplicadas']}")
    logger.info(f"  Errores: {stats['errores']}")
    logger.info(f"  Total Portal Empleo en BD: {stats['total_portalempleo']}")
    logger.info(f"  Total ofertas en BD: {stats['total_bd']}")


if __name__ == '__main__':
    main()
