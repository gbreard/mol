"""
Sistema de Tracking Incremental de IDs
======================================

Mantiene registro de ofertas ya scrapeadas por fuente para evitar duplicados
entre ejecuciones del pipeline.

Uso:
    tracker = IncrementalTracker(source='bumeran')

    # Cargar IDs existentes
    existing_ids = tracker.load_scraped_ids()

    # Filtrar solo IDs nuevos
    new_offers = [o for o in offers if o['id'] not in existing_ids]

    # Actualizar tracking
    new_ids = {o['id'] for o in new_offers}
    tracker.save_scraped_ids(new_ids)
"""

import json
import shutil
from pathlib import Path
from typing import Set, List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncrementalTracker:
    """Gestiona el tracking de IDs scrapeados por fuente"""

    def __init__(self, source: str, tracking_dir: Optional[Path] = None):
        """
        Inicializa el tracker para una fuente específica

        Args:
            source: Nombre de la fuente (zonajobs, bumeran, computrabajo, etc.)
            tracking_dir: Directorio donde guardar archivos de tracking
        """
        self.source = source

        # Directorio de tracking
        if tracking_dir is None:
            project_root = Path(__file__).parent.parent.parent
            self.tracking_dir = project_root / "data" / "tracking"
        else:
            self.tracking_dir = tracking_dir

        # Crear directorio si no existe
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        # Archivo de tracking para esta fuente
        self.tracking_file = self.tracking_dir / f"{source}_scraped_ids.json"

        logger.info(f"IncrementalTracker inicializado para '{source}'")
        logger.info(f"  Archivo de tracking: {self.tracking_file}")

    def load_scraped_ids(self) -> Set[str]:
        """
        Carga el conjunto de IDs ya scrapeados

        Returns:
            Set de IDs (strings) ya scrapeados
        """
        if not self.tracking_file.exists():
            logger.info(f"  No existe archivo de tracking para {self.source}")
            logger.info(f"  Primera ejecución: se scrapeará TODO")
            return set()

        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            scraped_ids_data = data.get('scraped_ids', [])

            # Detectar formato: lista (v1.0) o dict con timestamps (v2.0)
            if isinstance(scraped_ids_data, list):
                # Formato viejo: lista simple
                ids = set(scraped_ids_data)
                logger.debug(f"  Formato v1.0 detectado (lista simple)")
            elif isinstance(scraped_ids_data, dict):
                # Formato nuevo: dict con timestamps
                ids = set(scraped_ids_data.keys())
                logger.debug(f"  Formato v2.0 detectado (con timestamps)")
            else:
                logger.warning(f"  Formato de scraped_ids desconocido: {type(scraped_ids_data)}")
                ids = set()

            last_update = data.get('last_update', 'unknown')
            total_ids = len(ids)

            logger.info(f"  IDs cargados: {total_ids:,}")
            logger.info(f"  Última actualización: {last_update}")

            return ids

        except Exception as e:
            logger.error(f"  Error cargando tracking de {self.source}: {e}")
            logger.warning(f"  Se creará nuevo archivo de tracking")
            return set()

    def save_scraped_ids(self, ids: Set[str], mode: str = 'replace'):
        """
        Guarda IDs scrapeados usando operaciones atómicas con timestamps

        Args:
            ids: Set de IDs a guardar
            mode: 'replace' (reemplazar) o 'merge' (combinar con existentes)
        """
        now = datetime.now().isoformat()
        ids_with_timestamps = {}

        if mode == 'merge' and self.tracking_file.exists():
            # Cargar timestamps existentes
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_scraped = existing_data.get('scraped_ids', {})

                    # Convertir formato viejo a nuevo si es necesario
                    if isinstance(existing_scraped, list):
                        # Formato v1.0: asignar timestamp actual a todos
                        ids_with_timestamps = {id_: now for id_ in existing_scraped}
                    elif isinstance(existing_scraped, dict):
                        # Formato v2.0: preservar timestamps existentes
                        ids_with_timestamps = existing_scraped.copy()
            except Exception as e:
                logger.warning(f"  No se pudieron cargar timestamps existentes: {e}")

        # Agregar nuevos IDs con timestamp actual
        for id_ in ids:
            if id_ not in ids_with_timestamps:
                ids_with_timestamps[id_] = now

        data = {
            'source': self.source,
            'scraped_ids': ids_with_timestamps,  # Nuevo formato: dict con timestamps
            'total_ids': len(ids_with_timestamps),
            'last_update': now,
            'metadata': {
                'created': datetime.now().isoformat() if not self.tracking_file.exists() else None,
                'mode': mode,
                'version': '2.0',  # Versión con operaciones atómicas + timestamps
                'format': 'dict_with_timestamps'
            }
        }

        # PASO 1: Escribir a archivo temporal primero
        temp_file = self.tracking_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # PASO 2: Validar que se escribió correctamente
            with open(temp_file, 'r', encoding='utf-8') as f:
                validated_data = json.load(f)
                assert validated_data['total_ids'] == len(ids), "Validación falló: count mismatch"

            logger.debug(f"  Archivo temporal validado: {temp_file.name}")

        except Exception as e:
            # Si falla la escritura/validación, eliminar temporal y abortar
            if temp_file.exists():
                temp_file.unlink()
            logger.error(f"  Error escribiendo archivo temporal: {e}")
            raise RuntimeError(f"No se pudo guardar tracking de forma segura: {e}")

        # PASO 3: Crear backup del original (COPIA, no mover)
        if self.tracking_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.tracking_file.with_suffix(f'.json.bak_{timestamp}')
            try:
                shutil.copy2(self.tracking_file, backup_file)  # COPIA en vez de rename
                logger.debug(f"  Backup creado: {backup_file.name}")
            except Exception as e:
                logger.warning(f"  No se pudo crear backup: {e}")
                # Continuar de todas formas (no es crítico)

        # PASO 4: Reemplazar original con temporal (operación atómica en POSIX)
        try:
            temp_file.replace(self.tracking_file)  # Atómico en sistemas POSIX
            logger.info(f"  [OK] Tracking actualizado: {len(ids):,} IDs guardados")
        except Exception as e:
            logger.error(f"  Error reemplazando archivo: {e}")
            # Intentar recuperar desde backup
            self._recover_from_backup()
            raise RuntimeError(f"Error crítico guardando tracking: {e}")

    def merge_scraped_ids(self, new_ids: Set[str]) -> Set[str]:
        """
        Combina IDs nuevos con existentes y guarda

        Args:
            new_ids: Set de IDs nuevos a agregar

        Returns:
            Set de IDs que son realmente nuevos (no existían antes)
        """
        existing_ids = self.load_scraped_ids()
        truly_new_ids = new_ids - existing_ids

        if truly_new_ids:
            all_ids = existing_ids.union(new_ids)
            self.save_scraped_ids(all_ids, mode='merge')
            logger.info(f"  [OK] {len(truly_new_ids):,} IDs nuevos agregados")
        else:
            logger.info(f"  No hay IDs nuevos para agregar")

        return truly_new_ids

    def filter_new_offers(
        self,
        offers: List[Dict],
        id_field: str = 'id_oferta'
    ) -> List[Dict]:
        """
        Filtra solo las ofertas con IDs nuevos (no scrapeados antes)

        Args:
            offers: Lista de ofertas (dicts)
            id_field: Campo que contiene el ID de la oferta

        Returns:
            Lista de ofertas con IDs nuevos
        """
        existing_ids = self.load_scraped_ids()

        new_offers = [
            offer for offer in offers
            if str(offer.get(id_field, '')) not in existing_ids
        ]

        total = len(offers)
        new = len(new_offers)
        existing = total - new

        logger.info(f"  Filtrado de ofertas:")
        logger.info(f"    Total scrapeadas: {total:,}")
        logger.info(f"    Ya existentes: {existing:,}")
        logger.info(f"    Nuevas: {new:,}")

        return new_offers

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del tracking

        Returns:
            Dict con estadísticas
        """
        if not self.tracking_file.exists():
            return {
                'source': self.source,
                'exists': False,
                'total_ids': 0
            }

        with open(self.tracking_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            'source': self.source,
            'exists': True,
            'total_ids': data.get('total_ids', 0),
            'last_update': data.get('last_update', 'unknown'),
            'file_path': str(self.tracking_file)
        }

    def get_old_ids(self, days_threshold: int = 30) -> Set[str]:
        """
        Obtiene IDs de ofertas scrapeadas hace más de N días

        Args:
            days_threshold: Número de días para considerar ID como antiguo

        Returns:
            Set de IDs antiguos que deberían ser re-scrapeados
        """
        if not self.tracking_file.exists():
            return set()

        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            scraped_ids_data = data.get('scraped_ids', {})

            # Solo funciona con formato v2.0 (dict con timestamps)
            if not isinstance(scraped_ids_data, dict):
                logger.warning(f"  get_old_ids() requiere formato v2.0 con timestamps")
                return set()

            # Calcular fecha límite
            from datetime import timedelta
            now = datetime.now()
            threshold_date = now - timedelta(days=days_threshold)

            old_ids = set()
            for id_, timestamp_str in scraped_ids_data.items():
                try:
                    scraped_date = datetime.fromisoformat(timestamp_str)
                    if scraped_date < threshold_date:
                        old_ids.add(id_)
                except Exception as e:
                    logger.debug(f"  Error parseando timestamp para {id_}: {e}")
                    continue

            logger.info(f"  IDs antiguos (>{days_threshold} días): {len(old_ids):,}")
            return old_ids

        except Exception as e:
            logger.error(f"  Error obteniendo IDs antiguos: {e}")
            return set()

    def _recover_from_backup(self) -> bool:
        """
        Intenta recuperar el archivo de tracking desde el backup más reciente

        Returns:
            True si la recuperación fue exitosa, False si no
        """
        logger.warning(f"  Intentando recuperar tracking desde backup...")

        # Buscar todos los backups disponibles
        backup_pattern = f"{self.source}_scraped_ids.json.bak_*"
        backups = sorted(
            self.tracking_dir.glob(backup_pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True  # Más reciente primero
        )

        if not backups:
            logger.error(f"  No se encontraron backups para {self.source}")
            return False

        # Intentar restaurar desde el backup más reciente
        for backup_file in backups:
            try:
                logger.info(f"  Intentando con backup: {backup_file.name}")

                # Validar que el backup es un JSON válido
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Si es válido, copiarlo como archivo principal
                shutil.copy2(backup_file, self.tracking_file)
                logger.info(f"  [OK] Recuperado desde backup: {backup_file.name}")
                logger.info(f"  IDs recuperados: {data.get('total_ids', 0):,}")
                return True

            except Exception as e:
                logger.warning(f"  Backup corrupto {backup_file.name}: {e}")
                continue

        logger.error(f"  No se pudo recuperar tracking desde ningún backup")
        return False


def get_all_tracking_stats(tracking_dir: Optional[Path] = None) -> List[Dict]:
    """
    Obtiene estadísticas de tracking para todas las fuentes

    Args:
        tracking_dir: Directorio de tracking (opcional)

    Returns:
        Lista de dicts con estadísticas por fuente
    """
    if tracking_dir is None:
        project_root = Path(__file__).parent.parent.parent
        tracking_dir = project_root / "data" / "tracking"

    if not tracking_dir.exists():
        return []

    stats = []
    for tracking_file in tracking_dir.glob("*_scraped_ids.json"):
        source = tracking_file.stem.replace('_scraped_ids', '')
        tracker = IncrementalTracker(source, tracking_dir)
        stats.append(tracker.get_stats())

    return stats


# ===== FUNCIONES DE UTILIDAD =====

def reset_tracking(source: str, tracking_dir: Optional[Path] = None):
    """
    Resetea el tracking de una fuente (elimina archivo)

    Args:
        source: Nombre de la fuente
        tracking_dir: Directorio de tracking (opcional)
    """
    tracker = IncrementalTracker(source, tracking_dir)

    if tracker.tracking_file.exists():
        # Crear backup antes de eliminar
        backup_file = tracker.tracking_file.with_suffix(
            f'.json.reset_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        tracker.tracking_file.rename(backup_file)
        logger.info(f"[OK] Tracking reseteado para {source}")
        logger.info(f"  Backup guardado: {backup_file.name}")
    else:
        logger.info(f"No hay tracking para resetear en {source}")


def print_tracking_summary():
    """Imprime resumen de tracking de todas las fuentes"""
    print("="*70)
    print("RESUMEN DE TRACKING INCREMENTAL")
    print("="*70)
    print()

    stats = get_all_tracking_stats()

    if not stats:
        print("No hay archivos de tracking disponibles")
        print()
        return

    for stat in stats:
        print(f"Fuente: {stat['source']}")
        if stat['exists']:
            print(f"  IDs scrapeados: {stat['total_ids']:,}")
            print(f"  Última actualización: {stat['last_update']}")
        else:
            print(f"  Estado: Sin tracking (primera ejecución)")
        print()

    total_ids = sum(s['total_ids'] for s in stats if s['exists'])
    print(f"TOTAL de IDs únicos tracked: {total_ids:,}")
    print("="*70)


if __name__ == "__main__":
    # Ejemplo de uso
    print(__doc__)
    print()
    print_tracking_summary()
