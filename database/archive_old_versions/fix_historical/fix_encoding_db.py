#!/usr/bin/env python3
"""
FASE 1.1: Fix Encoding UTF-8 en descripciones de ofertas

Corrige encoding corrupto en campo 'descripcion' y crea columna 'descripcion_utf8' limpia.
Usa la librer[U+00ED]a ftfy (fix text for you) para corregir autom[U+00E1]ticamente encoding mixto UTF-8/Latin-1.

Uso:
    python fix_encoding_db.py

Tiempo estimado: 10-15 minutos para ~5,479 ofertas
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Verificar si ftfy est[U+00E1] instalado
try:
    import ftfy
except ImportError:
    print("ERROR: La librer[U+00ED]a 'ftfy' no est[U+00E1] instalada.")
    print("Instal[U+00E1] con: pip install ftfy")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: La librer[U+00ED]a 'tqdm' no est[U+00E1] instalada. No se mostrar[U+00E1] barra de progreso.")
    print("Pod[U+00E9]s instalarla con: pip install tqdm")
    tqdm = None


class EncodingFixer:
    """Corrige encoding UTF-8 corrupto en base de datos de ofertas"""

    def __init__(self, db_path='bumeran_scraping.db'):
        """
        Inicializa el fixer de encoding.

        Args:
            db_path (str): Ruta a la base de datos SQLite
        """
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        self.conn = None
        self.stats = {
            'total_ofertas': 0,
            'ofertas_con_descripcion': 0,
            'ofertas_corregidas': 0,
            'ofertas_sin_cambios': 0,
            'ofertas_con_errores': 0,
            'ejemplos_corregidos': []
        }

    def conectar_db(self):
        """Conecta a la base de datos SQLite"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[OK] Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error al conectar a la base de datos: {e}")
            return False

    def verificar_columna_existe(self):
        """Verifica si la columna descripcion_utf8 ya existe"""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(ofertas)")
        columnas = [col[1] for col in cursor.fetchall()]
        return 'descripcion_utf8' in columnas

    def agregar_columna_utf8(self):
        """Agrega la columna descripcion_utf8 si no existe"""
        if self.verificar_columna_existe():
            print("  -> La columna 'descripcion_utf8' ya existe")
            return True

        try:
            cursor = self.conn.cursor()
            cursor.execute("ALTER TABLE ofertas ADD COLUMN descripcion_utf8 TEXT")
            self.conn.commit()
            print("  -> Columna 'descripcion_utf8' creada exitosamente")
            return True
        except Exception as e:
            print(f"  [ERROR] Error al crear columna: {e}")
            return False

    def obtener_ofertas(self):
        """Obtiene todas las ofertas con descripci[U+00F3]n no nula"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id_oferta, descripcion
            FROM ofertas
            WHERE descripcion IS NOT NULL
            ORDER BY id_oferta
        """)
        ofertas = cursor.fetchall()
        self.stats['total_ofertas'] = len(ofertas)
        self.stats['ofertas_con_descripcion'] = len(ofertas)
        return ofertas

    def fix_text_encoding(self, text):
        """
        Corrige encoding corrupto en un texto.

        Args:
            text (str): Texto con posible encoding corrupto

        Returns:
            tuple: (texto_corregido, fue_corregido)
        """
        if not text or text.strip() == '':
            return text, False

        try:
            # ftfy corrige autom[U+00E1]ticamente encoding mixto
            texto_corregido = ftfy.fix_text(text)

            # Detectar si hubo cambios
            fue_corregido = texto_corregido != text

            return texto_corregido, fue_corregido
        except Exception as e:
            print(f"    [ERROR] Error corrigiendo texto: {e}")
            return text, False

    def guardar_ejemplo_correccion(self, id_oferta, original, corregido):
        """Guarda un ejemplo de correcci[U+00F3]n para el reporte"""
        if len(self.stats['ejemplos_corregidos']) < 5:
            # Tomar los primeros 100 caracteres de cada uno
            self.stats['ejemplos_corregidos'].append({
                'id_oferta': id_oferta,
                'original': original[:100] if original else '',
                'corregido': corregido[:100] if corregido else ''
            })

    def procesar_ofertas(self, ofertas):
        """
        Procesa todas las ofertas corrigiendo su encoding.

        Args:
            ofertas (list): Lista de tuplas (id_oferta, descripcion)
        """
        cursor = self.conn.cursor()

        # Usar tqdm si est[U+00E1] disponible
        iterator = tqdm(ofertas, desc="Corrigiendo encoding", unit="oferta") if tqdm else ofertas

        for id_oferta, descripcion in iterator:
            try:
                # Corregir encoding
                descripcion_limpia, fue_corregido = self.fix_text_encoding(descripcion)

                # Actualizar en base de datos
                cursor.execute("""
                    UPDATE ofertas
                    SET descripcion_utf8 = ?
                    WHERE id_oferta = ?
                """, (descripcion_limpia, id_oferta))

                # Actualizar estad[U+00ED]sticas
                if fue_corregido:
                    self.stats['ofertas_corregidas'] += 1
                    self.guardar_ejemplo_correccion(id_oferta, descripcion, descripcion_limpia)
                else:
                    self.stats['ofertas_sin_cambios'] += 1

            except Exception as e:
                print(f"\n  [ERROR] Error procesando oferta {id_oferta}: {e}")
                self.stats['ofertas_con_errores'] += 1

        # Commit de todos los cambios
        self.conn.commit()

    def generar_reporte(self):
        """Genera reporte de estad[U+00ED]sticas de correcci[U+00F3]n"""
        print("\n" + "=" * 70)
        print("REPORTE DE CORRECCI[U+00D3]N DE ENCODING")
        print("=" * 70)
        print(f"\n[STATS] ESTAD[U+00CD]STICAS:")
        print(f"  - Total ofertas procesadas:     {self.stats['ofertas_con_descripcion']:,}")
        print(f"  - Ofertas corregidas:           {self.stats['ofertas_corregidas']:,}")
        print(f"  - Ofertas sin cambios:          {self.stats['ofertas_sin_cambios']:,}")
        print(f"  - Ofertas con errores:          {self.stats['ofertas_con_errores']:,}")

        porcentaje_corregido = (self.stats['ofertas_corregidas'] / self.stats['ofertas_con_descripcion'] * 100) if self.stats['ofertas_con_descripcion'] > 0 else 0
        print(f"\n  [CHART] Tasa de correcci[U+00F3]n:          {porcentaje_corregido:.1f}%")

        # Mostrar ejemplos
        if self.stats['ejemplos_corregidos']:
            print(f"\n[MEMO] EJEMPLOS DE CORRECCIONES (primeros 5):")
            for i, ejemplo in enumerate(self.stats['ejemplos_corregidos'], 1):
                print(f"\n  Ejemplo {i} - Oferta ID: {ejemplo['id_oferta']}")
                print(f"    ANTES: {ejemplo['original']}...")
                print(f"    DESPU[U+00C9]S: {ejemplo['corregido']}...")

        print("\n" + "=" * 70)
        print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta el proceso completo de correcci[U+00F3]n de encoding"""
        print("\n" + "=" * 70)
        print("CORRECCI[U+00D3]N DE ENCODING UTF-8 EN DESCRIPCIONES")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Paso 1: Conectar a DB
        print("PASO 1: Conectando a base de datos...")
        if not self.conectar_db():
            return False

        # Paso 2: Agregar columna
        print("\nPASO 2: Verificando/creando columna 'descripcion_utf8'...")
        if not self.agregar_columna_utf8():
            return False

        # Paso 3: Obtener ofertas
        print("\nPASO 3: Obteniendo ofertas con descripci[U+00F3]n...")
        ofertas = self.obtener_ofertas()
        print(f"  -> {len(ofertas):,} ofertas encontradas")

        if len(ofertas) == 0:
            print("  [WARNING] No hay ofertas para procesar")
            return True

        # Paso 4: Procesar ofertas
        print(f"\nPASO 4: Corrigiendo encoding (esto puede tomar 10-15 minutos)...")
        self.procesar_ofertas(ofertas)

        # Paso 5: Generar reporte
        self.generar_reporte()

        # Cerrar conexi[U+00F3]n
        self.conn.close()

        return True

    def __del__(self):
        """Destructor: cierra la conexi[U+00F3]n si est[U+00E1] abierta"""
        if self.conn:
            self.conn.close()


def main():
    """Funci[U+00F3]n principal"""
    try:
        fixer = EncodingFixer()
        exito = fixer.ejecutar()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
