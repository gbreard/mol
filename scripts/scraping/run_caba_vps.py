#!/usr/bin/env python3
"""
CABA Portal de Trabajo - Scraping para VPS
===========================================

Scrapea trabajo.buenosaires.gob.ar y guarda en la misma BD SQLite.
Disenado para correr en el VPS junto con los scrapers de Bumeran, ZonaJobs y ComputRabajo.

Campos de CABA mapeados a la tabla ofertas:
  - id_oferta: 6_000_000_000 + id_anuncio nativo
  - titulo, empresa, descripcion, ubicacion -> localizacion
  - modalidad_trabajo, cantidad_vacantes, tipo_trabajo (disponibilidad)
  - fecha_publicacion -> fecha_publicacion_iso
  - url_oferta
  - portal = 'caba'

Campos extra en descripcion (no hay columnas dedicadas):
  - industria, sector, estudios, idiomas, conocimientos IT
  -> Se agregan al final de descripcion como metadata estructurada

Uso:
    python3 scripts/scraping/run_caba_vps.py
    python3 scripts/scraping/run_caba_vps.py --db /ruta/bd.db
    python3 scripts/scraping/run_caba_vps.py --no-details   # solo listado, rapido
"""

import sqlite3
import json
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "01_sources" / "caba" / "scrapers"))
sys.path.insert(0, str(BASE_DIR))

from database.colisiones_id import (
    asegurar_tabla as _asegurar_colisiones,
    registrar_si_cross_portal as _registrar_colision,
)

from caba_scraper import CABAScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Nodo donde corre este runner (para la tabla colisiones_id)
NODO_COLISIONES = 'vps'

# Prefix para IDs de CABA (evitar colisiones con otros portales)
# Bumeran: ~1,100,000,000 range
# ZonaJobs: ~2,100,000 range
# ComputRabajo: 5,000,000,000+ range
# CABA: 6,000,000,000+ range
CABA_ID_PREFIX = 6_000_000_000


def caba_id_to_int(anuncio_id: int) -> int:
    """Convierte ID nativo de CABA a ID unico para la BD."""
    return CABA_ID_PREFIX + anuncio_id


def _build_descripcion_extendida(oferta: dict) -> str:
    """
    Construye descripcion extendida incluyendo campos estructurados
    que no tienen columna dedicada en la tabla ofertas.

    Los campos extra (industria, sector, estudios, idiomas, IT)
    son muy valiosos para NLP y se agregan como bloque al final.
    """
    parts = []

    # Descripcion principal
    desc = oferta.get('descripcion')
    if desc:
        parts.append(desc)

    # Beneficios
    beneficios = oferta.get('beneficios')
    if beneficios:
        parts.append(f"\nBeneficios: {beneficios}")

    # Metadata estructurada (muy util para NLP)
    metadata = []

    industria = oferta.get('industria')
    if industria:
        metadata.append(f"Industria: {industria}")

    sector = oferta.get('sector')
    if sector:
        metadata.append(f"Sector/Area: {sector}")

    estudios = oferta.get('estudios')
    if estudios:
        metadata.append(f"Estudios requeridos: {estudios}")

    exp = oferta.get('experiencia_excluyente')
    if exp:
        metadata.append(f"Experiencia excluyente: {exp}")

    idiomas = oferta.get('idiomas')
    if idiomas:
        metadata.append(f"Idiomas: {', '.join(idiomas)}")

    # Conocimientos IT
    it_parts = []
    for campo, label in [
        ('paquete_office', 'Office'),
        ('sistemas_contables', 'Sistemas contables'),
        ('programacion', 'Programacion'),
        ('base_datos', 'Base de datos'),
    ]:
        val = oferta.get(campo)
        if val and val.strip().lower() not in ('no', 'no:'):
            # Limpiar whitespace excesivo del HTML
            import re as _re
            val_clean = _re.sub(r'\s+', ' ', val).strip()
            it_parts.append(f"{label}: {val_clean}")
    if it_parts:
        metadata.append(f"Conocimientos IT: {'; '.join(it_parts)}")

    dias = oferta.get('dias_laborables')
    if dias:
        metadata.append(f"Dias laborables: {dias}")

    horario = oferta.get('horario')
    if horario:
        metadata.append(f"Horario: {horario}")

    residencia = oferta.get('residencia')
    if residencia:
        metadata.append(f"Residencia requerida: {residencia}")

    if metadata:
        parts.append("\n---\n" + "\n".join(metadata))

    return "\n".join(parts) if parts else None


def mapear_oferta_para_bd(oferta: dict) -> dict:
    """
    Mapea los campos de CABA al schema de la tabla ofertas.

    CABA tiene campos MUY ricos (industria, sector, vacantes, educacion, etc.)
    que otros portales no tienen. Los que no mapean a columnas existentes
    se integran en la descripcion extendida.
    """
    id_int = caba_id_to_int(oferta['id'])

    # Mapear disponibilidad a tipo_trabajo
    disp = oferta.get('disponibilidad')
    tipo_trabajo_map = {
        'Full-Time': 'full-time',
        'Part-Time': 'part-time',
        'Fines de Semana': 'part-time',
        'Free-Lance': 'freelance',
    }
    tipo_trabajo = tipo_trabajo_map.get(disp, disp)

    # Ubicacion: usar lugar_detalle (direccion completa) si existe, sino lugar_trabajo
    ubicacion = oferta.get('lugar_detalle') or oferta.get('lugar_trabajo')

    return {
        # IDs
        'id_oferta': id_int,
        'id_empresa': oferta.get('id_empresa'),

        # Info basica
        'titulo': oferta.get('titulo'),
        'empresa': oferta.get('empresa'),
        'descripcion': _build_descripcion_extendida(oferta),
        'confidencial': None,

        # Ubicacion y modalidad
        'localizacion': ubicacion,
        'modalidad_trabajo': oferta.get('modalidad'),
        'tipo_trabajo': tipo_trabajo,

        # Fechas
        'fecha_publicacion_original': oferta.get('fecha_publicacion_raw'),
        'fecha_hora_publicacion_original': None,
        'fecha_modificado_original': None,
        'fecha_publicacion_iso': oferta.get('fecha_publicacion'),
        'fecha_hora_publicacion_iso': None,
        'fecha_modificado_iso': None,
        'fecha_publicacion_datetime': None,
        'fecha_hora_publicacion_datetime': None,
        'fecha_modificado_datetime': None,

        # Detalles
        'cantidad_vacantes': oferta.get('vacantes'),
        'apto_discapacitado': None,

        # Categorizacion
        'id_area': None,
        'id_subarea': None,
        'id_pais': None,

        # Empresa
        'logo_url': None,
        'empresa_validada': None,
        'empresa_pro': None,
        'promedio_empresa': None,

        # Plan de publicacion
        'plan_publicacion_id': None,
        'plan_publicacion_nombre': None,

        # Otros
        'portal': 'caba',
        'tipo_aviso': None,
        'tiene_preguntas': None,
        'salario_obligatorio': None,
        'alta_revision_perfiles': None,
        'guardado': None,
        'gptw_url': None,

        # Metadata
        'url_oferta': oferta.get('url'),
        'scrapeado_en': oferta.get('scrapeado_en', datetime.now().isoformat()),
    }


# Columnas para INSERT (debe coincidir con schema de la tabla ofertas)
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
    """
    Inserta ofertas mapeadas en la BD SQLite (INSERT OR IGNORE).

    Returns:
        Dict con estadisticas: insertadas, duplicadas, errores
    """
    conn = sqlite3.connect(db_path, timeout=30)
    cur = conn.cursor()
    _asegurar_colisiones(cur)

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
                # rowcount 0: duplicado legitimo del mismo portal, o COLISION de id
                # entre portales (espacio de ids mal dimensionado). El SELECT del
                # portal existente ocurre solo aca, no en el camino de insercion.
                _registrar_colision(cur, valores[0], 'caba', oferta, nodo=NODO_COLISIONES)
                duplicadas += 1
        except Exception as e:
            errores += 1
            if errores <= 5:
                logger.warning(f"Error insertando oferta {oferta.get('id_oferta')}: {e}")

    conn.commit()

    # Estadisticas
    cur.execute("SELECT COUNT(*) FROM ofertas")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ofertas WHERE portal = 'caba'")
    total_caba = cur.fetchone()[0]

    conn.close()

    return {
        'insertadas': insertadas,
        'duplicadas': duplicadas,
        'errores': errores,
        'total_bd': total,
        'total_caba': total_caba
    }


def main():
    parser = argparse.ArgumentParser(description='CABA Portal de Trabajo Scraper')
    parser.add_argument('--db', type=str, default=None,
                        help='Ruta a la BD SQLite (default: database/bumeran_scraping.db)')
    parser.add_argument('--no-details', action='store_true',
                        help='Solo listado, sin fetch de detalle (rapido)')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='Delay entre requests en segundos (default: 1.5)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo scrapear, no insertar en BD')
    args = parser.parse_args()

    # DB path
    if args.db:
        db_path = args.db
    else:
        db_path = str(BASE_DIR / "database" / "bumeran_scraping.db")

    logger.info("=" * 60)
    logger.info("CABA Portal de Trabajo - Scraping")
    logger.info("=" * 60)
    logger.info(f"BD: {db_path}")
    logger.info(f"Delay: {args.delay}s")
    logger.info(f"Fetch details: {not args.no_details}")

    # Scrapear
    scraper = CABAScraper(delay=args.delay)
    ofertas = scraper.scrape_all(fetch_details=not args.no_details)

    if not ofertas:
        logger.warning("No se obtuvieron ofertas")
        return

    logger.info(f"\nOfertas scrapeadas: {len(ofertas)}")

    # Mapear
    ofertas_mapeadas = []
    for o in ofertas:
        mapeada = mapear_oferta_para_bd(o)
        if mapeada:
            ofertas_mapeadas.append(mapeada)
            logger.info(f"  [{o['id']} -> {mapeada['id_oferta']}] {o['titulo']}")

    logger.info(f"Ofertas mapeadas: {len(ofertas_mapeadas)}")

    if args.dry_run:
        logger.info("DRY RUN - no se inserta en BD")
        # Guardar JSON para inspeccion
        out_path = BASE_DIR / "caba_ofertas_dry_run.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Ofertas guardadas en {out_path}")
        return

    # Insertar en BD
    stats = insertar_en_bd(ofertas_mapeadas, db_path)

    logger.info("\n" + "=" * 60)
    logger.info("RESULTADO CABA SCRAPING")
    logger.info("=" * 60)
    logger.info(f"  Nuevas insertadas: {stats['insertadas']}")
    logger.info(f"  Duplicadas (ya existian): {stats['duplicadas']}")
    logger.info(f"  Errores: {stats['errores']}")
    logger.info(f"  Total CABA en BD: {stats['total_caba']}")
    logger.info(f"  Total ofertas en BD: {stats['total_bd']}")


if __name__ == '__main__':
    main()
