#!/usr/bin/env python3
"""
Export incremental de ofertas nuevas desde el VPS.
Genera un dump SQL con INSERT OR IGNORE para importar en BD local.

Uso:
    python3 scripts/export_nuevas.py              # Exporta desde último sync
    python3 scripts/export_nuevas.py --full       # Exporta todo
    python3 scripts/export_nuevas.py --since 2026-03-10  # Desde fecha específica
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'database' / 'bumeran_scraping.db'
EXPORT_DIR = BASE_DIR / 'data' / 'export'
SYNC_LOG = BASE_DIR / 'data' / 'sync_log.json'

# Columnas de la tabla ofertas que exportamos
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


def get_last_sync():
    """Lee timestamp del último sync exitoso"""
    if SYNC_LOG.exists():
        data = json.loads(SYNC_LOG.read_text())
        return data.get('last_export', None)
    return None


def save_sync_timestamp(timestamp, count):
    """Guarda timestamp del export actual"""
    SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if SYNC_LOG.exists():
        data = json.loads(SYNC_LOG.read_text())
    
    data['last_export'] = timestamp
    data['last_export_count'] = count
    data['history'] = data.get('history', [])
    data['history'].append({
        'timestamp': timestamp,
        'count': count,
        'exported_at': datetime.now().isoformat()
    })
    # Mantener solo últimos 50 registros
    data['history'] = data['history'][-50:]
    
    SYNC_LOG.write_text(json.dumps(data, indent=2))


def escape_sql(value):
    """Escapa un valor para SQL"""
    if value is None:
        return 'NULL'
    if isinstance(value, (int, float)):
        return str(value)
    # Escapar comillas simples
    return "'" + str(value).replace("'", "''") + "'"


def export_ofertas(since=None, full=False, portales=None, dry_run=False):
    """Exporta ofertas a archivo SQL"""
    
    if not DB_PATH.exists():
        print(f"ERROR: BD no encontrada en {DB_PATH}")
        sys.exit(1)
    
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Determinar desde cuándo exportar (condiciones combinables con AND)
    conditions = []
    params = []
    # Race condition fix (2026-05-15): incluir ofertas con descripción
    # actualizada después de last_sync, no solo scrapeado_en. Cubre el caso
    # del scraping en 2 fases (listado + detalle) donde descripcion se completa
    # después del scrapeado_en inicial. Requiere columna descripcion_actualizada_en
    # + trigger trg_ofertas_descripcion_updated en la tabla ofertas.
    if full:
        print('Modo: FULL (todas las ofertas)')
    elif since:
        conditions.append('(scrapeado_en > ? OR descripcion_actualizada_en > ?)')
        params += [since, since]
        print(f'Modo: Desde {since}')
    else:
        last_sync = get_last_sync()
        if last_sync:
            conditions.append('(scrapeado_en > ? OR descripcion_actualizada_en > ?)')
            params += [last_sync, last_sync]
            print(f'Modo: Incremental (desde último sync: {last_sync})')
        else:
            print('Modo: FULL (primer export, sin sync previo)')

    # Filtro por portal — backfill quirúrgico (2026-06-30). No avanza el watermark.
    portal_list = None
    if portales:
        portal_list = [p.strip() for p in portales.split(',') if p.strip()]
        placeholders = ','.join('?' * len(portal_list))
        conditions.append(f'portal IN ({placeholders})')
        params += portal_list
        print(f'Filtro portal: {portal_list} (backfill, no toca watermark)')

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    params = tuple(params)

    # Contar ofertas a exportar
    cur.execute(f'SELECT COUNT(*) FROM ofertas {where}', params)
    count = cur.fetchone()[0]
    
    if count == 0:
        print('No hay ofertas nuevas para exportar.')
        return None

    print(f'Ofertas a exportar: {count}')

    if dry_run:
        # Estimación de tamaño sin escribir nada
        cur.execute(f'SELECT SUM(LENGTH(COALESCE(descripcion,\"\"))) FROM ofertas {where}', params)
        desc_bytes = cur.fetchone()[0] or 0
        print(f'DRY-RUN: no se escribe archivo.')
        print(f'  Filas: {count}')
        print(f'  Peso descripciones: ~{desc_bytes/1024:.0f} KB (archivo final algo mayor)')
        if portal_list:
            for p in portal_list:
                cur.execute('SELECT COUNT(*) FROM ofertas WHERE portal=?', (p,))
                print(f'  {p}: {cur.fetchone()[0]} filas en VPS')
        conn.close()
        return None
    
    # Generar archivo SQL
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'ofertas_export_{timestamp}.sql'
    filepath = EXPORT_DIR / filename
    
    cols_str = ', '.join(COLUMNAS)
    
    cur.execute(f'SELECT {cols_str} FROM ofertas {where} ORDER BY scrapeado_en', params)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'-- MOL Export: {count} ofertas\n')
        f.write(f'-- Generado: {datetime.now().isoformat()}\n')
        f.write(f'-- Fuente: VPS {os.uname().nodename}\n')
        f.write(f'-- Modo: {"full" if full else "incremental"}\n')
        f.write('BEGIN TRANSACTION;\n')
        
        batch = []
        for row in cur:
            values = ', '.join(escape_sql(row[col]) for col in COLUMNAS)
            # Bug A fix (2026-05-12): UPSERT condicional para que descripciones del VPS
            # actualicen ofertas existentes en local. Sólo toca descripcion; otros campos
            # (estado_validacion, validacion_humana, banderas, etc.) quedan intactos.
            # Guard LENGTH(new) > LENGTH(old) evita sobrescribir desc buena con vacío.
            batch.append(
                f'INSERT INTO ofertas ({cols_str}) VALUES ({values}) '
                f'ON CONFLICT(id_oferta) DO UPDATE SET descripcion = excluded.descripcion '
                f"WHERE LENGTH(excluded.descripcion) > LENGTH(COALESCE(ofertas.descripcion, ''));"
            )
            
            # Escribir en batches de 100
            if len(batch) >= 100:
                f.write('\n'.join(batch) + '\n')
                batch = []
        
        # Escribir resto
        if batch:
            f.write('\n'.join(batch) + '\n')
        
        f.write('COMMIT;\n')

    # Watermark = MAX timestamp REALMENTE exportado, no datetime.now() (2026-06-30).
    # Usar now() adelantaba el cursor más allá de filas recién scrapeadas (race) y,
    # combinado con el self-export del cron, perdía portales. Tomamos el mayor entre
    # scrapeado_en y descripcion_actualizada_en sobre el set exportado (mismo WHERE),
    # así el próximo incremental nunca saltea una fila no entregada (a lo sumo re-exporta,
    # que es idempotente por el ON CONFLICT).
    cur.execute(
        f"SELECT MAX(MAX(COALESCE(scrapeado_en,''), "
        f"COALESCE(descripcion_actualizada_en,''))) FROM ofertas {where}",
        params,
    )
    new_watermark = cur.fetchone()[0] or datetime.now().isoformat()

    conn.close()

    # Guardar watermark SOLO en exports normales. Un backfill por --portal es un
    # parche puntual: no debe mover el cursor del sync incremental.
    if portal_list:
        print('(backfill: watermark NO modificado)')
    else:
        save_sync_timestamp(new_watermark, count)
    
    filesize = filepath.stat().st_size
    print(f'Exportado: {filepath}')
    print(f'Tamaño: {filesize / 1024:.1f} KB')
    
    return str(filepath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export incremental de ofertas')
    parser.add_argument('--full', action='store_true', help='Exportar todas las ofertas')
    parser.add_argument('--since', type=str, help='Exportar desde fecha (ISO)')
    parser.add_argument('--portal', type=str, help='Filtrar por portal(es), coma-separados (backfill quirúrgico, no toca watermark). Ej: --portal caba,portalempleo')
    parser.add_argument('--dry-run', action='store_true', help='Solo contar/estimar, no escribir archivo')
    args = parser.parse_args()

    result = export_ofertas(since=args.since, full=args.full,
                            portales=args.portal, dry_run=args.dry_run)
    if result:
        print(f'\nPara transferir a local:')
        print(f'  scp root@187.124.150.28:{result} .')
