"""
Configuración de Base de Datos
================================

Define configuración para SQLite.

Uso:
    from database.config import DB_CONFIG

    db = DatabaseManager(**DB_CONFIG)
"""

import os
from pathlib import Path

# =====================================================================
# CONFIGURACIÓN DE SQLITE
# =====================================================================

DB_CONFIG = {
    'db_path': os.getenv('DB_PATH', 'database/bumeran_scraping.db'),
    'enable_dual_write': True,  # Habilita escritura simultanea en schema v1 y v2
}

# =====================================================================
# CONFIGURACIÓN DE DIRECTORIOS
# =====================================================================

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent

# Directorios de datos
DATA_DIR = PROJECT_ROOT / "data"
TRACKING_DIR = DATA_DIR / "tracking"
RAW_DATA_DIR = PROJECT_ROOT / "01_sources" / "bumeran" / "data" / "raw"
METRICS_DIR = PROJECT_ROOT / "01_sources" / "bumeran" / "data" / "metrics"

# Crear directorios si no existen
for dir_path in [DATA_DIR, TRACKING_DIR, RAW_DATA_DIR, METRICS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =====================================================================
# CONFIGURACIÓN DE SCHEDULER
# =====================================================================

SCHEDULER_CONFIG = {
    # Días de la semana (0 = lunes, 6 = domingo)
    'days_of_week': [0, 3],  # Lunes y Jueves

    # Hora de ejecución (formato 24h)
    'hour': 8,
    'minute': 0,

    # Timezone
    'timezone': 'America/Argentina/Buenos_Aires',
}

# =====================================================================
# CONFIGURACIÓN DE SCRAPING
# =====================================================================

SCRAPING_CONFIG = {
    # Delay inicial entre requests
    'initial_delay': 2.0,

    # Rate limiter adaptativo
    'rate_limiter': {
        'min_delay': 0.5,
        'max_delay': 10.0,
        'success_threshold': 5,
        'error_threshold': 3,
    },

    # Circuit breaker
    'circuit_breaker': {
        'max_failures': 5,
        'timeout': 30,  # segundos
    },

    # Modo incremental por defecto
    'incremental': True,

    # Page size
    'page_size': 20,
}

# =====================================================================
# CONFIGURACIÓN DE ALERTAS
# =====================================================================

ALERTS_CONFIG = {
    # Email (futuro)
    'email_enabled': False,
    'email_to': os.getenv('ALERT_EMAIL', ''),

    # Consola
    'console_output': True,

    # Slack (futuro)
    'slack_webhook': os.getenv('SLACK_WEBHOOK', ''),
}


# =====================================================================
# FUNCIONES ÚTILES
# =====================================================================

def validate_config() -> bool:
    """
    Valida que la configuración esté completa

    Returns:
        True si configuración válida

    Raises:
        ValueError si falta configuración crítica
    """
    errors = []

    # Validar DB path
    if not DB_CONFIG['db_path']:
        errors.append("DB_PATH no configurado")

    if errors:
        raise ValueError(
            "Configuración incompleta:\n  " + "\n  ".join(errors) +
            "\n\nConfigurar en database/config.py o variables de entorno"
        )

    return True


def print_config():
    """Imprime configuración actual"""
    print("="*70)
    print("CONFIGURACIÓN ACTUAL")
    print("="*70)
    print()
    print("BASE DE DATOS (SQLite):")
    print(f"  DB Path:  {DB_CONFIG['db_path']}")
    db_path = Path(DB_CONFIG['db_path'])
    print(f"  Existe:   {'Sí' if db_path.exists() else 'No (se creará automáticamente)'}")
    if db_path.exists():
        print(f"  Tamaño:   {db_path.stat().st_size / 1024:.2f} KB")
    print()
    print("SCHEDULER:")
    print(f"  Días:     {', '.join(['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'][d] for d in SCHEDULER_CONFIG['days_of_week'])}")
    print(f"  Hora:     {SCHEDULER_CONFIG['hour']:02d}:{SCHEDULER_CONFIG['minute']:02d}")
    print(f"  Timezone: {SCHEDULER_CONFIG['timezone']}")
    print()
    print("SCRAPING:")
    print(f"  Delay inicial:        {SCRAPING_CONFIG['initial_delay']}s")
    print(f"  Rate limiter min/max: {SCRAPING_CONFIG['rate_limiter']['min_delay']}s - {SCRAPING_CONFIG['rate_limiter']['max_delay']}s")
    print(f"  Circuit breaker:      max {SCRAPING_CONFIG['circuit_breaker']['max_failures']} fallos, timeout {SCRAPING_CONFIG['circuit_breaker']['timeout']}s")
    print(f"  Modo incremental:     {SCRAPING_CONFIG['incremental']}")
    print()
    print("ALERTAS:")
    print(f"  Email:    {'Habilitado' if ALERTS_CONFIG['email_enabled'] else 'Deshabilitado'}")
    print(f"  Consola:  {'Habilitado' if ALERTS_CONFIG['console_output'] else 'Deshabilitado'}")
    print("="*70)


if __name__ == "__main__":
    """Muestra configuración actual"""
    print(__doc__)
    print()

    try:
        print_config()
        print()
        validate_config()
        print("✓ Configuración válida")
    except ValueError as e:
        print(f"\n✗ Error en configuración:\n{e}")
