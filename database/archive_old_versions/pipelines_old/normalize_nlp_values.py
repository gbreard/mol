# -*- coding: utf-8 -*-
"""
Normalizador de Valores NLP
===========================

Normaliza valores extraídos por LLM a vocabulario controlado.
Uso: importar normalizar_valor() o ejecutar para aplicar a la BD.
"""

import sqlite3
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"


def quitar_acentos(texto):
    """Quita acentos de un texto."""
    if texto is None:
        return None
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# Mapeo de valores a normalizar
NORMALIZACIONES = {
    "modalidad": {
        "semi presencial": "hibrido",
        "semipresencial": "hibrido",
        "híbrido": "hibrido",
        "hibrido": "hibrido",
        "hibrida": "hibrido",
        "híbrida": "hibrido",
        "presencial": "presencial",
        "remoto": "remoto",
        "home office": "remoto",
        "trabajo remoto": "remoto",
        "mixta": "hibrido",
        "mixto": "hibrido",
    },
    "nivel_seniority": {
        "semi-senior": "semisenior",
        "semi senior": "semisenior",
        "ssr": "semisenior",
        "semisenior": "semisenior",
        "sr": "senior",
        "senior": "senior",
        "jr": "junior",
        "junior": "junior",
        "trainee": "trainee",
        "lead": "lead/manager",
        "lead/manager": "lead/manager",
        "manager": "lead/manager",
        "jefe": "lead/manager",
        "gerente": "lead/manager",
        "director": "lead/manager",
    },
    "area_funcional": {
        # Con tildes -> sin tildes
        "producción": "Produccion/Manufactura",
        "produccion": "Produccion/Manufactura",
        "produccion/manufactura": "Produccion/Manufactura",
        "administración": "Administracion/Finanzas",
        "administracion": "Administracion/Finanzas",
        "administración/finanzas": "Administracion/Finanzas",
        "administracion/finanzas": "Administracion/Finanzas",
        "it/sistemas": "IT/Sistemas",
        "sistemas": "IT/Sistemas",
        "tecnología": "IT/Sistemas",
        "tecnologia": "IT/Sistemas",
        "ventas/comercial": "Ventas/Comercial",
        "ventas": "Ventas/Comercial",
        "comercial": "Ventas/Comercial",
        "operaciones/logistica": "Operaciones/Logistica",
        "operaciones/logística": "Operaciones/Logistica",
        "logistica": "Operaciones/Logistica",
        "logística": "Operaciones/Logistica",
        "operaciones": "Operaciones/Logistica",
        "rrhh": "RRHH",
        "recursos humanos": "RRHH",
        "marketing": "Marketing",
        "salud": "Salud",
        "educacion": "Educacion",
        "educación": "Educacion",
        "legal": "Legal",
        "atencion al cliente": "Atencion al Cliente",
        "atención al cliente": "Atencion al Cliente",
        "customer service": "Atencion al Cliente",
        "consultoria": "Consultoria",
        "consultoría": "Consultoria",
        "otros": "Otros",
    },
    "tipo_oferta": {
        "demanda_real": "demanda_real",
        "demanda real": "demanda_real",
        "bolsa_trabajo": "bolsa_trabajo",
        "bolsa de trabajo": "bolsa_trabajo",
        "consultora_pool": "consultora_pool",
        "consultora pool": "consultora_pool",
    },
    "jornada_laboral": {
        "full_time": "full_time",
        "full time": "full_time",
        "full-time": "full_time",
        "tiempo completo": "full_time",
        "part_time": "part_time",
        "part time": "part_time",
        "part-time": "part_time",
        "medio tiempo": "part_time",
        "por_horas": "por_horas",
        "por horas": "por_horas",
        "freelance": "freelance",
    },
}


def normalizar_valor(campo, valor):
    """
    Normaliza un valor según el campo.

    Args:
        campo: nombre del campo (modalidad, nivel_seniority, etc.)
        valor: valor a normalizar

    Returns:
        Valor normalizado o el original si no hay mapeo.
    """
    if valor is None:
        return None

    # Normalizar: quitar espacios, lowercase
    valor_norm = str(valor).lower().strip()
    valor_norm = quitar_acentos(valor_norm)

    if campo in NORMALIZACIONES:
        mapeo = NORMALIZACIONES[campo]
        # Buscar en mapeo (también sin acentos)
        for key, normalized in mapeo.items():
            if quitar_acentos(key.lower()) == valor_norm:
                return normalized

    return valor


def aplicar_normalizacion_bd(dry_run=True):
    """
    Aplica normalización a todas las ofertas con NLP v10.0.0.

    Args:
        dry_run: Si True, solo muestra qué cambiaría sin modificar.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Campos a normalizar
    campos = ['modalidad', 'nivel_seniority', 'area_funcional', 'tipo_oferta', 'jornada_laboral']

    # Obtener ofertas v10
    cursor.execute("""
        SELECT id_oferta, modalidad, nivel_seniority, area_funcional, tipo_oferta, jornada_laboral
        FROM ofertas_nlp
        WHERE nlp_version = '10.0.0'
    """)
    rows = cursor.fetchall()

    print(f"Ofertas NLP v10.0.0: {len(rows)}")
    print("=" * 70)

    cambios = []
    for row in rows:
        id_oferta = row['id_oferta']
        updates = {}

        for campo in campos:
            valor_original = row[campo]
            valor_normalizado = normalizar_valor(campo, valor_original)

            if valor_original != valor_normalizado and valor_original is not None:
                updates[campo] = {
                    'original': valor_original,
                    'normalizado': valor_normalizado
                }

        if updates:
            cambios.append({
                'id_oferta': id_oferta,
                'updates': updates
            })

    # Mostrar cambios
    print(f"\nCambios a realizar: {len(cambios)}")
    print("-" * 70)

    for cambio in cambios:
        print(f"\nID: {cambio['id_oferta']}")
        for campo, vals in cambio['updates'].items():
            print(f"  {campo}: '{vals['original']}' -> '{vals['normalizado']}'")

    if dry_run:
        print("\n[DRY RUN] No se aplicaron cambios. Ejecutar con dry_run=False para aplicar.")
    else:
        # Aplicar cambios
        print("\nAplicando cambios...")
        for cambio in cambios:
            for campo, vals in cambio['updates'].items():
                cursor.execute(f"""
                    UPDATE ofertas_nlp
                    SET [{campo}] = ?
                    WHERE id_oferta = ? AND nlp_version = '10.0.0'
                """, (vals['normalizado'], cambio['id_oferta']))

        conn.commit()
        print(f"[OK] {len(cambios)} registros actualizados.")

    conn.close()
    return cambios


def mostrar_valores_unicos():
    """Muestra valores únicos por campo crítico."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    campos = ['modalidad', 'nivel_seniority', 'area_funcional', 'tipo_oferta', 'jornada_laboral']

    print("=" * 70)
    print("VALORES UNICOS POR CAMPO (NLP v10.0.0)")
    print("=" * 70)

    for campo in campos:
        cursor.execute(f"""
            SELECT DISTINCT [{campo}], COUNT(*) as cnt
            FROM ofertas_nlp
            WHERE nlp_version = '10.0.0'
            GROUP BY [{campo}]
            ORDER BY cnt DESC
        """)

        print(f"\n{campo}:")
        for row in cursor.fetchall():
            valor = row[0] if row[0] else "(NULL)"
            print(f"  {valor}: {row[1]}")

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        aplicar_normalizacion_bd(dry_run=False)
    elif len(sys.argv) > 1 and sys.argv[1] == "--show":
        mostrar_valores_unicos()
    else:
        # Por defecto, dry run
        aplicar_normalizacion_bd(dry_run=True)
        print("\n" + "=" * 70)
        mostrar_valores_unicos()
