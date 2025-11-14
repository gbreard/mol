"""
Database Manager v2.0 - DUAL-WRITE STRATEGY
============================================

Estrategia de migración gradual:
- WRITE v1 (producción): tabla ofertas (38 columnas) - CRITICAL
- WRITE v2 (nuevo): ofertas_raw + scraping_sessions - WARNING si falla

Garantías:
1. v1 (producción) SIEMPRE funciona → si falla, lanza excepción
2. v2 (nuevo) es opcional → si falla, solo logging WARNING
3. Scheduler Monday/Thursday 8:00 NO SE INTERRUMPE
4. Tracking file bumeran_scraped_ids.json NO SE CORROMPE

Uso:
    from database.db_manager_v2 import DatabaseManagerV2

    db = DatabaseManagerV2(
        db_path='database/bumeran_scraping.db',
        enable_dual_write=True  # Activar dual-write
    )

    # API 100% compatible con db_manager.py original
    db.insert_ofertas(ofertas_df)
"""

import sqlite3
import pandas as pd
import json
import hashlib
import uuid
from typing import List, Dict, Optional
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManagerV2:
    """
    Database Manager con soporte dual-write v1/v2.

    API 100% compatible con DatabaseManager original.
    """

    def __init__(self,
                 db_path: str = 'database/bumeran_scraping.db',
                 enable_dual_write: bool = True):
        """
        Inicializa Database Manager con dual-write

        Args:
            db_path: Ruta a SQLite
            enable_dual_write: True = escribe a v1 + v2, False = solo v1 (legacy)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.enable_dual_write = enable_dual_write
        self.conn = None
        self.cursor = None

        # Session tracking para v2
        self.current_session_id = None
        self.current_session_uuid = None

        logger.info(f"DatabaseManagerV2 inicializado")
        logger.info(f"  DB: {self.db_path}")
        logger.info(f"  Dual-write: {'ENABLED' if enable_dual_write else 'DISABLED (legacy mode)'}")

    def connect(self):
        """Establece conexión con SQLite"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Conexión establecida: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a SQLite: {e}")
            return False

    def disconnect(self):
        """Cierra conexión"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Conexión cerrada")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.conn.rollback()
            logger.error(f"Error en transacción: {exc_val}")
        else:
            self.conn.commit()
        self.disconnect()

    # ============================================
    # v2 HELPERS: SCRAPING SESSIONS
    # ============================================

    def create_scraping_session(self,
                                source: str = 'bumeran',
                                mode: str = 'incremental') -> tuple:
        """
        Crea una nueva sesión de scraping en v2

        Args:
            source: 'bumeran', 'indeed', etc
            mode: 'full', 'incremental'

        Returns:
            (session_id, session_uuid)
        """
        if not self.enable_dual_write:
            return (None, None)

        try:
            session_uuid = str(uuid.uuid4())

            query = """
                INSERT INTO scraping_sessions (
                    session_uuid, source, mode, start_time, status
                ) VALUES (?, ?, ?, ?, 'running')
            """

            self.cursor.execute(query, (
                session_uuid,
                source,
                mode,
                datetime.now().isoformat()
            ))

            session_id = self.cursor.lastrowid
            self.current_session_id = session_id
            self.current_session_uuid = session_uuid

            logger.info(f"[v2] Sesión creada: {session_id} ({session_uuid[:8]}...)")
            return (session_id, session_uuid)

        except Exception as e:
            logger.warning(f"[v2] Error creando sesión (NO CRÍTICO): {e}")
            return (None, None)

    def close_scraping_session(self,
                              ofertas_total: int = 0,
                              ofertas_nuevas: int = 0,
                              status: str = 'completed'):
        """Cierra sesión de scraping"""
        if not self.enable_dual_write or not self.current_session_id:
            return

        try:
            query = """
                UPDATE scraping_sessions
                SET end_time = ?,
                    ofertas_total = ?,
                    ofertas_nuevas = ?,
                    status = ?
                WHERE id = ?
            """

            self.cursor.execute(query, (
                datetime.now().isoformat(),
                ofertas_total,
                ofertas_nuevas,
                status,
                self.current_session_id
            ))

            logger.info(f"[v2] Sesión cerrada: {self.current_session_id}")

        except Exception as e:
            logger.warning(f"[v2] Error cerrando sesión (NO CRÍTICO): {e}")

    # ============================================
    # v2 HELPERS: OFERTAS RAW
    # ============================================

    def _insert_ofertas_v2_raw(self, ofertas: pd.DataFrame) -> int:
        """
        Inserta ofertas en formato RAW (v2)

        Args:
            ofertas: DataFrame con ofertas

        Returns:
            Número de ofertas insertadas en v2
        """
        if not self.enable_dual_write:
            return 0

        try:
            count = 0

            for _, row in ofertas.iterrows():
                # Convertir row a JSON (raw inmutable)
                raw_json = row.to_json()

                # Content hash para detección de cambios
                content_hash = hashlib.sha256(raw_json.encode()).hexdigest()

                # Datos principales
                id_oferta = row.get('id_oferta')
                titulo = row.get('titulo', '')
                empresa = row.get('empresa', '')
                url = row.get('url_oferta', '')

                # INSERT OR IGNORE (no actualizar raw inmutable)
                query = """
                    INSERT OR IGNORE INTO ofertas_raw (
                        id_oferta, scraping_session_id, raw_json,
                        content_hash, titulo, empresa, url_oferta,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """

                self.cursor.execute(query, (
                    id_oferta,
                    self.current_session_id,
                    raw_json,
                    content_hash,
                    titulo,
                    empresa,
                    url,
                    datetime.now().isoformat()
                ))

                if self.cursor.rowcount > 0:
                    count += 1

            logger.info(f"[v2] {count} ofertas insertadas en ofertas_raw")
            return count

        except Exception as e:
            logger.warning(f"[v2] Error insertando ofertas_raw (NO CRÍTICO): {e}")
            return 0

    # ============================================
    # DUAL-WRITE: INSERT OFERTAS
    # ============================================

    def insert_ofertas(self, ofertas: pd.DataFrame) -> int:
        """
        Inserta ofertas con DUAL-WRITE strategy

        FLUJO:
        1. v1 (producción): INSERT OR REPLACE en tabla `ofertas` → CRITICAL
        2. v2 (nuevo): INSERT en `ofertas_raw` → WARNING si falla

        Args:
            ofertas: DataFrame con ofertas procesadas

        Returns:
            Número de ofertas insertadas en v1 (producción)
        """
        if ofertas.empty:
            logger.warning("DataFrame vacío, no hay ofertas para insertar")
            return 0

        logger.info(f"Insertando {len(ofertas)} ofertas (dual-write={'ON' if self.enable_dual_write else 'OFF'})...")

        # ========================================
        # PASO 1: v1 (PRODUCCIÓN) - CRITICAL
        # ========================================

        # Mapeo exacto del db_manager.py original
        column_mapping = {
            'id_oferta': 'id_oferta',
            'id_empresa': 'id_empresa',
            'titulo': 'titulo',
            'empresa': 'empresa',
            'descripcion': 'descripcion',
            'confidencial': 'confidencial',
            'localizacion': 'localizacion',
            'modalidad_trabajo': 'modalidad_trabajo',
            'tipo_trabajo': 'tipo_trabajo',
            'fecha_publicacion_original': 'fecha_publicacion_original',
            'fecha_publicacion_iso': 'fecha_publicacion_iso',
            'fecha_publicacion_datetime': 'fecha_publicacion_datetime',
            'fecha_hora_publicacion_original': 'fecha_hora_publicacion_original',
            'fecha_hora_publicacion_iso': 'fecha_hora_publicacion_iso',
            'fecha_hora_publicacion_datetime': 'fecha_hora_publicacion_datetime',
            'fecha_modificado_original': 'fecha_modificado_original',
            'fecha_modificado_iso': 'fecha_modificado_iso',
            'fecha_modificado_datetime': 'fecha_modificado_datetime',
            'cantidad_vacantes': 'cantidad_vacantes',
            'apto_discapacitado': 'apto_discapacitado',
            'id_area': 'id_area',
            'id_subarea': 'id_subarea',
            'id_pais': 'id_pais',
            'logo_url': 'logo_url',
            'empresa_validada': 'empresa_validada',
            'empresa_pro': 'empresa_pro',
            'promedio_empresa': 'promedio_empresa',
            'plan_publicacion_id': 'plan_publicacion_id',
            'plan_publicacion_nombre': 'plan_publicacion_nombre',
            'portal': 'portal',
            'tipo_aviso': 'tipo_aviso',
            'tiene_preguntas': 'tiene_preguntas',
            'salario_obligatorio': 'salario_obligatorio',
            'alta_revision_perfiles': 'alta_revision_perfiles',
            'guardado': 'guardado',
            'gptw_url': 'gptw_url',
            'url_oferta': 'url_oferta',
            'scrapeado_en': 'scrapeado_en'
        }

        columns = list(column_mapping.values())
        values = []

        for _, row in ofertas.iterrows():
            row_values = []
            for df_col in column_mapping.keys():
                if df_col in ofertas.columns:
                    val = row[df_col]
                    if pd.isna(val):
                        row_values.append(None)
                    elif isinstance(val, bool):
                        row_values.append(1 if val else 0)
                    else:
                        row_values.append(val)
                else:
                    row_values.append(None)
            values.append(tuple(row_values))

        placeholders = ','.join(['?'] * len(columns))
        query_v1 = f"""
            INSERT OR REPLACE INTO ofertas ({','.join(columns)})
            VALUES ({placeholders})
        """

        try:
            logger.debug(f"[v1] Insertando {len(values)} ofertas...")
            self.cursor.executemany(query_v1, values)
            self.conn.commit()

            # Verificar count
            self.cursor.execute("SELECT COUNT(*) FROM ofertas")
            count_v1 = self.cursor.fetchone()[0]

            logger.info(f"[v1] OK: {len(ofertas)} ofertas insertadas (total v1: {count_v1:,})")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"[v1] CRITICAL ERROR insertando ofertas: {e}")
            raise  # LANZAR EXCEPCIÓN - v1 es CRÍTICO

        # ========================================
        # PASO 2: v2 (NUEVO) - WARNING si falla
        # ========================================

        if self.enable_dual_write:
            try:
                # Crear sesión si no existe
                if not self.current_session_id:
                    self.create_scraping_session(
                        source='bumeran',
                        mode='incremental',
                        metadata={'auto_session': True}
                    )

                # Insertar en ofertas_raw
                count_v2 = self._insert_ofertas_v2_raw(ofertas)

                logger.info(f"[v2] OK: {count_v2} ofertas insertadas en ofertas_raw")

            except Exception as e:
                # v2 falla NO es crítico → solo log WARNING
                logger.warning(f"[v2] Error insertando ofertas_raw (NO CRÍTICO): {e}")
                logger.warning("[v2] Producción (v1) NO afectada, continúa funcionando")

        return len(ofertas)

    # ============================================
    # LEGACY API: 100% COMPATIBLE
    # ============================================

    def insert_metricas(self, metrics_report: Dict) -> int:
        """Inserta métricas (legacy API - solo v1)"""
        logger.info("Insertando métricas de scraping...")

        query = """
            INSERT INTO metricas_scraping (
                start_time, end_time, total_time_seconds,
                pages_scraped, pages_failed, pages_total,
                success_rate, avg_time_per_page,
                offers_total, offers_new, offers_duplicates, offers_per_second,
                validation_rate_avg, validation_rate_min, validation_rate_max,
                errors_count, warnings_count,
                incremental_mode, query
            ) VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?
            )
        """

        values = (
            metrics_report.get('start_time'),
            metrics_report.get('end_time'),
            metrics_report.get('total_time_seconds'),
            metrics_report.get('pages_scraped'),
            metrics_report.get('pages_failed'),
            metrics_report.get('pages_total'),
            metrics_report.get('success_rate'),
            metrics_report.get('avg_time_per_page'),
            metrics_report.get('offers_total'),
            metrics_report.get('offers_new'),
            metrics_report.get('offers_duplicates'),
            metrics_report.get('offers_per_second'),
            metrics_report.get('validation_rate_avg'),
            metrics_report.get('validation_rate_min'),
            metrics_report.get('validation_rate_max'),
            metrics_report.get('errors_count'),
            metrics_report.get('warnings_count'),
            1,
            None
        )

        try:
            self.cursor.execute(query, values)
            metrica_id = self.cursor.lastrowid
            self.conn.commit()

            # Cerrar sesión v2 si existe
            if self.enable_dual_write and self.current_session_id:
                self.close_scraping_session(
                    ofertas_total=metrics_report.get('offers_total', 0),
                    ofertas_nuevas=metrics_report.get('offers_new', 0),
                    status='completed'
                )

            logger.info(f"Métricas guardadas con ID: {metrica_id}")
            return metrica_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando métricas: {e}")
            raise

    def insert_alertas(self, alertas: List[Dict], metrica_id: int) -> int:
        """Inserta alertas (legacy API)"""
        if not alertas:
            logger.debug("No hay alertas para insertar")
            return 0

        logger.info(f"Insertando {len(alertas)} alertas...")

        query = """
            INSERT INTO alertas (
                metrica_id, timestamp, level, type, message, context
            ) VALUES (?, ?, ?, ?, ?, ?)
        """

        values = []
        for alert in alertas:
            context = alert.get('context', {})
            context_json = json.dumps(context) if context else None

            values.append((
                metrica_id,
                alert.get('timestamp'),
                alert.get('level'),
                alert.get('type', 'general'),
                alert.get('message'),
                context_json
            ))

        try:
            self.cursor.executemany(query, values)
            self.conn.commit()
            logger.info(f"{len(alertas)} alertas insertadas")
            return len(alertas)

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando alertas: {e}")
            raise

    def insert_circuit_breaker_stats(self, stats: Dict, metrica_id: int):
        """Inserta stats circuit breaker (legacy API)"""
        logger.debug("Insertando stats de circuit breaker...")

        query = """
            INSERT INTO circuit_breaker_stats (
                metrica_id, state, consecutive_failures, consecutive_successes,
                total_calls, total_successes, total_failures, total_rejected,
                success_rate, times_opened, time_in_state_seconds
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?
            )
        """

        values = (
            metrica_id,
            stats.get('state'),
            stats.get('consecutive_failures'),
            stats.get('consecutive_successes'),
            stats.get('total_calls'),
            stats.get('total_successes'),
            stats.get('total_failures'),
            stats.get('total_rejected'),
            stats.get('success_rate'),
            stats.get('times_opened'),
            stats.get('time_in_state_seconds')
        )

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug("Circuit breaker stats guardados")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando circuit breaker stats: {e}")
            raise

    def insert_rate_limiter_stats(self, stats: Dict, metrica_id: int):
        """Inserta stats rate limiter (legacy API)"""
        logger.debug("Insertando stats de rate limiter...")

        query = """
            INSERT INTO rate_limiter_stats (
                metrica_id, current_delay, min_delay, max_delay,
                total_requests, total_success, total_errors, total_rate_limits,
                success_rate, consecutive_success, consecutive_errors,
                delay_history
            ) VALUES (
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?
            )
        """

        delay_history = stats.get('delay_history', [])
        delay_history_json = json.dumps(delay_history) if delay_history else None

        values = (
            metrica_id,
            stats.get('current_delay'),
            stats.get('min_delay'),
            stats.get('max_delay'),
            stats.get('total_requests'),
            stats.get('total_success'),
            stats.get('total_errors'),
            stats.get('total_rate_limits'),
            stats.get('success_rate'),
            stats.get('consecutive_success'),
            stats.get('consecutive_errors'),
            delay_history_json
        )

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.debug("Rate limiter stats guardados")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando rate limiter stats: {e}")
            raise

    def get_ultimas_metricas(self, limit: int = 10) -> pd.DataFrame:
        """Obtiene últimas métricas (legacy API)"""
        query = """
            SELECT * FROM v_ultimas_ejecuciones
            ORDER BY start_time DESC
            LIMIT ?
        """

        try:
            return pd.read_sql_query(query, self.conn, params=(limit,))
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
            return pd.DataFrame()

    def get_alertas_recientes(self, limit: int = 50) -> pd.DataFrame:
        """Obtiene alertas recientes (legacy API)"""
        query = """
            SELECT * FROM v_alertas_criticas
            ORDER BY timestamp DESC
            LIMIT ?
        """

        try:
            return pd.read_sql_query(query, self.conn, params=(limit,))
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {e}")
            return pd.DataFrame()

    def get_ofertas_count(self) -> int:
        """Obtiene total de ofertas en v1 (legacy API)"""
        query = "SELECT COUNT(*) FROM ofertas"

        try:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error contando ofertas: {e}")
            return 0


# Mantener alias para compatibilidad
DatabaseManager = DatabaseManagerV2


if __name__ == "__main__":
    """Prueba de dual-write"""
    print(__doc__)
    print()

    logging.basicConfig(level=logging.INFO)

    print("Probando DatabaseManagerV2 con dual-write...")
    print()

    with DatabaseManagerV2(db_path='database/bumeran_scraping.db', enable_dual_write=True) as db:
        # Test: contar ofertas
        count_v1 = db.get_ofertas_count()
        print(f"Total ofertas en v1: {count_v1:,}")

        # Test: crear sesión
        session_id, session_uuid = db.create_scraping_session(
            source='bumeran',
            mode='test',
            metadata={'test': True}
        )
        print(f"Sesión v2 creada: {session_id} ({session_uuid})")

        # Test: cerrar sesión
        db.close_scraping_session(ofertas_total=0, ofertas_nuevas=0, status='test_completed')
        print("Sesión v2 cerrada")
