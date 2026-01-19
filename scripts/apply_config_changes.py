#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Config Changes v1.0 - Aplicar cambios de config recomendados
===================================================================

Aplica cambios a archivos de configuración basados en las recomendaciones
generadas durante el proceso de revisión.

Características:
- Backup automático antes de modificar
- Validación de JSON syntax
- Merge inteligente de reglas (no sobrescribe, agrega)
- Rollback si algo falla

Uso:
    # Aplicar cambios desde archivo de recomendaciones
    python scripts/apply_config_changes.py --input exports/review_recommendations.json

    # Ver qué cambios se aplicarían (dry-run)
    python scripts/apply_config_changes.py --input exports/review_recommendations.json --dry-run

    # Aplicar una regla específica manualmente
    python scripts/apply_config_changes.py --add-rule matching_rules_business.json R_GERENTE_VENTAS '{"titulo_contiene_alguno": ["gerente"], "forzar_isco": "1221"}'

    # Ver reglas actuales
    python scripts/apply_config_changes.py --list-rules matching_rules_business.json

    # Rollback (restaurar backup)
    python scripts/apply_config_changes.py --rollback config/matching_rules_business.json
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Paths
BASE = Path(__file__).parent.parent
CONFIG_DIR = BASE / "config"
BACKUPS_DIR = BASE / "config" / "backups"


def backup_config(config_path: Path) -> Path:
    """
    Crea backup de un archivo de configuración.

    Args:
        config_path: Path al archivo de config

    Returns:
        Path al archivo de backup
    """
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{config_path.stem}_{timestamp}{config_path.suffix}"
    backup_path = BACKUPS_DIR / backup_name

    shutil.copy2(config_path, backup_path)
    print(f"[BACKUP] {config_path.name} -> {backup_path}")

    return backup_path


def load_config(config_name: str) -> Tuple[Dict, Path]:
    """
    Carga un archivo de configuración.

    Args:
        config_name: Nombre del archivo (e.g., "matching_rules_business.json")

    Returns:
        Tuple de (contenido dict, path completo)
    """
    # Soportar tanto nombre solo como path completo
    if "/" in config_name or "\\" in config_name:
        config_path = Path(config_name)
        if not config_path.is_absolute():
            config_path = BASE / config_name
    else:
        config_path = CONFIG_DIR / config_name

    if not config_path.exists():
        raise FileNotFoundError(f"Config no encontrado: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data, config_path


def save_config(config_path: Path, data: Dict, backup: bool = True) -> bool:
    """
    Guarda un archivo de configuración.

    Args:
        config_path: Path al archivo
        data: Datos a guardar
        backup: Si hacer backup antes

    Returns:
        True si se guardó correctamente
    """
    if backup and config_path.exists():
        backup_config(config_path)

    # Validar JSON antes de guardar
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        json.loads(json_str)  # Validar que es JSON válido
    except Exception as e:
        print(f"[ERROR] JSON inválido: {e}")
        return False

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(json_str)

    print(f"[OK] Guardado: {config_path}")
    return True


def add_rule(
    config_name: str,
    rule_name: str,
    rule_data: Dict,
    dry_run: bool = False
) -> bool:
    """
    Agrega una regla a un archivo de configuración.

    Args:
        config_name: Nombre del archivo de config
        rule_name: Nombre de la regla (e.g., "R_GERENTE_VENTAS")
        rule_data: Datos de la regla
        dry_run: Si solo mostrar qué se haría

    Returns:
        True si se agregó correctamente
    """
    data, config_path = load_config(config_name)

    # Para matching_rules_business.json, las reglas van en reglas_forzar_isco
    if "reglas_forzar_isco" in data:
        rules_container = data["reglas_forzar_isco"]
    else:
        rules_container = data

    # Verificar si ya existe
    if rule_name in rules_container:
        print(f"[WARN] Regla {rule_name} ya existe en {config_name}")
        print(f"       Existente: {json.dumps(rules_container[rule_name], indent=2)}")
        print(f"       Nueva:     {json.dumps(rule_data, indent=2)}")

        if dry_run:
            print("[DRY-RUN] Se sobrescribiria la regla existente")
            return False

        # En modo real, sobrescribir
        print("[INFO] Sobrescribiendo regla existente...")

    # Agregar regla
    rules_container[rule_name] = rule_data

    if dry_run:
        print(f"[DRY-RUN] Se agregaria regla {rule_name} a {config_name}:")
        print(json.dumps(rule_data, indent=2))
        return True

    return save_config(config_path, data)


def list_rules(config_name: str):
    """Lista reglas en un archivo de configuración."""
    data, config_path = load_config(config_name)

    print(f"\n{'=' * 60}")
    print(f"REGLAS EN: {config_name}")
    print(f"{'=' * 60}")

    # Para matching_rules_business.json, las reglas estan en reglas_forzar_isco
    if "reglas_forzar_isco" in data:
        rules = data["reglas_forzar_isco"]
        print(f"Version: {data.get('version', 'N/A')}")
        print(f"Total reglas: {len([k for k in rules.keys() if k.startswith('R')])}\n")

        for rule_name, rule_data in sorted(rules.items()):
            if not rule_name.startswith('R'):  # Skip metadata
                continue
            if isinstance(rule_data, dict):
                # Estructura nueva con condicion/accion
                if 'accion' in rule_data:
                    isco = rule_data.get('accion', {}).get('forzar_isco', 'N/A')
                    titulo = rule_data.get('condicion', {}).get('titulo_contiene_alguno', [])
                else:
                    # Estructura plana
                    isco = rule_data.get('forzar_isco', 'N/A')
                    titulo = rule_data.get('titulo_contiene_alguno', [])

                if isinstance(titulo, list):
                    titulo = titulo[:3]
                prioridad = rule_data.get('prioridad', 'N/A')
                nombre = rule_data.get('nombre', rule_name)
                activa = rule_data.get('activa', True)

                print(f"  {rule_name}: {nombre}")
                print(f"    -> ISCO: {isco} | Prioridad: {prioridad} | Activa: {activa}")
                if titulo:
                    print(f"    -> titulo_contiene: {titulo}")
    else:
        # Formato genérico
        print(f"Total: {len(data)} items\n")
        for key, value in sorted(data.items()):
            if isinstance(value, dict):
                print(f"  {key}: {list(value.keys())[:3]}...")
            else:
                print(f"  {key}: {str(value)[:50]}...")

    print()


def apply_recommendations(
    recommendations_file: str,
    dry_run: bool = False,
    filter_config: str = None
) -> Dict:
    """
    Aplica recomendaciones desde un archivo JSON.

    El archivo debe tener formato:
    {
        "ofertas": [
            {
                "id_oferta": "123",
                "recomendacion": {
                    "archivo": "config/matching_rules_business.json",
                    "tipo_cambio": "nueva_regla",
                    "regla_sugerida": {
                        "R_NOMBRE": {...}
                    }
                }
            }
        ]
    }

    Args:
        recommendations_file: Path al archivo de recomendaciones
        dry_run: Si solo mostrar qué se haría
        filter_config: Aplicar solo cambios a este config

    Returns:
        Dict con estadísticas de aplicación
    """
    rec_path = Path(recommendations_file)
    if not rec_path.exists():
        raise FileNotFoundError(f"Archivo de recomendaciones no encontrado: {rec_path}")

    with open(rec_path, 'r', encoding='utf-8') as f:
        recommendations = json.load(f)

    # Agrupar por archivo de config
    changes_by_config = {}

    ofertas = recommendations.get("ofertas", recommendations.get("recomendaciones", []))

    for item in ofertas:
        rec = item.get("recomendacion", item)

        archivo = rec.get("archivo", rec.get("config_sugerido"))
        if not archivo:
            continue

        if filter_config and filter_config not in archivo:
            continue

        if archivo not in changes_by_config:
            changes_by_config[archivo] = []

        regla = rec.get("regla_sugerida", rec.get("regla"))
        if regla:
            changes_by_config[archivo].append({
                "id_oferta": item.get("id_oferta"),
                "regla": regla,
                "justificacion": rec.get("justificacion", "")
            })

    # Aplicar cambios
    stats = {"aplicados": 0, "errores": 0, "skipped": 0}

    for config_name, changes in changes_by_config.items():
        print(f"\n{'=' * 60}")
        print(f"PROCESANDO: {config_name}")
        print(f"{'=' * 60}")
        print(f"Cambios a aplicar: {len(changes)}")

        # Cargar config actual
        try:
            data, config_path = load_config(config_name)
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            stats["errores"] += len(changes)
            continue

        # Hacer backup una sola vez
        if not dry_run and changes:
            backup_config(config_path)

        # Aplicar cada cambio
        for change in changes:
            regla = change["regla"]

            for rule_name, rule_data in regla.items():
                if rule_name in data:
                    print(f"[SKIP] {rule_name} ya existe")
                    stats["skipped"] += 1
                else:
                    if dry_run:
                        print(f"[DRY-RUN] Agregaría: {rule_name}")
                        print(f"          Oferta: {change.get('id_oferta')}")
                        print(f"          Justificación: {change.get('justificacion', 'N/A')[:50]}")
                    else:
                        data[rule_name] = rule_data
                        print(f"[ADD] {rule_name}")
                    stats["aplicados"] += 1

        # Guardar config (sin backup, ya lo hicimos)
        if not dry_run and changes:
            save_config(config_path, data, backup=False)

    return stats


def rollback(config_name: str) -> bool:
    """
    Restaura un config desde el backup más reciente.

    Args:
        config_name: Nombre del archivo de config

    Returns:
        True si se restauró correctamente
    """
    # Encontrar backup más reciente
    config_stem = Path(config_name).stem

    backups = list(BACKUPS_DIR.glob(f"{config_stem}_*.json"))
    if not backups:
        print(f"[ERROR] No hay backups para {config_name}")
        return False

    # Ordenar por fecha (más reciente primero)
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_backup = backups[0]

    print(f"[ROLLBACK] Restaurando {config_name} desde {latest_backup.name}")

    # Cargar backup
    with open(latest_backup, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Determinar path destino
    if "/" in config_name or "\\" in config_name:
        config_path = BASE / config_name
    else:
        config_path = CONFIG_DIR / config_name

    # Guardar (sin backup adicional)
    return save_config(config_path, data, backup=False)


def generate_recommendations_from_db() -> Dict:
    """
    Genera archivo de recomendaciones basado en evaluaciones en BD.

    Lee ofertas con diagnóstico y genera JSON de recomendaciones.
    """
    import sqlite3
    from pathlib import Path

    DB_PATH = BASE / "database" / "bumeran_scraping.db"

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Obtener ofertas con diagnóstico
    cur.execute('''
        SELECT id_oferta, notas_revision
        FROM ofertas_esco_matching
        WHERE estado_validacion = 'en_revision'
        AND notas_revision IS NOT NULL
        AND notas_revision != ''
    ''')

    recomendaciones = []

    for row in cur.fetchall():
        try:
            notas = json.loads(row['notas_revision'])

            if notas.get("triage") in ["incorrecto", "sospechoso"]:
                rec = {
                    "id_oferta": row['id_oferta'],
                    "triage": notas.get("triage"),
                    "diagnostico": notas.get("diagnostico"),
                    "config_sugerido": notas.get("config_sugerido"),
                    "recomendacion": notas.get("recomendacion"),
                    "isco_correcto_sugerido": notas.get("isco_correcto_sugerido")
                }
                recomendaciones.append(rec)
        except:
            pass

    conn.close()

    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(recomendaciones),
        "recomendaciones": recomendaciones
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aplicar cambios de configuración recomendados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Aplicar recomendaciones
  python scripts/apply_config_changes.py --input exports/review_recommendations.json

  # Dry-run (ver qué se haría)
  python scripts/apply_config_changes.py --input exports/review_recommendations.json --dry-run

  # Agregar regla manualmente
  python scripts/apply_config_changes.py --add-rule matching_rules_business.json R_TEST '{"forzar_isco": "1234"}'

  # Listar reglas
  python scripts/apply_config_changes.py --list-rules matching_rules_business.json

  # Rollback
  python scripts/apply_config_changes.py --rollback config/matching_rules_business.json

  # Generar recomendaciones desde BD
  python scripts/apply_config_changes.py --generate-from-db
        """
    )

    parser.add_argument('--input', type=str, help='Archivo JSON con recomendaciones')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se haría')
    parser.add_argument('--filter-config', type=str, help='Aplicar solo a este config')
    parser.add_argument('--add-rule', nargs=3, metavar=('CONFIG', 'RULE_NAME', 'RULE_JSON'),
                        help='Agregar regla manualmente')
    parser.add_argument('--list-rules', type=str, metavar='CONFIG', help='Listar reglas de un config')
    parser.add_argument('--rollback', type=str, metavar='CONFIG', help='Restaurar config desde backup')
    parser.add_argument('--generate-from-db', action='store_true',
                        help='Generar archivo de recomendaciones desde BD')
    parser.add_argument('--output', type=str, help='Archivo de salida (para generate-from-db)')

    args = parser.parse_args()

    if args.list_rules:
        list_rules(args.list_rules)
    elif args.rollback:
        rollback(args.rollback)
    elif args.add_rule:
        config_name, rule_name, rule_json = args.add_rule
        try:
            rule_data = json.loads(rule_json)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON inválido: {e}")
            return
        add_rule(config_name, rule_name, rule_data, dry_run=args.dry_run)
    elif args.input:
        stats = apply_recommendations(
            args.input,
            dry_run=args.dry_run,
            filter_config=args.filter_config
        )
        print(f"\n{'=' * 40}")
        print(f"RESUMEN:")
        print(f"  Aplicados: {stats['aplicados']}")
        print(f"  Skipped:   {stats['skipped']}")
        print(f"  Errores:   {stats['errores']}")
        print(f"{'=' * 40}")
    elif args.generate_from_db:
        recommendations = generate_recommendations_from_db()
        output_path = args.output or f"exports/review_recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        output_path = BASE / output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)

        print(f"[OK] Generado: {output_path}")
        print(f"     Total recomendaciones: {recommendations['total']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
