# -*- coding: utf-8 -*-
"""
Matching Manual Perfecto por Claude
====================================

Claude hace matching manual de cada caso usando razonamiento contextual.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import unicodedata
import re

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
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def buscar_en_esco(esco_data, keywords, isco_filter=None):
    """Busca ocupaciones en ESCO por keywords"""
    keywords_norm = [normalizar_texto(k) for k in keywords if k]

    matches = []
    for esco_id, data in esco_data.items():
        if not data:
            continue

        label = data.get('label_es', '') or data.get('label_en', '')
        # USAR ISCO COMPLETO (con decimales) en vez del genérico
        isco = data.get('codigo_isco', data.get('isco', ''))
        isco_4d = data.get('codigo_isco_4d', str(isco).split('.')[0] if '.' in str(isco) else isco)
        alt_labels = data.get('alt_labels_es', []) or []

        # Filtro ISCO - usar codigo_isco_4d para filtrar
        if isco_filter and not str(isco_4d).startswith(str(isco_filter)):
            continue

        # Buscar keywords en label y alt_labels
        texto_completo = f"{normalizar_texto(label)} {' '.join([normalizar_texto(a) for a in alt_labels[:3]])}"

        score = 0
        for kw in keywords_norm:
            if kw in texto_completo:
                score += 1

        if score > 0:
            matches.append({
                'esco_id': esco_id,
                'label': label,
                'isco': isco,  # Retornar ISCO completo
                'score': score,
                'alt_labels': alt_labels[:3]
            })

    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches[:10]


# MATCHING MANUAL - CASOS ESPECÍFICOS
MANUAL_MATCHES = {
    # VENDEDORES/PROMOCIÓN
    "promovendedores zona caba": {
        "buscar": ["demostrador", "promociones"],
        "isco_filter": "5242",
        "razonamiento": "Promovendedor = Demostrador de promociones (término europeo)"
    },
    "promovendedores zona norte": {
        "buscar": ["demostrador", "promociones"],
        "isco_filter": "5242",
        "razonamiento": "Promovendedor = Demostrador de promociones"
    },
    "vendedora asistente administrativo": {
        "buscar": ["asistente", "tienda"],
        "isco_filter": "5223",
        "razonamiento": "Asistente de tienda / Vendedor especializado"
    },
    "vendedor plan ahorro": {
        "buscar": ["vendedor", "especializado"],
        "isco_filter": "5223",
        "razonamiento": "Vendedor especializado"
    },

    # CONDUCTORES
    "chofer empresa avicola": {
        "buscar": ["conductor", "camion", "reparto"],
        "isco_filter": "8322",
        "razonamiento": "Conductor de camión de reparto (empresa avícola)"
    },
    "chofer recoleccion residuos": {
        "buscar": ["conductor", "vehiculo", "recogida", "basura"],
        "isco_filter": "8332",
        "razonamiento": "Conductor de vehículo de recogida de basura"
    },

    # TÉCNICOS/MECÁNICOS
    "tecnico mecanico soldador": {
        "buscar": ["soldador", "soldadura"],
        "isco_filter": "7212",
        "razonamiento": "Soldador (no técnico de sonido!)"
    },
    "soldador mig operario metalurgico": {
        "buscar": ["soldador", "soldadura"],
        "isco_filter": "7212",
        "razonamiento": "Soldador MIG"
    },

    # MANTENIMIENTO
    "operario mantenimiento": {
        "buscar": ["mecanico", "mantenimiento", "industrial"],
        "isco_filter": "7233",
        "razonamiento": "Mecánico de maquinaria industrial"
    },
    "medio oficial mantenimiento plastico": {
        "buscar": ["mecanico", "mantenimiento", "industrial"],
        "isco_filter": "7233",
        "razonamiento": "Mecánico de mantenimiento"
    },

    # COORDINADORES/SUPERVISORES
    "coordinador operaciones": {
        "buscar": ["supervisor", "produccion", "operaciones"],
        "isco_filter": "1",
        "razonamiento": "Supervisor de operaciones (no guardería ni portuarias)"
    },
    "lider comercial": {
        "buscar": ["director", "comercial", "ventas"],
        "isco_filter": "1221",
        "razonamiento": "Director/Jefe de ventas y comercialización"
    },
    "responsable marketing digital": {
        "buscar": ["responsable", "marketing", "digital"],
        "isco_filter": "1221",
        "razonamiento": "Responsable de marketing digital"
    },

    # ANALISTAS
    "analista oficina tecnica construccion": {
        "buscar": ["tecnico", "obras", "construccion"],
        "isco_filter": "3112",
        "razonamiento": "Técnico de obras de construcción civil"
    },
    "analista impuestos": {
        "buscar": ["asesor", "fiscal", "tributario"],
        "isco_filter": "2411",
        "razonamiento": "Asesor fiscal/tributario (no presupuestos)"
    },
    "analista recursos humanos": {
        "buscar": ["especialista", "recursos", "humanos"],
        "isco_filter": "2423",
        "razonamiento": "Especialista en recursos humanos"
    },
    "analista logistica": {
        "buscar": ["analista", "logistica", "cadena"],
        "isco_filter": "2421",
        "razonamiento": "Analista de logística y cadena de suministro"
    },

    # ASISTENTES
    "asistente marketing digital ventas": {
        "buscar": ["ayudante", "asistente", "marketing"],
        "isco_filter": "2431",
        "razonamiento": "Ayudante/asistente de marketing"
    },

    # OPERARIOS
    "operario central pesada": {
        "buscar": ["operador", "equipos", "pesados"],
        "isco_filter": "8",
        "razonamiento": "Operador de equipos pesados/maquinaria"
    },
    "operador planta tratamiento efluentes": {
        "buscar": ["operador", "planta", "tratamiento", "agua"],
        "isco_filter": "3131",
        "razonamiento": "Operador de planta de tratamiento de agua"
    },

    # ADMINISTRATIVOS
    "administrativo deposito logistica": {
        "buscar": ["empleado", "control", "existencias", "almacen"],
        "isco_filter": "4321",
        "razonamiento": "Empleado de control de existencias"
    },

    # ASESORES COMERCIALES
    "asesor comercial venta muebles": {
        "buscar": ["vendedor", "especializado", "muebles"],
        "isco_filter": "5223",
        "razonamiento": "Vendedor especializado en muebles"
    },

    # SENIOR/OTROS
    "senior reintegros": {
        "buscar": ["empleado", "seguros"],
        "isco_filter": "3321",
        "razonamiento": "Empleado de seguros (gestión de reintegros)"
    },

    # CASOS ADICIONALES - COMPLETANDO LOS 16 PENDIENTES

    # Analista de Oficina Técnica (construcción)
    "analista oficina tecnica": {
        "buscar": ["tecnico", "construccion", "civil", "obras"],
        "isco_filter": "3112",
        "razonamiento": "Técnico de construcción civil (oficina técnica)"
    },

    # Mantenimiento específico
    "operario mantenimiento san martin": {
        "buscar": ["mecanico", "mantenimiento", "maquinaria"],
        "isco_filter": "7233",
        "razonamiento": "Mecánico de mantenimiento de maquinaria industrial"
    },

    # Analista RRHH
    "analista hard recursos humanos": {
        "buscar": ["especialista", "recursos", "humanos", "gestion"],
        "isco_filter": "2423",
        "razonamiento": "Especialista en gestión de recursos humanos"
    },

    # Asesores comerciales
    "asesor comercial venta sillones muebles": {
        "buscar": ["vendedor", "especializado", "muebles"],
        "isco_filter": "5223",
        "razonamiento": "Vendedor especializado en muebles"
    },

    # Coordinador operaciones
    "coordinador operaciones req199724 eventual tortuguitas": {
        "buscar": ["supervisor", "almacen", "deposito"],
        "isco_filter": "1324",
        "razonamiento": "Supervisor de almacén/depósito (operaciones logísticas)"
    },

    # Medio oficial
    "medio oficial mantenimiento rubro plastico zona villa soldati": {
        "buscar": ["mecanico", "mantenimiento", "industrial"],
        "isco_filter": "7233",
        "razonamiento": "Mecánico de mantenimiento"
    },

    # Chofer recolección
    "chofer con experiencia en recoleccion de residuos villa lugano": {
        "buscar": ["conductor", "vehiculo", "recogida", "basura"],
        "isco_filter": "8332",
        "razonamiento": "Conductor de vehículo de recogida de basura"
    },

    # Responsable marketing
    "responsable marketing digital para recuperodatos": {
        "buscar": ["responsable", "marketing", "digital"],
        "isco_filter": "1221",
        "razonamiento": "Responsable de marketing digital"
    },

    # Auxiliar atención paciente
    "auxiliar atencion paciente bilingue hospitality": {
        "buscar": ["auxiliar", "enfermeria", "atencion", "pacientes"],
        "isco_filter": "5321",
        "razonamiento": "Auxiliar de enfermería/atención al paciente"
    }
}


def main():
    """Función principal"""
    print("=" * 100)
    print("MATCHING MANUAL PERFECTO POR CLAUDE")
    print("=" * 100)

    # Cargar datos
    print(f"\n[1/3] Cargando ofertas...")
    df = pd.read_csv(OFERTAS_PATH, encoding='utf-8', low_memory=False)
    print(f"  OK: {len(df)} ofertas")

    print(f"\n[2/3] Cargando ESCO...")
    with open(ESCO_PATH, 'r', encoding='utf-8') as f:
        esco_data = json.load(f)
    print(f"  OK: {len(esco_data)} ocupaciones")

    print(f"\n[3/3] Procesando matches manuales...")
    print(f"  Reglas definidas: {len(MANUAL_MATCHES)}")

    # Procesar cada oferta
    resultados = []

    # Palabras de ubicación/zona que no son discriminatorias
    palabras_ubicacion = {'zona', 'norte', 'sur', 'caba', 'para', 'con', 'experiencia', 'req',
                          'eventual', 'sr', 'ssr', 'tortuguitas', 'beccar', 'soldati', 'ciudadela',
                          'villa', 'san', 'martin', 'lugano', 'rubro', 'plastico', 'req199724'}

    for idx, row in df.iterrows():
        titulo = row['titulo']
        titulo_norm = normalizar_texto(titulo)

        # Buscar en reglas manuales (más estricto)
        match_info = None
        for patron, config in MANUAL_MATCHES.items():
            # Filtrar palabras de ubicación del patrón
            palabras_patron = [p for p in patron.split() if p not in palabras_ubicacion]
            palabras_titulo = [p for p in titulo_norm.split() if p not in palabras_ubicacion]

            # Contar cuántas palabras CLAVE del patrón están en título
            palabras_en_titulo = sum(1 for p in palabras_patron if p in palabras_titulo)

            # Match si al menos 70% de palabras CLAVE están presentes (más estricto)
            if palabras_patron and palabras_en_titulo >= len(palabras_patron) * 0.7:
                # Buscar en ESCO
                candidatos = buscar_en_esco(
                    esco_data,
                    config['buscar'],
                    config.get('isco_filter')
                )

                if candidatos:
                    mejor = candidatos[0]
                    match_info = {
                        'esco_id': mejor['esco_id'],
                        'esco_label': mejor['label'],
                        'isco_code': mejor['isco'],
                        'confidence': 'manual_perfecto',
                        'razonamiento': config['razonamiento'],
                        'patron_usado': patron
                    }
                break

        if not match_info:
            match_info = {
                'esco_id': None,
                'esco_label': None,
                'isco_code': None,
                'confidence': 'pendiente_manual',
                'razonamiento': 'No hay regla definida - requiere análisis manual',
                'patron_usado': None
            }

        resultados.append({
            'titulo': titulo,
            'claude_esco_id': match_info['esco_id'],
            'claude_esco_label': match_info['esco_label'],
            'claude_isco_code': match_info['isco_code'],
            'claude_confidence': match_info['confidence'],
            'claude_razonamiento': match_info['razonamiento'],
            'claude_patron': match_info['patron_usado'],
            # Original para comparar
            'fuzzy_esco_label': row.get('esco_occupation_label', ''),
            'fuzzy_isco_code': row.get('esco_codigo_isco', ''),
            'fuzzy_confidence': row.get('esco_confianza', '')
        })

    # Guardar
    df_results = pd.DataFrame(resultados)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"matching_manual_claude_{timestamp}.csv"

    df_results.to_csv(output_path, index=False, encoding='utf-8')

    # Estadísticas
    matched = df_results['claude_esco_label'].notna().sum()
    pendientes = (df_results['claude_confidence'] == 'pendiente_manual').sum()

    print(f"\n" + "=" * 100)
    print("RESULTADOS")
    print("=" * 100)
    print(f"\n  Matched con reglas:  {matched} ({matched/len(df)*100:.1f}%)")
    print(f"  Pendientes manual:   {pendientes} ({pendientes/len(df)*100:.1f}%)")
    print(f"\n  Guardado: {output_path}")
    print("=" * 100)


if __name__ == "__main__":
    main()
