# -*- coding: utf-8 -*-
"""Optimización y limpieza de base de datos MOL."""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print("OPTIMIZACIÓN BASE DE DATOS MOL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Estado inicial
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas_antes = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    indices_antes = [r[0] for r in cursor.fetchall()]

    print(f"\n[ESTADO INICIAL]")
    print(f"  Tablas: {len(tablas_antes)}")
    print(f"  Índices: {len(indices_antes)}")

    # ========================================
    # FASE 1: Eliminar tablas vacías/deprecated
    # ========================================
    print("\n" + "=" * 70)
    print("FASE 1: ELIMINAR TABLAS VACÍAS/DEPRECATED")
    print("=" * 70)

    tablas_eliminar = [
        'skills',
        'ofertas_skills',
        'cno_ocupaciones',
        'cno_esco_matches',
        'sinonimos_regionales',
        'circuit_breaker_stats',
        'rate_limiter_stats',
        'schema_migrations'
    ]

    eliminadas = []
    for tabla in tablas_eliminar:
        try:
            # Verificar que existe y está vacía
            cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute(f"DROP TABLE IF EXISTS [{tabla}]")
                eliminadas.append(tabla)
                print(f"  [ELIMINADA] {tabla} (0 registros)")
            else:
                print(f"  [CONSERVADA] {tabla} ({count} registros)")
        except Exception as e:
            print(f"  [ERROR] {tabla}: {e}")

    conn.commit()
    print(f"\nTablas eliminadas: {len(eliminadas)}")

    # ========================================
    # FASE 2: Crear índices faltantes
    # ========================================
    print("\n" + "=" * 70)
    print("FASE 2: CREAR ÍNDICES FALTANTES")
    print("=" * 70)

    indices_crear = [
        ("idx_ofertas_portal_fecha", "ofertas", "portal, fecha_publicacion_iso"),
        ("idx_ofertas_estado", "ofertas", "estado_oferta"),
        ("idx_ofertas_nlp_id", "ofertas_nlp", "id_oferta"),
        ("idx_ofertas_esco_isco", "ofertas_esco_matching", "isco_code"),
        ("idx_ofertas_esco_metodo", "ofertas_esco_matching", "occupation_match_method"),
    ]

    creados = []
    for idx_name, tabla, columnas in indices_crear:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON [{tabla}]({columnas})")
            creados.append(idx_name)
            print(f"  [CREADO] {idx_name} ON {tabla}({columnas})")
        except Exception as e:
            print(f"  [ERROR] {idx_name}: {e}")

    conn.commit()
    print(f"\nÍndices creados: {len(creados)}")

    # ========================================
    # FASE 3: Verificar consistencia id_oferta
    # ========================================
    print("\n" + "=" * 70)
    print("FASE 3: VERIFICAR CONSISTENCIA ID_OFERTA")
    print("=" * 70)

    tablas_id_oferta = [
        ('ofertas', 'id_oferta'),
        ('ofertas_nlp', 'id_oferta'),
        ('ofertas_esco_matching', 'id_oferta'),
        ('ofertas_esco_skills_detalle', 'id_oferta'),
        ('ofertas_raw', 'id_oferta'),
    ]

    for tabla, col in tablas_id_oferta:
        try:
            cursor.execute(f"SELECT typeof({col}), COUNT(*) FROM [{tabla}] GROUP BY typeof({col})")
            tipos = cursor.fetchall()
            tipos_str = ", ".join([f"{t[0]}:{t[1]}" for t in tipos])
            print(f"  {tabla}.{col}: {tipos_str}")
        except Exception as e:
            print(f"  [ERROR] {tabla}: {e}")

    # ========================================
    # FASE 4: Consolidar tablas duplicadas
    # ========================================
    print("\n" + "=" * 70)
    print("FASE 4: CONSOLIDAR TABLAS DUPLICADAS")
    print("=" * 70)

    tablas_v2 = ['ofertas_nlp_v2', 'keywords_performance_v2']

    for tabla in tablas_v2:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute(f"DROP TABLE IF EXISTS [{tabla}]")
                eliminadas.append(tabla)
                print(f"  [ELIMINADA] {tabla} (0 registros)")
            else:
                print(f"  [CONSERVADA] {tabla} ({count} registros)")
        except Exception as e:
            print(f"  [NO EXISTE] {tabla}")

    conn.commit()

    # ========================================
    # VERIFICACIÓN FINAL
    # ========================================
    print("\n" + "=" * 70)
    print("VERIFICACIÓN FINAL")
    print("=" * 70)

    # Contar tablas después
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas_despues = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    indices_despues = [r[0] for r in cursor.fetchall()]

    print(f"\n{'Métrica':<25} {'Antes':>10} {'Después':>10} {'Cambio':>10}")
    print("-" * 55)
    print(f"{'Tablas':<25} {len(tablas_antes):>10} {len(tablas_despues):>10} {len(tablas_despues)-len(tablas_antes):>+10}")
    print(f"{'Índices':<25} {len(indices_antes):>10} {len(indices_despues):>10} {len(indices_despues)-len(indices_antes):>+10}")

    # Tests de integridad
    print("\n[TESTS DE INTEGRIDAD]")

    # Test 1: Join ofertas + nlp
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas o
            JOIN ofertas_nlp n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        """)
        count = cursor.fetchone()[0]
        print(f"  [OK] ofertas JOIN ofertas_nlp: {count} registros")
    except Exception as e:
        print(f"  [FAIL] ofertas JOIN ofertas_nlp: {e}")

    # Test 2: Join ofertas + matching
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas o
            JOIN ofertas_esco_matching m ON CAST(o.id_oferta AS TEXT) = m.id_oferta
        """)
        count = cursor.fetchone()[0]
        print(f"  [OK] ofertas JOIN ofertas_esco_matching: {count} registros")
    except Exception as e:
        print(f"  [FAIL] ofertas JOIN ofertas_esco_matching: {e}")

    # Test 3: Diccionario
    try:
        cursor.execute("SELECT COUNT(*) FROM diccionario_arg_esco")
        count = cursor.fetchone()[0]
        print(f"  [OK] diccionario_arg_esco: {count} términos")
    except Exception as e:
        print(f"  [FAIL] diccionario_arg_esco: {e}")

    # VACUUM para compactar
    print("\n[VACUUM] Compactando base de datos...")
    conn.execute("VACUUM")

    # Tablas finales
    print("\n[TABLAS FINALES]")
    for t in tablas_despues:
        if t != 'sqlite_sequence':
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
                count = cursor.fetchone()[0]
                print(f"  {t}: {count:,} registros")
            except:
                pass

    conn.close()

    print("\n" + "=" * 70)
    print("OPTIMIZACIÓN COMPLETADA")
    print("=" * 70)
    print(f"\nTablas eliminadas ({len(eliminadas)}):")
    for t in eliminadas:
        print(f"  - {t}")
    print(f"\nÍndices creados ({len(creados)}):")
    for i in creados:
        print(f"  - {i}")

if __name__ == '__main__':
    main()
