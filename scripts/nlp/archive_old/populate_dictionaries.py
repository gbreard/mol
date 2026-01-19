#!/usr/bin/env python3
"""
FASE 3: Poblar diccionarios argentinos y CNO

Carga en DB:
- Diccionario normalizaci[U+00F3]n Argentina-ESCO
- Sin[U+00F3]nimos regionales
- Ocupaciones CNO (si existe)
- Matches CNO-ESCO pre-calculados

Tiempo estimado: 2-5 minutos
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

class DictionaryPopulator:
    """Pobla diccionarios argentinos en DB"""

    def __init__(self, db_path='bumeran_scraping.db'):
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.conn = None
        self.stats = {
            'dict_arg_esco': 0,
            'sinonimos': 0,
            'cno_ocupaciones': 0,
            'cno_matches': 0,
            'errores': []
        }

    def conectar_db(self):
        """Conecta a DB"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[OK] Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            return False

    def cargar_diccionario_arg_esco(self):
        """Carga diccionario_normalizacion_arg_esco.json"""
        print("\n[BOOK] CARGANDO DICCIONARIO ARG-ESCO")
        print("=" * 70)

        json_path = Path(__file__).parent.parent / "03_esco_matching/data/diccionario_normalizacion_arg_esco.json"

        if not json_path.exists():
            print(f"  [WARNING] Archivo no encontrado: {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cursor = self.conn.cursor()

        for termino_arg, info in data.items():
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO diccionario_arg_esco (
                        termino_argentino, esco_terms_json, isco_target,
                        esco_preferred_label, notes
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    termino_arg,
                    json.dumps(info.get('esco_terms', []), ensure_ascii=False),
                    info.get('isco_target'),
                    info.get('notes'),
                    info.get('notes')
                ))
                self.stats['dict_arg_esco'] += 1
            except Exception as e:
                self.stats['errores'].append(f"Dict ARG {termino_arg}: {e}")

        self.conn.commit()
        print(f"  [OK] {self.stats['dict_arg_esco']:,} t[U+00E9]rminos argentinos cargados")

    def cargar_sinonimos_regionales(self):
        """Carga diccionario_sinonimos_ocupacionales_AR_ES.json"""
        print("\n[WORLD] CARGANDO SIN[U+00D3]NIMOS REGIONALES")
        print("=" * 70)

        json_path = Path(r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\diccionario_sinonimos_ocupacionales_AR_ES.json")

        if not json_path.exists():
            print(f"  [WARNING] Archivo no encontrado: {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cursor = self.conn.cursor()

        for categoria, ocupaciones in data.items():
            for termino_base, info_regional in ocupaciones.items():
                try:
                    for pais, sinonimos in info_regional.items():
                        if pais == 'descripcion':
                            continue

                        cursor.execute("""
                            INSERT OR IGNORE INTO sinonimos_regionales (
                                categoria_ocupacional, termino_base, pais,
                                sinonimos_json, descripcion
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            categoria,
                            termino_base,
                            pais,
                            json.dumps(sinonimos if isinstance(sinonimos, list) else [sinonimos], ensure_ascii=False),
                            info_regional.get('descripcion', '')
                        ))
                        self.stats['sinonimos'] += 1
                except Exception as e:
                    self.stats['errores'].append(f"Sin[U+00F3]nimo {termino_base}: {e}")

        self.conn.commit()
        print(f"  [OK] {self.stats['sinonimos']:,} variantes regionales cargadas")

    def generar_reporte(self):
        """Genera reporte final"""
        print("\n" + "=" * 70)
        print("REPORTE FINAL")
        print("=" * 70)

        print(f"\n[STATS] ESTAD[U+00CD]STICAS:")
        print(f"  - T[U+00E9]rminos AR-ESCO:       {self.stats['dict_arg_esco']:,}")
        print(f"  - Variantes regionales:   {self.stats['sinonimos']:,}")
        print(f"  - Ocupaciones CNO:        {self.stats['cno_ocupaciones']:,}")
        print(f"  - Matches CNO-ESCO:       {self.stats['cno_matches']:,}")

        if self.stats['errores']:
            print(f"\n[WARNING] ERRORES: {len(self.stats['errores'])}")
            for error in self.stats['errores'][:5]:
                print(f"  - {error}")

        print("\n" + "=" * 70)
        print("[OK] PROCESO COMPLETADO")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta proceso completo"""
        print("\n" + "=" * 70)
        print("POBLACI[U+00D3]N DE DICCIONARIOS ARGENTINOS")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.conectar_db():
            return False

        self.cargar_diccionario_arg_esco()
        self.cargar_sinonimos_regionales()

        self.generar_reporte()

        self.conn.close()
        return True

    def __del__(self):
        if self.conn:
            self.conn.close()


def main():
    try:
        populator = DictionaryPopulator()
        exito = populator.ejecutar()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
