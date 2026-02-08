#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detectar_republicaciones.py
============================
Detecta ofertas republicadas (mismo titulo+empresa, distinto id_oferta).

Indicador de DEMANDA INSATISFECHA: la empresa no encontró candidato
y volvió a publicar el aviso.

Lógica:
1. Normaliza títulos (lowercase, strip, sin puntuación extra)
2. Agrupa por (titulo_normalizado, id_empresa) — excluye confidenciales
3. Grupos con count > 1 → republicaciones
4. Ordena por fecha_publicacion_iso ASC dentro de cada grupo
5. Primera = original, resto = republicaciones (numero_republicacion)
6. Actualiza columnas en tabla ofertas + ofertas_nlp.es_republica

Uso:
    python database/detectar_republicaciones.py
    python database/detectar_republicaciones.py --dry-run
    python database/detectar_republicaciones.py --stats
"""

import sqlite3
import hashlib
import logging
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'


def normalizar_titulo(titulo: str) -> str:
    """
    Normaliza un título para comparación de republicaciones.

    - Lowercase
    - Strip whitespace
    - Remueve puntuación redundante
    - Colapsa espacios múltiples
    """
    if not titulo:
        return ''
    t = titulo.lower().strip()
    # Remover puntuación al final (., !, -, etc.)
    t = re.sub(r'[.\-!?:;,]+$', '', t)
    # Colapsar espacios múltiples
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def generar_grupo_hash(titulo_norm: str, id_empresa: int) -> str:
    """Genera hash determinístico para un grupo de republicaciones."""
    key = f"{titulo_norm}|{id_empresa}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:12]


class DetectorRepublicaciones:
    """Detecta y marca ofertas republicadas en la BD."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def verificar_migracion(self) -> bool:
        """Verifica que la migración 023 fue aplicada."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(ofertas)")
        columnas = {row[1] for row in cursor.fetchall()}
        return 'grupo_republicacion' in columnas

    def aplicar_migracion(self):
        """Aplica migración 023 si no está aplicada."""
        migration_path = Path(__file__).parent / 'migrations' / '023_republicacion_tracking.sql'
        if not migration_path.exists():
            logger.error(f"Migración no encontrada: {migration_path}")
            return False

        logger.info("Aplicando migración 023_republicacion_tracking...")
        cursor = self.conn.cursor()

        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Ejecutar cada statement por separado (SQLite no soporta multi-statement)
        for statement in sql.split(';'):
            # Remover líneas de comentario antes de evaluar si está vacío
            lines = [l for l in statement.strip().splitlines()
                     if l.strip() and not l.strip().startswith('--')]
            clean = '\n'.join(lines).strip()
            if not clean:
                continue
            try:
                cursor.execute(statement)
            except sqlite3.OperationalError as e:
                # "duplicate column name" es OK (ya existe)
                if 'duplicate column' in str(e).lower():
                    continue
                # "table already exists" es OK
                if 'already exists' in str(e).lower():
                    continue
                raise

        self.conn.commit()
        logger.info("Migración 023 aplicada correctamente")
        return True

    def detectar_grupos(self) -> List[Dict]:
        """
        Detecta grupos de ofertas republicadas.

        Solo considera ofertas NO confidenciales (con id_empresa).

        Returns:
            Lista de grupos con sus ofertas ordenadas por fecha
        """
        cursor = self.conn.cursor()

        # Traer todas las ofertas con empresa conocida
        cursor.execute("""
            SELECT id_oferta, titulo, id_empresa, empresa,
                   fecha_publicacion_iso, estado_oferta, cantidad_vacantes
            FROM ofertas
            WHERE id_empresa IS NOT NULL
              AND titulo IS NOT NULL
              AND titulo != ''
            ORDER BY fecha_publicacion_iso ASC
        """)

        rows = cursor.fetchall()
        logger.info(f"Ofertas con empresa conocida: {len(rows):,}")

        # Agrupar por (titulo_normalizado, id_empresa)
        grupos = {}
        for row in rows:
            titulo_norm = normalizar_titulo(row['titulo'])
            if not titulo_norm:
                continue

            key = (titulo_norm, row['id_empresa'])
            if key not in grupos:
                grupos[key] = {
                    'titulo_norm': titulo_norm,
                    'id_empresa': row['id_empresa'],
                    'empresa': row['empresa'],
                    'ofertas': []
                }

            grupos[key]['ofertas'].append({
                'id_oferta': row['id_oferta'],
                'titulo': row['titulo'],
                'fecha': row['fecha_publicacion_iso'],
                'estado': row['estado_oferta'],
                'vacantes': row['cantidad_vacantes']
            })

        # Filtrar solo grupos con más de 1 oferta (republicaciones)
        grupos_repub = [
            g for g in grupos.values()
            if len(g['ofertas']) > 1
        ]

        # Ordenar ofertas dentro de cada grupo por fecha
        for grupo in grupos_repub:
            grupo['ofertas'].sort(key=lambda x: x['fecha'] or '')

        logger.info(f"Grupos con republicaciones: {len(grupos_repub):,}")
        total_ofertas_repub = sum(len(g['ofertas']) for g in grupos_repub)
        logger.info(f"Ofertas involucradas: {total_ofertas_repub:,}")

        return grupos_repub

    def marcar_republicaciones(
        self,
        grupos: List[Dict],
        dry_run: bool = False
    ) -> Dict:
        """
        Marca las ofertas republicadas en la BD.

        Args:
            grupos: Lista de grupos detectados
            dry_run: Si True, no modifica la BD

        Returns:
            Estadísticas de la operación
        """
        if not grupos:
            logger.info("No hay republicaciones para marcar")
            return {'grupos': 0, 'ofertas_marcadas': 0}

        cursor = self.conn.cursor()
        total_marcadas = 0
        total_originales = 0

        for grupo in grupos:
            titulo_norm = grupo['titulo_norm']
            id_empresa = grupo['id_empresa']
            grupo_hash = generar_grupo_hash(titulo_norm, id_empresa)

            for i, oferta in enumerate(grupo['ofertas']):
                es_repub = 0 if i == 0 else 1
                numero = i + 1
                id_original = grupo['ofertas'][0]['id_oferta']

                if not dry_run:
                    cursor.execute("""
                        UPDATE ofertas
                        SET grupo_republicacion = ?,
                            es_republicacion = ?,
                            numero_republicacion = ?,
                            id_oferta_original = ?
                        WHERE id_oferta = ?
                    """, (grupo_hash, es_repub, numero, id_original, oferta['id_oferta']))

                if es_repub:
                    total_marcadas += 1
                else:
                    total_originales += 1

        # Actualizar ofertas_nlp.es_republica si la tabla existe
        if not dry_run:
            try:
                cursor.execute("""
                    UPDATE ofertas_nlp
                    SET es_republica = 1
                    WHERE id_oferta IN (
                        SELECT CAST(id_oferta AS TEXT)
                        FROM ofertas
                        WHERE es_republicacion = 1
                    )
                """)
                nlp_actualizadas = cursor.rowcount
                logger.info(f"ofertas_nlp.es_republica actualizado: {nlp_actualizadas}")
            except sqlite3.OperationalError:
                pass  # Tabla no existe o columna faltante

        if not dry_run:
            # Limpiar ofertas que ya no son republicación
            # (por si se re-ejecuta y los datos cambiaron)
            cursor.execute("""
                UPDATE ofertas
                SET grupo_republicacion = NULL,
                    es_republicacion = 0,
                    numero_republicacion = NULL,
                    id_oferta_original = NULL
                WHERE grupo_republicacion IS NOT NULL
                  AND id_oferta NOT IN (
                      SELECT id_oferta FROM ofertas
                      WHERE grupo_republicacion IS NOT NULL
                        AND es_republicacion IS NOT NULL
                  )
            """)
            self.conn.commit()

        stats = {
            'grupos_detectados': len(grupos),
            'ofertas_originales': total_originales,
            'ofertas_republicadas': total_marcadas,
            'total_ofertas_involucradas': total_originales + total_marcadas,
            'dry_run': dry_run
        }

        return stats

    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de republicaciones desde la BD."""
        cursor = self.conn.cursor()

        stats = {}

        # Total republicaciones
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas WHERE es_republicacion = 1
        """)
        stats['total_republicaciones'] = cursor.fetchone()[0]

        # Total grupos
        cursor.execute("""
            SELECT COUNT(DISTINCT grupo_republicacion)
            FROM ofertas
            WHERE grupo_republicacion IS NOT NULL
        """)
        stats['total_grupos'] = cursor.fetchone()[0]

        # Distribución por veces republicada
        cursor.execute("""
            SELECT veces_pub, COUNT(*) as cantidad
            FROM (
                SELECT grupo_republicacion, COUNT(*) as veces_pub
                FROM ofertas
                WHERE grupo_republicacion IS NOT NULL
                GROUP BY grupo_republicacion
            )
            GROUP BY veces_pub
            ORDER BY veces_pub
        """)
        stats['distribucion'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Top 10 más republicadas
        cursor.execute("""
            SELECT
                MIN(titulo) as titulo,
                MIN(empresa) as empresa,
                COUNT(*) as veces,
                CAST(
                    julianday(MAX(fecha_publicacion_iso)) -
                    julianday(MIN(fecha_publicacion_iso))
                AS INTEGER) as dias_persistencia
            FROM ofertas
            WHERE grupo_republicacion IS NOT NULL
            GROUP BY grupo_republicacion
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        stats['top_10'] = [
            {
                'titulo': row[0],
                'empresa': row[1],
                'veces': row[2],
                'dias_persistencia': row[3]
            }
            for row in cursor.fetchall()
        ]

        # Promedio de republicaciones por empresa (top 10 empresas)
        cursor.execute("""
            SELECT
                empresa,
                COUNT(DISTINCT grupo_republicacion) as puestos_republicados,
                SUM(CASE WHEN es_republicacion = 1 THEN 1 ELSE 0 END) as total_repubs
            FROM ofertas
            WHERE grupo_republicacion IS NOT NULL
              AND empresa IS NOT NULL
            GROUP BY empresa
            HAVING COUNT(DISTINCT grupo_republicacion) > 1
            ORDER BY puestos_republicados DESC
            LIMIT 10
        """)
        stats['top_empresas'] = [
            {
                'empresa': row[0],
                'puestos_republicados': row[1],
                'total_repubs': row[2]
            }
            for row in cursor.fetchall()
        ]

        return stats

    def ejecutar(self, dry_run: bool = False) -> Dict:
        """
        Ejecuta detección completa de republicaciones.

        Args:
            dry_run: No modificar BD

        Returns:
            Estadísticas
        """
        logger.info("=" * 70)
        logger.info("DETECCIÓN DE REPUBLICACIONES")
        logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Modo: {'DRY-RUN' if dry_run else 'PRODUCCIÓN'}")
        logger.info("=" * 70)

        # Verificar/aplicar migración
        if not self.verificar_migracion():
            logger.info("Migración 023 no aplicada. Aplicando...")
            if not self.aplicar_migracion():
                return {'error': 'No se pudo aplicar la migración'}

        # Detectar grupos
        grupos = self.detectar_grupos()

        # Marcar en BD
        stats = self.marcar_republicaciones(grupos, dry_run=dry_run)

        # Log resumen
        logger.info("")
        logger.info("=" * 70)
        logger.info("RESUMEN REPUBLICACIONES")
        logger.info("=" * 70)
        for k, v in stats.items():
            if isinstance(v, int):
                logger.info(f"  {k}: {v:,}")
            else:
                logger.info(f"  {k}: {v}")
        logger.info("=" * 70)

        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Detecta ofertas republicadas (demanda insatisfecha)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='No modificar BD, solo mostrar qué se haría'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='Mostrar estadísticas de republicaciones existentes'
    )
    parser.add_argument(
        '--db', type=Path, default=DB_PATH,
        help=f'Ruta a la BD (default: {DB_PATH})'
    )

    args = parser.parse_args()

    with DetectorRepublicaciones(args.db) as detector:
        if args.stats:
            # Solo mostrar estadísticas
            if not detector.verificar_migracion():
                print("Migración 023 no aplicada. Ejecutar sin --stats primero.")
                return

            stats = detector.obtener_estadisticas()

            print(f"\n{'=' * 60}")
            print("ESTADÍSTICAS DE REPUBLICACIONES")
            print(f"{'=' * 60}")
            print(f"  Grupos con republicaciones: {stats['total_grupos']:,}")
            print(f"  Total ofertas republicadas: {stats['total_republicaciones']:,}")

            if stats['distribucion']:
                print(f"\n  Distribución por veces publicada:")
                for veces, cantidad in sorted(stats['distribucion'].items()):
                    label = "vez" if veces == 1 else "veces"
                    print(f"    {veces} {label}: {cantidad:,} grupos")

            if stats['top_10']:
                print(f"\n  Top 10 más republicadas:")
                print(f"  {'Título':<35} {'Empresa':<20} {'Veces':>5} {'Días':>5}")
                print(f"  {'-'*35} {'-'*20} {'-'*5} {'-'*5}")
                for item in stats['top_10']:
                    titulo = (item['titulo'][:32] + '...') if len(item['titulo'] or '') > 35 else item['titulo']
                    empresa = (item['empresa'][:17] + '...') if len(item['empresa'] or '') > 20 else item['empresa']
                    print(f"  {titulo:<35} {empresa:<20} {item['veces']:>5} {item['dias_persistencia'] or 0:>5}")

            if stats['top_empresas']:
                print(f"\n  Top 10 empresas con más republicaciones:")
                print(f"  {'Empresa':<35} {'Puestos':>8} {'Repubs':>7}")
                print(f"  {'-'*35} {'-'*8} {'-'*7}")
                for item in stats['top_empresas']:
                    empresa = (item['empresa'][:32] + '...') if len(item['empresa'] or '') > 35 else item['empresa']
                    print(f"  {empresa:<35} {item['puestos_republicados']:>8} {item['total_repubs']:>7}")

            print(f"{'=' * 60}\n")
        else:
            # Ejecutar detección
            stats = detector.ejecutar(dry_run=args.dry_run)

            if not args.dry_run and stats.get('grupos_detectados', 0) > 0:
                print("\nPara ver estadísticas detalladas:")
                print("  python database/detectar_republicaciones.py --stats")


if __name__ == '__main__':
    main()
