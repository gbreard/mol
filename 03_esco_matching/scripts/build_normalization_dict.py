# -*- coding: utf-8 -*-
"""
Constructor de Diccionario de Normalización Argentina → ESCO
=============================================================

Analiza los títulos de ofertas argentinas y crea un diccionario
de mapeo de términos locales a términos ESCO europeos.
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter
import re
import unicodedata

# Rutas
OFERTAS_PATH = r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809.csv"
ESCO_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")


def normalizar_texto(text):
    """Normaliza texto"""
    if pd.isna(text) or not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text


def extraer_terminos_comunes(ofertas_df):
    """Extrae términos más comunes de títulos"""
    print("\n" + "=" * 100)
    print("ANALISIS DE VOCABULARIO ARGENTINO")
    print("=" * 100)

    # Extraer todas las palabras de títulos
    todas_palabras = []
    for titulo in ofertas_df['titulo']:
        if pd.isna(titulo):
            continue
        titulo_norm = normalizar_texto(titulo)
        # Eliminar caracteres especiales
        titulo_norm = re.sub(r'[^a-z0-9\s]', ' ', titulo_norm)
        palabras = titulo_norm.split()
        todas_palabras.extend(palabras)

    # Contar frecuencia
    contador = Counter(todas_palabras)

    # Filtrar palabras muy cortas o comunes sin significado
    stopwords = {
        'de', 'y', 'para', 'con', 'en', 'el', 'la', 'los', 'las', 'un', 'una',
        'del', 'al', 'por', 'a', 'zona', 'req', 'eventual', 'sr', 'ssr', 'jr',
        'p', 'rubro', 'empresa', 'importante', 'caba', 'gba', 'norte', 'sur',
        'este', 'oeste', 'buenos', 'aires'
    }

    terminos_relevantes = {
        palabra: count
        for palabra, count in contador.items()
        if len(palabra) > 3 and palabra not in stopwords and count >= 2
    }

    # Ordenar por frecuencia
    terminos_ordenados = sorted(terminos_relevantes.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop 50 términos más frecuentes:")
    print("-" * 100)
    for i, (termino, count) in enumerate(terminos_ordenados[:50], 1):
        print(f"{i:>3}. {termino:<30} ({count:>3} veces)")

    return terminos_ordenados


def crear_diccionario_base():
    """Crea diccionario base de normalización con conocimiento experto"""

    diccionario = {
        # ========== VENDEDORES / COMERCIALES ==========
        'promovendedor': {
            'esco_terms': ['demostrador', 'promociones', 'ventas'],
            'isco_target': '5242',
            'notes': 'Demostrador de promociones/demostradora de promociones'
        },
        'promovendedora': {
            'esco_terms': ['demostrador', 'promociones', 'ventas'],
            'isco_target': '5242',
            'notes': 'Demostrador de promociones/demostradora de promociones'
        },
        'promotor': {
            'esco_terms': ['demostrador', 'promociones', 'ventas'],
            'isco_target': '5242',
            'notes': 'Demostrador de promociones/demostradora de promociones'
        },
        'vendedor': {
            'esco_terms': ['vendedor', 'especializado', 'tienda'],
            'isco_target': '5223',
            'notes': 'Vendedor especializado/vendedora especializada'
        },
        'vendedora': {
            'esco_terms': ['vendedor', 'especializado', 'tienda'],
            'isco_target': '5223',
            'notes': 'Vendedor especializado/vendedora especializada'
        },
        'asesor comercial': {
            'esco_terms': ['asesor', 'comercial', 'ventas', 'tecnico'],
            'isco_target': '2433',
            'notes': 'Representante técnico de ventas'
        },

        # ========== CONDUCTORES / TRANSPORTE ==========
        'chofer': {
            'esco_terms': ['conductor', 'vehiculo', 'camion'],
            'isco_target': '8332',
            'notes': 'Conductor de vehículo/conductora de vehículo'
        },
        'conductor': {
            'esco_terms': ['conductor', 'vehiculo'],
            'isco_target': '8332',
            'notes': 'Conductor de vehículo/conductora de vehículo'
        },
        'fletero': {
            'esco_terms': ['conductor', 'reparto', 'camion'],
            'isco_target': '8322',
            'notes': 'Conductor de camión de reparto'
        },

        # ========== OPERARIOS / PRODUCCIÓN ==========
        'operario': {
            'esco_terms': ['operador', 'maquinaria', 'produccion'],
            'isco_target': '8',  # Nivel ISCO
            'notes': 'Operador de maquinaria (varía según contexto)'
        },
        'operador': {
            'esco_terms': ['operador', 'maquinaria'],
            'isco_target': '8',
            'notes': 'Operador de maquinaria/operadora de maquinaria'
        },

        # ========== MANTENIMIENTO ==========
        'mantenimiento': {
            'esco_terms': ['mantenimiento', 'mecanico', 'reparacion'],
            'isco_target': '7',
            'notes': 'Técnico/mecánico de mantenimiento'
        },
        'oficial mantenimiento': {
            'esco_terms': ['mecanico', 'mantenimiento', 'industrial'],
            'isco_target': '7233',
            'notes': 'Mecánico de maquinaria agrícola e industrial'
        },
        'medio oficial': {
            'esco_terms': ['oficial', 'mecanico', 'mantenimiento'],
            'isco_target': '7',
            'notes': 'Oficial de oficio (nivel medio)'
        },

        # ========== PROFESIONALES ==========
        'analista': {
            'esco_terms': ['analista', 'especialista'],
            'isco_target': '2',
            'notes': 'Analista profesional (varía según área)'
        },
        'asesor': {
            'esco_terms': ['asesor', 'consultor'],
            'isco_target': '2',
            'notes': 'Asesor/consultor profesional'
        },
        'especialista': {
            'esco_terms': ['especialista', 'profesional'],
            'isco_target': '2',
            'notes': 'Especialista profesional'
        },

        # ========== TÉCNICOS ==========
        'tecnico': {
            'esco_terms': ['tecnico', 'profesional medio'],
            'isco_target': '3',
            'notes': 'Técnico de nivel medio'
        },
        'asistente': {
            'esco_terms': ['asistente', 'auxiliar'],
            'isco_target': '3',  # O '4' según contexto
            'notes': 'Asistente técnico o administrativo'
        },

        # ========== COORDINACIÓN / SUPERVISIÓN ==========
        'coordinador': {
            'esco_terms': ['coordinador', 'supervisor', 'jefe'],
            'isco_target': '1',
            'notes': 'Coordinador/supervisor (nivel directivo)'
        },
        'coordinadora': {
            'esco_terms': ['coordinador', 'supervisor', 'jefe'],
            'isco_target': '1',
            'notes': 'Coordinador/supervisor (nivel directivo)'
        },
        'responsable': {
            'esco_terms': ['responsable', 'encargado', 'jefe'],
            'isco_target': '1',
            'notes': 'Responsable/encargado de área'
        },
        'jefe': {
            'esco_terms': ['jefe', 'supervisor', 'coordinador'],
            'isco_target': '1',
            'notes': 'Jefe/supervisor'
        },
        'lider': {
            'esco_terms': ['coordinador', 'supervisor', 'responsable'],
            'isco_target': '1',
            'notes': 'Líder/coordinador de equipo'
        },

        # ========== ADMINISTRATIVOS ==========
        'administrativo': {
            'esco_terms': ['administrativo', 'oficina', 'gestion'],
            'isco_target': '4',
            'notes': 'Empleado administrativo'
        },
        'administrativa': {
            'esco_terms': ['administrativo', 'oficina', 'gestion'],
            'isco_target': '4',
            'notes': 'Empleado administrativo'
        },
        'recepcionista': {
            'esco_terms': ['recepcionista', 'atencion cliente'],
            'isco_target': '4226',
            'notes': 'Recepcionista'
        },

        # ========== SOLDADURA / METALÚRGICA ==========
        'soldador': {
            'esco_terms': ['soldador', 'soldadura'],
            'isco_target': '7212',
            'notes': 'Soldador/soldadora'
        },
        'metalurgico': {
            'esco_terms': ['soldador', 'metalurgico', 'metal'],
            'isco_target': '7212',
            'notes': 'Trabajador metalúrgico/soldador'
        },

        # ========== DEPÓSITO / LOGÍSTICA ==========
        'deposito': {
            'esco_terms': ['almacen', 'deposito', 'logistica'],
            'isco_target': '4321',
            'notes': 'Empleado de control de existencias'
        },
        'logistica': {
            'esco_terms': ['logistica', 'cadena suministro', 'transporte'],
            'isco_target': '2421',
            'notes': 'Analista de logística'
        },
        'repositor': {
            'esco_terms': ['reponedor', 'tienda', 'stock'],
            'isco_target': '5223',
            'notes': 'Reponedor de tienda'
        },

        # ========== MARKETING / VENTAS ==========
        'marketing': {
            'esco_terms': ['marketing', 'publicidad', 'comercializacion'],
            'isco_target': '2431',
            'notes': 'Especialista en marketing/publicidad'
        },

        # ========== OTROS COMUNES ==========
        'ayudante': {
            'esco_terms': ['ayudante', 'auxiliar', 'asistente'],
            'isco_target': '9',
            'notes': 'Ayudante/auxiliar (trabajo elemental)'
        },
        'senior': {
            'esco_terms': ['senior', 'experimentado'],
            'isco_target': None,
            'notes': 'Calificador de nivel (no cambiar ocupación base)'
        },
        'junior': {
            'esco_terms': ['junior', 'joven'],
            'isco_target': None,
            'notes': 'Calificador de nivel (no cambiar ocupación base)'
        }
    }

    return diccionario


def expandir_con_contextos():
    """Expansión con contextos específicos de industria"""

    contextos = {
        # Contexto: Industria/Producción
        'operario plastico': {
            'esco_terms': ['operador', 'equipos', 'tratamiento', 'plastico'],
            'isco_target': '8142',
            'notes': 'Operador de equipos de tratamiento térmico del plástico'
        },
        'operario metalurgico': {
            'esco_terms': ['soldador', 'metal', 'produccion'],
            'isco_target': '7212',
            'notes': 'Soldador/trabajador metalúrgico'
        },

        # Contexto: Farmacéutica
        'operario farmaceutico': {
            'esco_terms': ['operador', 'productos', 'farmaceuticos'],
            'isco_target': '8131',
            'notes': 'Operador de equipos de productos farmacéuticos'
        },

        # Contexto: Alimentos
        'operario carnicos': {
            'esco_terms': ['operario', 'preparados', 'carnicos'],
            'isco_target': '7511',
            'notes': 'Operario de preparados cárnicos'
        },

        # Contexto: Transporte específico
        'chofer recolector': {
            'esco_terms': ['conductor', 'vehiculo', 'recogida', 'basura'],
            'isco_target': '8332',
            'notes': 'Conductor de vehículo de recogida de basura'
        },
        'chofer reparto': {
            'esco_terms': ['conductor', 'camion', 'reparto'],
            'isco_target': '8322',
            'notes': 'Conductor de camión de reparto'
        },

        # Contexto: Ventas especializada
        'vendedor muebles': {
            'esco_terms': ['vendedor', 'especializado', 'muebles'],
            'isco_target': '5223',
            'notes': 'Vendedor especializado en muebles'
        },
        'asesor inversiones': {
            'esco_terms': ['asesor', 'financiero', 'inversiones'],
            'isco_target': '2412',
            'notes': 'Asesor financiero/de inversiones'
        },

        # Contexto: Tratamiento/Plantas
        'operador planta efluentes': {
            'esco_terms': ['operador', 'planta', 'tratamiento', 'agua'],
            'isco_target': '3131',
            'notes': 'Operador de planta de tratamiento de agua'
        },
        'operador planta gas': {
            'esco_terms': ['operador', 'planta', 'tratamiento', 'gas'],
            'isco_target': '3134',
            'notes': 'Operador de planta de tratamiento de gas'
        }
    }

    return contextos


def main():
    """Función principal"""
    print("=" * 100)
    print("CONSTRUCCION DE DICCIONARIO DE NORMALIZACION ARGENTINA -> ESCO")
    print("=" * 100)

    # Cargar ofertas
    print(f"\n[1/4] Cargando ofertas...")
    df = pd.read_csv(OFERTAS_PATH, encoding='utf-8', low_memory=False)
    print(f"  OK: {len(df)} ofertas")

    # Analizar términos comunes
    print(f"\n[2/4] Analizando vocabulario...")
    terminos_comunes = extraer_terminos_comunes(df)

    # Crear diccionario base
    print(f"\n[3/4] Construyendo diccionario de normalización...")
    diccionario_base = crear_diccionario_base()
    contextos = expandir_con_contextos()

    # Combinar
    diccionario_completo = {**diccionario_base, **contextos}

    print(f"\n  OK: {len(diccionario_completo)} entradas en diccionario")
    print(f"    - Términos base: {len(diccionario_base)}")
    print(f"    - Contextos específicos: {len(contextos)}")

    # Guardar
    print(f"\n[4/4] Guardando diccionario...")

    output_path = OUTPUT_DIR / "diccionario_normalizacion_arg_esco.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(diccionario_completo, f, indent=2, ensure_ascii=False)

    print(f"  OK: {output_path}")

    # Estadísticas
    print("\n" + "=" * 100)
    print("RESUMEN DEL DICCIONARIO")
    print("=" * 100)

    # Por nivel ISCO
    niveles_isco = {}
    for term, config in diccionario_completo.items():
        isco = config.get('isco_target')
        if isco:
            nivel = str(isco)[0] if isco else 'N/A'
            niveles_isco[nivel] = niveles_isco.get(nivel, 0) + 1

    print("\nDistribución por nivel ISCO:")
    nombres_nivel = {
        '1': 'Directores/Gerentes',
        '2': 'Profesionales',
        '3': 'Técnicos',
        '4': 'Administrativos',
        '5': 'Servicios/Ventas',
        '6': 'Agropecuarios',
        '7': 'Oficios',
        '8': 'Operadores',
        '9': 'Elementales'
    }

    for nivel in sorted(niveles_isco.keys()):
        count = niveles_isco[nivel]
        nombre = nombres_nivel.get(nivel, 'Otro')
        print(f"  ISCO {nivel} - {nombre:<20}: {count:>3} términos")

    print("\n" + "=" * 100)
    print("[COMPLETADO]")
    print("=" * 100)
    print(f"\nDiccionario guardado en:")
    print(f"  {output_path}")
    print(f"\nTotal entradas: {len(diccionario_completo)}")


if __name__ == "__main__":
    main()
