# -*- coding: utf-8 -*-
"""
Ejecutar Migración 003: NLP Schema v5 Completo
=============================================

Agrega 95 columnas a ofertas_nlp para completar el schema v5.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
BACKUP_DIR = PROJECT_ROOT / "backups"
MIGRATION_FILE = Path(__file__).parent / "003_nlp_schema_v5_complete.sql"


def backup_database():
    """Crea backup de la BD antes de migrar."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"bumeran_scraping_{timestamp}_pre_migration_003.db"

    print(f"[1] Creando backup: {backup_path.name}")
    shutil.copy2(DB_PATH, backup_path)

    # Verificar
    original_size = DB_PATH.stat().st_size
    backup_size = backup_path.stat().st_size

    if original_size == backup_size:
        print(f"    OK - Backup creado ({backup_size / 1024 / 1024:.1f} MB)")
        return backup_path
    else:
        raise Exception("Error: Backup incompleto")


def get_existing_columns(conn):
    """Obtiene columnas existentes."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    return {row[1] for row in cursor.fetchall()}


def run_migration(conn, existing_columns):
    """Ejecuta la migración, saltando columnas existentes."""
    cursor = conn.cursor()

    # Leer SQL
    with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Parsear ALTER TABLE statements
    statements = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line.startswith('ALTER TABLE ofertas_nlp ADD COLUMN'):
            statements.append(line)

    print(f"\n[2] Ejecutando migración ({len(statements)} columnas)")
    print("-" * 60)

    added = 0
    skipped = 0
    errors = []

    for stmt in statements:
        # Extraer nombre de columna
        # ALTER TABLE ofertas_nlp ADD COLUMN nombre_columna TYPE;
        parts = stmt.split('ADD COLUMN')[1].strip().split()
        col_name = parts[0]

        if col_name in existing_columns:
            print(f"    [SKIP] {col_name} (ya existe)")
            skipped += 1
            continue

        try:
            cursor.execute(stmt)
            print(f"    [ADD]  {col_name}")
            added += 1
        except sqlite3.Error as e:
            print(f"    [ERR]  {col_name}: {e}")
            errors.append((col_name, str(e)))

    conn.commit()

    return added, skipped, errors


def verify_migration(conn):
    """Verifica columnas después de migración."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    columns = [row[1] for row in cursor.fetchall()]
    return len(columns), columns


def main():
    print("=" * 70)
    print("MIGRACIÓN 003: NLP Schema v5 Completo")
    print("=" * 70)

    # 1. Backup
    backup_path = backup_database()

    # 2. Conectar
    conn = sqlite3.connect(DB_PATH)

    # 3. Columnas existentes
    existing = get_existing_columns(conn)
    print(f"\n    Columnas existentes: {len(existing)}")

    # 4. Ejecutar migración
    added, skipped, errors = run_migration(conn, existing)

    # 5. Verificar
    total, columns = verify_migration(conn)

    conn.close()

    # 6. Resumen
    print("\n" + "=" * 70)
    print("RESUMEN MIGRACIÓN")
    print("=" * 70)
    print(f"  Columnas antes:  {len(existing)}")
    print(f"  Agregadas:       {added}")
    print(f"  Saltadas:        {skipped}")
    print(f"  Errores:         {len(errors)}")
    print(f"  Total después:   {total}")
    print(f"\n  Backup en: {backup_path}")

    if errors:
        print("\n  ERRORES:")
        for col, err in errors:
            print(f"    - {col}: {err}")

    # Listar nuevas columnas por bloque
    bloques = {
        "Empresa": ["empresa_tamanio", "empresa_antiguedad", "rubro_empresa", "cliente_final"],
        "Ubicación": ["provincia", "localidad", "tipo_lugar", "zonas_cobertura_list",
                     "modalidad", "requiere_viajar", "frecuencia_viaje", "radio_viaje_km",
                     "requiere_movilidad_propia", "zona_residencia_req", "acepta_relocacion"],
        "Experiencia": ["experiencia_texto", "experiencia_descripcion", "experiencia_nivel_previo",
                       "experiencia_sector", "experiencia_areas_list", "experiencia_excluyente",
                       "experiencia_valorada"],
        "Educación": ["nivel_educativo_excluyente", "titulo_requerido", "orientacion_estudios",
                     "acepta_estudiantes_avanzados", "estudios_valorados_list"],
        "Skills": ["perfil_actitudinal_list", "conocimientos_especificos_list", "herramientas_list",
                  "sistemas_list", "nivel_herramienta_json", "conocimiento_excluyente_list"],
        "Idiomas": ["idioma_excluyente", "idiomas_adicionales_json"],
        "Rol/Tareas": ["mision_rol", "interactua_con_externos_list"],
        "Condiciones": ["horario_especifico", "dias_trabajo_list", "hora_entrada", "hora_salida"],
        "Compensación": ["salario_periodo", "salario_neto", "tiene_salario_base", "tiene_comisiones",
                        "tiene_bonos", "estructura_salarial", "bonos_json", "pide_pretension_salarial",
                        "pretension_formato"],
        "Beneficios": ["tiene_cobertura_salud", "cobertura_salud_familia", "tiene_comedor",
                      "tiene_capacitacion", "tiene_crecimiento", "tiene_programa_asistencia",
                      "tiene_descuentos", "descuentos_educacion_json", "descuentos_gimnasio_json",
                      "vehiculo_provisto", "otros_beneficios_list"],
        "Metadatos": ["nlp_score_max", "largo_descripcion", "campos_con_fuente_json"],
        "Licencias": ["licencia_conducir_excluyente", "licencia_autoelevador", "otras_licencias_list",
                     "matricula_profesional", "matricula_tipo"],
        "Calidad": ["tiene_errores_tipeo", "errores_detectados_list", "calidad_redaccion",
                   "titulo_repetido_en_descripcion", "tipo_discriminacion_list", "requisito_sexo",
                   "titulo_genero_especifico", "titulo_normalizado", "es_republica",
                   "tiene_clausula_diversidad"],
        "Certificaciones": ["certificaciones_requeridas_json", "certificaciones_deseables_list",
                           "certificaciones_tecnicas_list", "certificaciones_seguridad_list"],
        "Cond. Especiales": ["trabajo_en_altura", "altura_metros", "trabajo_espacios_confinados",
                            "trabajo_exterior", "trabajo_nocturno", "trabajo_turnos_rotativos",
                            "trabajo_fines_semana", "trabajo_feriados", "trabajo_riesgo",
                            "requiere_esfuerzo_fisico", "carga_peso_kg", "ambiente_trabajo"]
    }

    print("\n" + "-" * 70)
    print("COLUMNAS POR BLOQUE")
    print("-" * 70)

    for bloque, cols in bloques.items():
        present = sum(1 for c in cols if c in columns)
        print(f"  {bloque:20} | {present}/{len(cols)}")

    print("\n" + "=" * 70)

    return added, errors


if __name__ == "__main__":
    main()
