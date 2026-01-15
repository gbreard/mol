#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verificar_ofertas_activas.py
============================
Verifica si las ofertas en la BD siguen activas en la API de Bumeran.

Estrategia:
1. Obtener todas las ofertas con estado='activa' de la BD
2. Consultar la API por cada oferta (o por lotes)
3. Si la oferta NO existe en la API → marcar como 'baja'
4. Actualizar fecha_ultimo_visto para las que sí existen

Optimizaciones:
- Verificar solo ofertas no vistas en los últimos N días
- Batch de verificación por página de la API
- Rate limiting para no saturar la API

Uso:
    python verificar_ofertas_activas.py
    python verificar_ofertas_activas.py --dias-sin-ver 3
    python verificar_ofertas_activas.py --limite 1000
"""

import sqlite3
import requests
import time
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, List, Dict, Tuple
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'


class VerificadorOfertas:
    """Verifica si ofertas siguen activas en la API"""

    def __init__(self, db_path: Path = DB_PATH, delay: float = 1.0):
        self.db_path = db_path
        self.delay = delay
        self.session = requests.Session()
        self.session_token = str(uuid.uuid4())

        # Headers para API Bumeran
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-site-id': 'BMAR',
            'x-pre-session-token': self.session_token
        }

        # Estadísticas
        self.stats = {
            'verificadas': 0,
            'siguen_activas': 0,
            'dadas_de_baja': 0,
            'errores': 0
        }

    def obtener_ofertas_a_verificar(
        self,
        dias_sin_ver: int = 1,
        limite: int = None
    ) -> List[Dict]:
        """
        Obtiene ofertas activas que no han sido verificadas recientemente.

        Args:
            dias_sin_ver: Solo verificar ofertas no vistas en N días
            limite: Máximo de ofertas a verificar (None = todas)

        Returns:
            Lista de ofertas a verificar
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        fecha_limite = (datetime.now() - timedelta(days=dias_sin_ver)).isoformat()

        query = """
            SELECT id_oferta, titulo, fecha_publicacion_iso, fecha_ultimo_visto
            FROM ofertas
            WHERE estado_oferta = 'activa'
              AND (fecha_ultimo_visto IS NULL OR fecha_ultimo_visto < ?)
            ORDER BY fecha_ultimo_visto ASC NULLS FIRST
        """

        if limite:
            query += f" LIMIT {limite}"

        cursor.execute(query, (fecha_limite,))
        ofertas = [dict(row) for row in cursor.fetchall()]

        conn.close()

        logger.info(f"Ofertas a verificar: {len(ofertas):,}")
        return ofertas

    def verificar_oferta_existe(self, id_oferta: int) -> bool:
        """
        Verifica si una oferta específica existe en la API.

        La API de Bumeran no tiene endpoint directo por ID,
        así que usamos el endpoint de detalle.

        Args:
            id_oferta: ID de la oferta

        Returns:
            True si existe, False si no
        """
        url = f"https://www.bumeran.com.ar/api/avisos/{id_oferta}"

        try:
            response = self.session.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                return False
            else:
                logger.warning(f"Status inesperado {response.status_code} para oferta {id_oferta}")
                return True  # Asumir que existe si hay error

        except Exception as e:
            logger.error(f"Error verificando oferta {id_oferta}: {e}")
            self.stats['errores'] += 1
            return True  # Asumir que existe si hay error de conexión

    def obtener_ids_activos_por_pagina(self, max_paginas: int = 100) -> Set[int]:
        """
        Obtiene todos los IDs activos scrapeando la API completa.

        Esta es la estrategia más eficiente: en lugar de verificar
        oferta por oferta, obtenemos TODOS los IDs activos de una vez.

        Args:
            max_paginas: Máximo de páginas a scrapear

        Returns:
            Set de IDs de ofertas activas
        """
        logger.info("Obteniendo todos los IDs activos de la API...")

        ids_activos = set()
        page = 0
        page_size = 100  # Máximo permitido por la API

        while page < max_paginas:
            payload = {
                "pageSize": page_size,
                "page": page,
                "sort": "FECHA"
            }

            try:
                response = self.session.post(
                    "https://www.bumeran.com.ar/api/avisos/searchV2",
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code != 200:
                    logger.error(f"Error en página {page}: status {response.status_code}")
                    break

                data = response.json()
                ofertas = data.get('content', [])

                if not ofertas:
                    logger.info(f"No más ofertas en página {page}")
                    break

                for oferta in ofertas:
                    if oferta.get('id'):
                        ids_activos.add(int(oferta['id']))

                total = data.get('total', 0)
                logger.info(f"Página {page}: {len(ofertas)} ofertas | Total acumulado: {len(ids_activos):,} | API total: {total:,}")

                # Verificar si ya tenemos todos
                if len(ids_activos) >= total:
                    logger.info("Todos los IDs obtenidos")
                    break

                page += 1
                time.sleep(self.delay)

            except Exception as e:
                logger.error(f"Error en página {page}: {e}")
                break

        logger.info(f"Total IDs activos en API: {len(ids_activos):,}")
        return ids_activos

    def detectar_bajas_batch(self, ids_activos_api: Set[int]) -> Tuple[Set[int], Set[int]]:
        """
        Detecta qué ofertas de la BD ya no están en la API.

        Args:
            ids_activos_api: Set de IDs activos en la API

        Returns:
            Tuple (ids_dados_de_baja, ids_siguen_activos)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Obtener todos los IDs con estado 'activa' en la BD
        cursor.execute("""
            SELECT id_oferta
            FROM ofertas
            WHERE estado_oferta = 'activa'
        """)

        ids_bd_activas = {row[0] for row in cursor.fetchall()}
        conn.close()

        logger.info(f"Ofertas marcadas como 'activa' en BD: {len(ids_bd_activas):,}")

        # Detectar diferencias
        ids_dados_de_baja = ids_bd_activas - ids_activos_api
        ids_siguen_activos = ids_bd_activas & ids_activos_api

        logger.info(f"Siguen activas: {len(ids_siguen_activos):,}")
        logger.info(f"Dadas de baja: {len(ids_dados_de_baja):,}")

        return ids_dados_de_baja, ids_siguen_activos

    def actualizar_estado_ofertas(
        self,
        ids_baja: Set[int],
        ids_activas: Set[int]
    ) -> Dict:
        """
        Actualiza el estado de las ofertas en la BD.

        Args:
            ids_baja: IDs de ofertas que ya no existen
            ids_activas: IDs de ofertas que siguen activas

        Returns:
            Dict con estadísticas de actualización
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        ahora = datetime.now().isoformat()

        # Marcar como 'baja' las que desaparecieron
        if ids_baja:
            placeholders = ','.join(['?'] * len(ids_baja))
            cursor.execute(f"""
                UPDATE ofertas
                SET estado_oferta = 'baja',
                    fecha_baja = ?
                WHERE id_oferta IN ({placeholders})
                  AND estado_oferta = 'activa'
            """, (ahora, *ids_baja))

            bajas_actualizadas = cursor.rowcount
            logger.info(f"Ofertas marcadas como baja: {bajas_actualizadas:,}")
        else:
            bajas_actualizadas = 0

        # Actualizar fecha_ultimo_visto para las activas
        if ids_activas:
            # Hacer en batches para evitar límite de variables SQLite
            batch_size = 500
            ids_list = list(ids_activas)
            activas_actualizadas = 0

            for i in range(0, len(ids_list), batch_size):
                batch = ids_list[i:i+batch_size]
                placeholders = ','.join(['?'] * len(batch))
                cursor.execute(f"""
                    UPDATE ofertas
                    SET fecha_ultimo_visto = ?,
                        veces_vista = COALESCE(veces_vista, 0) + 1
                    WHERE id_oferta IN ({placeholders})
                """, (ahora, *batch))
                activas_actualizadas += cursor.rowcount

            logger.info(f"Ofertas actualizadas (fecha_ultimo_visto): {activas_actualizadas:,}")
        else:
            activas_actualizadas = 0

        conn.commit()
        conn.close()

        return {
            'bajas_marcadas': bajas_actualizadas,
            'activas_actualizadas': activas_actualizadas
        }

    def calcular_permanencia(self) -> int:
        """
        Calcula días de permanencia para ofertas dadas de baja.

        Returns:
            Número de ofertas actualizadas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calcular días de permanencia
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
              AND dias_publicada IS NULL
        """)

        actualizadas = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Permanencia calculada para {actualizadas:,} ofertas")
        return actualizadas

    def ejecutar_verificacion_completa(self, max_paginas: int = 200) -> Dict:
        """
        Ejecuta el ciclo completo de verificación.

        1. Obtiene todos los IDs activos de la API
        2. Compara con IDs en BD
        3. Marca bajas
        4. Actualiza fecha_ultimo_visto
        5. Calcula permanencia

        Returns:
            Dict con estadísticas
        """
        logger.info("="*70)
        logger.info("VERIFICACIÓN DE OFERTAS ACTIVAS")
        logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)

        # 1. Obtener IDs activos de la API
        ids_api = self.obtener_ids_activos_por_pagina(max_paginas)

        if not ids_api:
            logger.error("No se pudieron obtener IDs de la API")
            return {'error': 'No se pudieron obtener IDs de la API'}

        # 2. Detectar bajas
        ids_baja, ids_activas = self.detectar_bajas_batch(ids_api)

        # 3. Actualizar BD
        resultado = self.actualizar_estado_ofertas(ids_baja, ids_activas)

        # 4. Calcular permanencia
        permanencia_calculada = self.calcular_permanencia()

        # 5. Estadísticas finales
        stats = {
            'ids_en_api': len(ids_api),
            'bajas_detectadas': len(ids_baja),
            'activas_confirmadas': len(ids_activas),
            'bajas_marcadas_bd': resultado['bajas_marcadas'],
            'activas_actualizadas_bd': resultado['activas_actualizadas'],
            'permanencia_calculada': permanencia_calculada
        }

        logger.info("")
        logger.info("="*70)
        logger.info("RESUMEN")
        logger.info("="*70)
        for k, v in stats.items():
            logger.info(f"  {k}: {v:,}")
        logger.info("="*70)

        return stats


def aplicar_migracion():
    """Aplica la migración para agregar campos de permanencia"""
    migration_path = Path(__file__).parent / 'migrations' / '001_add_permanencia_fields.sql'

    if not migration_path.exists():
        logger.error(f"Migración no encontrada: {migration_path}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si ya se aplicó la migración
    cursor.execute("PRAGMA table_info(ofertas)")
    columnas = {row[1] for row in cursor.fetchall()}

    if 'estado_oferta' in columnas:
        logger.info("Migración ya aplicada")
        conn.close()
        return True

    logger.info("Aplicando migración 001_add_permanencia_fields.sql...")

    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Ejecutar cada statement por separado (SQLite no soporta múltiples en execute)
    for statement in sql.split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
            except Exception as e:
                logger.warning(f"Error en statement: {e}")

    conn.commit()
    conn.close()

    logger.info("Migración aplicada exitosamente")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Verifica ofertas activas y detecta bajas'
    )
    parser.add_argument(
        '--max-paginas',
        type=int,
        default=200,
        help='Máximo de páginas a scrapear de la API (default: 200)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay entre requests en segundos (default: 1.0)'
    )
    parser.add_argument(
        '--migrar',
        action='store_true',
        help='Aplicar migración de BD antes de verificar'
    )

    args = parser.parse_args()

    # Aplicar migración si se solicita
    if args.migrar:
        if not aplicar_migracion():
            return

    # Ejecutar verificación
    verificador = VerificadorOfertas(delay=args.delay)
    stats = verificador.ejecutar_verificacion_completa(max_paginas=args.max_paginas)

    print()
    print("Verificación completada. Estadísticas guardadas.")


if __name__ == '__main__':
    main()
