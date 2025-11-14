"""
Database Manager para Bumeran Scraping - SQLite
================================================

Gestiona inserción y consulta de datos en SQLite:
- Ofertas scrapeadas
- Métricas de scraping
- Alertas
- Stats de circuit breaker y rate limiter

Uso:
    from database.db_manager import DatabaseManager

    db = DatabaseManager(db_path='bumeran_scraping.db')

    # Insertar ofertas
    db.insert_ofertas(ofertas_df)

    # Guardar métricas
    metrica_id = db.insert_metricas(metrics_report)

    # Guardar alertas
    db.insert_alertas(alertas, metrica_id)
"""

import sqlite3
import pandas as pd
import json
from typing import List, Dict, Optional
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Importar DatabaseManagerV2 para dual-write
try:
    from database.db_manager_v2 import DatabaseManagerV2
    DUAL_WRITE_AVAILABLE = True
except ImportError:
    logger.warning("DatabaseManagerV2 no disponible, dual-write deshabilitado")
    DUAL_WRITE_AVAILABLE = False


class DatabaseManager:
    """Gestiona conexión y operaciones con SQLite"""

    def __init__(self, db_path: str = 'database/bumeran_scraping.db', enable_dual_write: bool = True):
        """
        Inicializa conexión a SQLite

        Args:
            db_path: Ruta al archivo de base de datos SQLite
            enable_dual_write: Habilitar escritura en schema v2 (default: True)
        """
        self.db_path = Path(db_path)

        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = None
        self.cursor = None

        # Inicializar DatabaseManagerV2 para dual-write
        self.db_v2 = None
        self.enable_dual_write = enable_dual_write and DUAL_WRITE_AVAILABLE

        if self.enable_dual_write:
            try:
                self.db_v2 = DatabaseManagerV2(
                    db_path=str(db_path),
                    enable_dual_write=True
                )
                logger.info(f"DatabaseManager inicializado con DUAL-WRITE habilitado")
            except Exception as e:
                logger.warning(f"No se pudo inicializar DatabaseManagerV2: {e}")
                self.db_v2 = None
                self.enable_dual_write = False

        logger.info(f"DatabaseManager inicializado para {self.db_path}")

    def connect(self):
        """Establece conexión con SQLite"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()

            # Habilitar foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")

            logger.info(f"Conexión establecida con SQLite: {self.db_path}")

            # Conectar db_v2 si dual-write está habilitado
            if self.enable_dual_write and self.db_v2:
                try:
                    self.db_v2.connect()
                    logger.info("Conexión v2 establecida para dual-write")
                except Exception as e:
                    logger.warning(f"Error conectando db_v2: {e}")

            return True
        except Exception as e:
            logger.error(f"Error conectando a SQLite: {e}")
            return False

    def disconnect(self):
        """Cierra conexión con SQLite"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

        # Desconectar db_v2 si dual-write está habilitado
        if self.enable_dual_write and self.db_v2:
            try:
                self.db_v2.disconnect()
                logger.info("Conexión v2 cerrada")
            except Exception as e:
                logger.warning(f"Error cerrando db_v2: {e}")

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

    def insert_ofertas(self, ofertas: pd.DataFrame) -> int:
        """
        Inserta ofertas en la base de datos (upsert)

        Args:
            ofertas: DataFrame con ofertas procesadas

        Returns:
            Número de ofertas insertadas/actualizadas
        """
        if ofertas.empty:
            logger.warning("DataFrame vacío, no hay ofertas para insertar")
            return 0

        logger.info(f"Insertando {len(ofertas)} ofertas...")

        # Mapeo de columnas DataFrame → SQLite
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

        # ============================================================
        # VALIDACIÓN DE CALIDAD DE DATOS (Agregado 2025-11-03)
        # ============================================================
        # Validar que las ofertas tengan campos críticos completos ANTES de insertar
        ofertas_validadas = []
        ofertas_rechazadas = 0

        logger.debug(f"Validando {len(ofertas)} ofertas antes de inserción...")

        for idx, row in ofertas.iterrows():
            # Verificar campos críticos
            campos_criticos_vacios = []

            # titulo
            if 'titulo' not in ofertas.columns or pd.isna(row.get('titulo')) or str(row.get('titulo')).strip() == '':
                campos_criticos_vacios.append('titulo')

            # descripcion
            if 'descripcion' not in ofertas.columns or pd.isna(row.get('descripcion')) or str(row.get('descripcion')).strip() == '':
                campos_criticos_vacios.append('descripcion')

            # empresa
            if 'empresa' not in ofertas.columns or pd.isna(row.get('empresa')) or str(row.get('empresa')).strip() == '':
                campos_criticos_vacios.append('empresa')

            # modalidad_trabajo
            if 'modalidad_trabajo' not in ofertas.columns or pd.isna(row.get('modalidad_trabajo')):
                campos_criticos_vacios.append('modalidad_trabajo')

            # tipo_trabajo
            if 'tipo_trabajo' not in ofertas.columns or pd.isna(row.get('tipo_trabajo')):
                campos_criticos_vacios.append('tipo_trabajo')

            # id_empresa
            if 'id_empresa' not in ofertas.columns or pd.isna(row.get('id_empresa')):
                campos_criticos_vacios.append('id_empresa')

            # Rechazar si faltan campos críticos
            if campos_criticos_vacios:
                ofertas_rechazadas += 1
                id_oferta = row.get('id_oferta', 'DESCONOCIDO')
                logger.warning(
                    f"⚠️ Oferta {id_oferta} RECHAZADA en insert_ofertas() - "
                    f"Campos críticos vacíos: {', '.join(campos_criticos_vacios)}"
                )
                continue  # Skip esta oferta

            # Si pasa validación, agregar a lista de validadas
            ofertas_validadas.append(row)

        # Estadísticas de validación
        if ofertas_rechazadas > 0:
            logger.warning(
                f"⚠️ {ofertas_rechazadas} de {len(ofertas)} ofertas RECHAZADAS "
                f"en insert_ofertas() por falta de campos críticos ({ofertas_rechazadas/len(ofertas)*100:.1f}%)"
            )

        if not ofertas_validadas:
            logger.error("❌ TODAS las ofertas fueron rechazadas por validación. No se insertará nada.")
            return 0

        logger.info(
            f"✓ {len(ofertas_validadas)} de {len(ofertas)} ofertas pasaron validación "
            f"({len(ofertas_validadas)/len(ofertas)*100:.1f}%)"
        )

        # Reconstruir DataFrame solo con ofertas validadas
        ofertas = pd.DataFrame(ofertas_validadas)
        logger.debug(f"Insertando {len(ofertas)} ofertas validadas...")

        # ============================================================
        # PREPARAR DATOS PARA INSERCIÓN
        # ============================================================
        columns = list(column_mapping.values())
        values = []

        for _, row in ofertas.iterrows():
            row_values = []
            for df_col in column_mapping.keys():
                if df_col in ofertas.columns:
                    val = row[df_col]
                    # Convertir NaN a None
                    if pd.isna(val):
                        row_values.append(None)
                    # Convertir bool a int para SQLite
                    elif isinstance(val, bool):
                        row_values.append(1 if val else 0)
                    else:
                        row_values.append(val)
                else:
                    row_values.append(None)

            values.append(tuple(row_values))

        # Query de INSERT OR REPLACE (upsert en SQLite)
        placeholders = ','.join(['?'] * len(columns))
        query = f"""
            INSERT OR REPLACE INTO ofertas ({','.join(columns)})
            VALUES ({placeholders})
        """

        # Debug logging
        logger.debug(f"Columns ({len(columns)}): {columns[:5]}...")
        logger.debug(f"Values rows: {len(values)}")
        if values:
            logger.debug(f"First value row length: {len(values[0])}")
            logger.debug(f"First 3 values: {values[0][:3]}")

        try:
            logger.debug(f"Executing INSERT OR REPLACE for {len(values)} rows...")
            self.cursor.executemany(query, values)
            rows_affected = self.cursor.rowcount
            logger.debug(f"Rows affected by executemany: {rows_affected}")

            # Commit transaction
            self.conn.commit()
            logger.debug("Commit completed")

            # Verify count immediately after commit
            self.cursor.execute("SELECT COUNT(*) FROM ofertas")
            count_after = self.cursor.fetchone()[0]
            logger.debug(f"Count after commit: {count_after}")

            # DUAL-WRITE: Escribir también en schema v2
            if self.enable_dual_write and self.db_v2:
                try:
                    logger.info(f"[DUAL-WRITE] Escribiendo {len(ofertas)} ofertas en schema v2...")
                    self.db_v2.insert_ofertas_raw(ofertas)
                    logger.info(f"[DUAL-WRITE] OK - {len(ofertas)} ofertas escritas en v2")
                except Exception as e:
                    # ERROR en v2 no es fatal (solo WARNING)
                    logger.warning(f"[DUAL-WRITE] ERROR escribiendo en v2: {e}")
                    logger.warning("[DUAL-WRITE] v1 OK, v2 falló (continuando...)")

            logger.info(f"[OK] {len(ofertas)} ofertas insertadas/actualizadas")
            return len(ofertas)

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando ofertas: {e}")
            raise

    def insert_metricas(self, metrics_report: Dict) -> int:
        """
        Inserta métricas de scraping

        Args:
            metrics_report: Dict con métricas de ScrapingMetrics.get_report()

        Returns:
            ID de la métrica insertada
        """
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
            1,  # incremental_mode (1=True, ajustar si es necesario)
            None   # query (ajustar si se usó búsqueda)
        )

        try:
            self.cursor.execute(query, values)
            metrica_id = self.cursor.lastrowid
            self.conn.commit()
            logger.info(f"✓ Métricas guardadas con ID: {metrica_id}")
            return metrica_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando métricas: {e}")
            raise

    def insert_alertas(self, alertas: List[Dict], metrica_id: int) -> int:
        """
        Inserta alertas

        Args:
            alertas: Lista de alertas de AlertManager.alerts
            metrica_id: ID de la métrica asociada

        Returns:
            Número de alertas insertadas
        """
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
            # Convertir context a JSON string
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
            logger.info(f"✓ {len(alertas)} alertas insertadas")
            return len(alertas)

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando alertas: {e}")
            raise

    def insert_circuit_breaker_stats(self, stats: Dict, metrica_id: int):
        """Inserta estadísticas del circuit breaker"""
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
            logger.debug("✓ Circuit breaker stats guardados")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando circuit breaker stats: {e}")
            raise

    def insert_rate_limiter_stats(self, stats: Dict, metrica_id: int):
        """Inserta estadísticas del rate limiter"""
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

        # Convertir delay_history array a JSON string
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
            logger.debug("✓ Rate limiter stats guardados")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error insertando rate limiter stats: {e}")
            raise

    def get_ultimas_metricas(self, limit: int = 10) -> pd.DataFrame:
        """
        Obtiene las últimas N métricas de scraping

        Args:
            limit: Número de métricas a obtener

        Returns:
            DataFrame con métricas
        """
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
        """Obtiene alertas recientes"""
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
        """Obtiene total de ofertas en DB"""
        query = "SELECT COUNT(*) FROM ofertas"

        try:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error contando ofertas: {e}")
            return 0


if __name__ == "__main__":
    """Ejemplo de uso"""
    print(__doc__)
    print()

    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Ejemplo de conexión
    print("Probando conexión a SQLite...")

    with DatabaseManager(db_path='database/bumeran_scraping.db') as db:
        # Probar consulta
        count = db.get_ofertas_count()
        print(f"Total ofertas en DB: {count:,}")

        # Últimas métricas
        df_metricas = db.get_ultimas_metricas(limit=5)
        print(f"\nÚltimas {len(df_metricas)} ejecuciones:")
        if not df_metricas.empty:
            print(df_metricas[['start_time', 'offers_total', 'success_rate']])
