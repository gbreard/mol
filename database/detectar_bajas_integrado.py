#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
detectar_bajas_integrado.py
===========================
Detecta ofertas dadas de baja usando los IDs del scraping regular.

ESTRATEGIA OPTIMIZADA:
- NO hace requests extra a la API
- Usa los IDs que el scraper YA trae en cada ejecución
- Se ejecuta DESPUÉS del scraping semanal
- Compara IDs scrapeados vs IDs en BD marcados como 'activa'

Flujo:
1. Scraper corre normalmente → guarda ofertas en BD
2. Este script lee IDs del último scraping (desde tracking o BD)
3. Compara con ofertas marcadas como 'activa' en BD
4. Las que NO aparecieron → marca como 'baja'
5. Calcula permanencia

Uso:
    # Después del scraping semanal:
    python detectar_bajas_integrado.py

    # Con archivo de IDs específico:
    python detectar_bajas_integrado.py --ids-file data/tracking/bumeran_scraped_ids.json

    # Modo dry-run (no modifica BD):
    python detectar_bajas_integrado.py --dry-run
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, Dict, Tuple, Optional
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rutas
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
TRACKING_PATH = Path(__file__).parent.parent / '01_sources' / 'bumeran' / 'tracking' / 'scraped_ids.json'


class DetectorBajasIntegrado:
    """Detecta bajas usando IDs del scraping regular"""

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

    def obtener_ids_ultimo_scraping(self, tracking_file: Path = TRACKING_PATH) -> Set[int]:
        """
        Obtiene los IDs del último scraping desde el archivo de tracking.

        El IncrementalTracker guarda todos los IDs vistos en cada sesión.
        Usamos eso como "snapshot" de ofertas activas.

        Args:
            tracking_file: Ruta al archivo de tracking

        Returns:
            Set de IDs vistos en el último scraping
        """
        if not tracking_file.exists():
            logger.error(f"Archivo de tracking no encontrado: {tracking_file}")
            return set()

        with open(tracking_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        scraped_ids = data.get('scraped_ids', {})

        # El tracking puede ser dict con timestamps o lista simple
        if isinstance(scraped_ids, dict):
            ids = {int(id_) for id_ in scraped_ids.keys()}
        elif isinstance(scraped_ids, list):
            ids = {int(id_) for id_ in scraped_ids}
        else:
            ids = set()

        logger.info(f"IDs en tracking: {len(ids):,}")
        logger.info(f"Última actualización: {data.get('last_update', 'desconocida')}")

        return ids

    def obtener_ids_recientes_bd(self, dias: int = 7) -> Set[int]:
        """
        Alternativa: obtener IDs scrapeados recientemente desde la BD.

        Útil si el tracking no está disponible.

        Args:
            dias: Considerar ofertas scrapeadas en los últimos N días

        Returns:
            Set de IDs scrapeados recientemente
        """
        cursor = self.conn.cursor()

        fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()

        cursor.execute("""
            SELECT DISTINCT id_oferta
            FROM ofertas
            WHERE scrapeado_en >= ?
        """, (fecha_limite,))

        ids = {row[0] for row in cursor.fetchall()}

        logger.info(f"IDs scrapeados en últimos {dias} días: {len(ids):,}")
        return ids

    def obtener_ids_activos_bd(self) -> Set[int]:
        """
        Obtiene todos los IDs marcados como 'activa' en la BD.

        Returns:
            Set de IDs con estado 'activa'
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id_oferta
            FROM ofertas
            WHERE estado_oferta = 'activa'
               OR estado_oferta IS NULL
        """)

        ids = {row[0] for row in cursor.fetchall()}

        logger.info(f"Ofertas marcadas como activas en BD: {len(ids):,}")
        return ids

    def detectar_bajas(
        self,
        ids_vistos: Set[int],
        ids_activos_bd: Set[int]
    ) -> Tuple[Set[int], Set[int]]:
        """
        Detecta qué ofertas fueron dadas de baja.

        Lógica:
        - Si una oferta está en BD como 'activa' pero NO apareció en el scraping
          → probablemente fue dada de baja

        Args:
            ids_vistos: IDs que aparecieron en el último scraping
            ids_activos_bd: IDs marcados como 'activa' en BD

        Returns:
            Tuple (ids_baja, ids_confirmadas_activas)
        """
        # Ofertas que deberían seguir activas pero no aparecieron
        ids_posible_baja = ids_activos_bd - ids_vistos

        # Ofertas confirmadas como activas (aparecieron en scraping)
        ids_confirmadas = ids_activos_bd & ids_vistos

        logger.info(f"Análisis de bajas:")
        logger.info(f"  Confirmadas activas: {len(ids_confirmadas):,}")
        logger.info(f"  Posibles bajas: {len(ids_posible_baja):,}")

        return ids_posible_baja, ids_confirmadas

    def marcar_bajas(self, ids_baja: Set[int], dry_run: bool = False) -> int:
        """
        Marca ofertas como dadas de baja.

        Args:
            ids_baja: IDs a marcar como baja
            dry_run: Si True, no modifica la BD

        Returns:
            Número de ofertas marcadas
        """
        if not ids_baja:
            logger.info("No hay ofertas para marcar como baja")
            return 0

        if dry_run:
            logger.info(f"[DRY-RUN] Se marcarían {len(ids_baja):,} ofertas como baja")
            return 0

        cursor = self.conn.cursor()
        ahora = datetime.now().isoformat()

        # Actualizar en batches
        batch_size = 500
        ids_list = list(ids_baja)
        total_actualizadas = 0

        for i in range(0, len(ids_list), batch_size):
            batch = ids_list[i:i+batch_size]
            placeholders = ','.join(['?'] * len(batch))

            cursor.execute(f"""
                UPDATE ofertas
                SET estado_oferta = 'baja',
                    fecha_baja = ?
                WHERE id_oferta IN ({placeholders})
                  AND (estado_oferta = 'activa' OR estado_oferta IS NULL)
            """, (ahora, *batch))

            total_actualizadas += cursor.rowcount

        self.conn.commit()

        logger.info(f"Ofertas marcadas como baja: {total_actualizadas:,}")
        return total_actualizadas

    def actualizar_fecha_ultimo_visto(self, ids_activas: Set[int], dry_run: bool = False) -> int:
        """
        Actualiza fecha_ultimo_visto para ofertas confirmadas activas.

        Args:
            ids_activas: IDs confirmados como activos
            dry_run: Si True, no modifica la BD

        Returns:
            Número de ofertas actualizadas
        """
        if not ids_activas:
            return 0

        if dry_run:
            logger.info(f"[DRY-RUN] Se actualizarían {len(ids_activas):,} ofertas")
            return 0

        cursor = self.conn.cursor()
        ahora = datetime.now().isoformat()

        # Actualizar en batches
        batch_size = 500
        ids_list = list(ids_activas)
        total_actualizadas = 0

        for i in range(0, len(ids_list), batch_size):
            batch = ids_list[i:i+batch_size]
            placeholders = ','.join(['?'] * len(batch))

            cursor.execute(f"""
                UPDATE ofertas
                SET fecha_ultimo_visto = ?,
                    estado_oferta = 'activa',
                    veces_vista = COALESCE(veces_vista, 0) + 1
                WHERE id_oferta IN ({placeholders})
            """, (ahora, *batch))

            total_actualizadas += cursor.rowcount

        self.conn.commit()

        logger.info(f"Ofertas actualizadas (fecha_ultimo_visto): {total_actualizadas:,}")
        return total_actualizadas

    def calcular_permanencia(self, dry_run: bool = False) -> int:
        """
        Calcula días de permanencia y categoriza.

        Returns:
            Número de ofertas procesadas
        """
        if dry_run:
            logger.info("[DRY-RUN] Se calcularía permanencia")
            return 0

        cursor = self.conn.cursor()

        # Calcular para ofertas dadas de baja
        cursor.execute("""
            UPDATE ofertas
            SET dias_publicada = CAST(
                julianday(fecha_baja) - julianday(fecha_publicacion_iso) AS INTEGER
            ),
            categoria_permanencia = CASE
                WHEN julianday(fecha_baja) - julianday(fecha_publicacion_iso) < 7 THEN 'baja'
                WHEN julianday(fecha_baja) - julianday(fecha_publicacion_iso) < 30 THEN 'media'
                ELSE 'alta'
            END
            WHERE estado_oferta = 'baja'
              AND fecha_baja IS NOT NULL
              AND fecha_publicacion_iso IS NOT NULL
              AND (dias_publicada IS NULL OR categoria_permanencia IS NULL)
        """)

        actualizadas_baja = cursor.rowcount

        # Calcular para ofertas activas (días hasta hoy)
        cursor.execute("""
            UPDATE ofertas
            SET dias_publicada = CAST(
                julianday('now') - julianday(fecha_publicacion_iso) AS INTEGER
            ),
            categoria_permanencia = CASE
                WHEN julianday('now') - julianday(fecha_publicacion_iso) < 7 THEN 'baja'
                WHEN julianday('now') - julianday(fecha_publicacion_iso) < 30 THEN 'media'
                ELSE 'alta'
            END
            WHERE estado_oferta = 'activa'
              AND fecha_publicacion_iso IS NOT NULL
        """)

        actualizadas_activas = cursor.rowcount

        self.conn.commit()

        total = actualizadas_baja + actualizadas_activas
        logger.info(f"Permanencia calculada: {total:,} ofertas")
        logger.info(f"  (bajas: {actualizadas_baja:,}, activas: {actualizadas_activas:,})")

        return total

    def ejecutar(
        self,
        tracking_file: Optional[Path] = None,
        usar_bd_reciente: bool = False,
        dias_recientes: int = 7,
        dry_run: bool = False
    ) -> Dict:
        """
        Ejecuta el proceso completo de detección de bajas.

        Args:
            tracking_file: Archivo de tracking (opcional)
            usar_bd_reciente: Usar IDs recientes de BD en vez de tracking
            dias_recientes: Días a considerar si usar_bd_reciente=True
            dry_run: No modificar BD

        Returns:
            Dict con estadísticas
        """
        logger.info("="*70)
        logger.info("DETECCIÓN DE BAJAS INTEGRADA")
        logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Modo: {'DRY-RUN' if dry_run else 'PRODUCCIÓN'}")
        logger.info("="*70)

        # 1. Obtener IDs del último scraping
        if usar_bd_reciente:
            ids_vistos = self.obtener_ids_recientes_bd(dias_recientes)
        else:
            tf = tracking_file or TRACKING_PATH
            ids_vistos = self.obtener_ids_ultimo_scraping(tf)

        if not ids_vistos:
            logger.error("No se encontraron IDs del scraping. Abortando.")
            return {'error': 'No IDs found'}

        # 2. Obtener IDs activos en BD
        ids_activos_bd = self.obtener_ids_activos_bd()

        # 3. Detectar bajas
        ids_baja, ids_confirmadas = self.detectar_bajas(ids_vistos, ids_activos_bd)

        # 4. Marcar bajas
        n_bajas = self.marcar_bajas(ids_baja, dry_run)

        # 5. Actualizar fecha_ultimo_visto
        n_actualizadas = self.actualizar_fecha_ultimo_visto(ids_confirmadas, dry_run)

        # 6. Calcular permanencia
        n_permanencia = self.calcular_permanencia(dry_run)

        # Estadísticas
        stats = {
            'fecha_ejecucion': datetime.now().isoformat(),
            'ids_en_scraping': len(ids_vistos),
            'ids_activos_bd': len(ids_activos_bd),
            'bajas_detectadas': len(ids_baja),
            'bajas_marcadas': n_bajas,
            'activas_confirmadas': len(ids_confirmadas),
            'activas_actualizadas': n_actualizadas,
            'permanencia_calculada': n_permanencia,
            'dry_run': dry_run
        }

        logger.info("")
        logger.info("="*70)
        logger.info("RESUMEN")
        logger.info("="*70)
        for k, v in stats.items():
            if k != 'fecha_ejecucion':
                logger.info(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")
        logger.info("="*70)

        return stats


def verificar_migracion_aplicada(db_path: Path) -> bool:
    """Verifica si la migración de permanencia fue aplicada"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(ofertas)")
    columnas = {row[1] for row in cursor.fetchall()}

    conn.close()

    return 'estado_oferta' in columnas


def main():
    parser = argparse.ArgumentParser(
        description='Detecta bajas usando IDs del scraping regular'
    )
    parser.add_argument(
        '--ids-file',
        type=Path,
        help='Archivo de tracking con IDs (default: bumeran_scraped_ids.json)'
    )
    parser.add_argument(
        '--usar-bd',
        action='store_true',
        help='Usar IDs recientes de BD en vez de tracking'
    )
    parser.add_argument(
        '--dias',
        type=int,
        default=7,
        help='Días a considerar con --usar-bd (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='No modificar BD, solo mostrar qué se haría'
    )
    parser.add_argument(
        '--migrar',
        action='store_true',
        help='Aplicar migración de BD si no está aplicada'
    )

    args = parser.parse_args()

    # Verificar/aplicar migración
    if not verificar_migracion_aplicada(DB_PATH):
        if args.migrar:
            logger.info("Aplicando migración...")
            from scripts.scraping.verificar_ofertas_activas import aplicar_migracion
            aplicar_migracion()
        else:
            logger.error("Migración no aplicada. Ejecutar con --migrar primero.")
            return

    # Ejecutar detección
    with DetectorBajasIntegrado() as detector:
        stats = detector.ejecutar(
            tracking_file=args.ids_file,
            usar_bd_reciente=args.usar_bd,
            dias_recientes=args.dias,
            dry_run=args.dry_run
        )

    if not args.dry_run:
        print("\n✓ Detección completada. Ejecutar 'python calcular_permanencia.py' para ver estadísticas.")


if __name__ == '__main__':
    main()
