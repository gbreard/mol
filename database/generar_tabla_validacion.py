#!/usr/bin/env python3
"""
Generador de Tabla de Validación Humana
=========================================

Genera un HTML interactivo con las ofertas del A/B test para validación manual.
Incluye descripción original y todas las variables extraídas por v4.0 y v5.1
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def conectar_db():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    return sqlite3.connect(db_path)


def cargar_ids_ab_test():
    """Carga los IDs del archivo de A/B test"""
    ids_file = Path(__file__).parent / "ids_for_ab_test.txt"
    with open(ids_file, 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]


def obtener_datos_oferta(conn, id_oferta: int) -> Dict[str, Any]:
    """
    Obtiene todos los datos de una oferta: original + extracciones v4 y v5.1
    """
    cursor = conn.cursor()

    # Datos originales de la oferta
    cursor.execute("""
        SELECT
            id_oferta,
            titulo,
            empresa,
            descripcion,
            ubicacion,
            modalidad_trabajo,
            url_oferta,
            fecha_publicacion
        FROM ofertas
        WHERE id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    if not row:
        return None

    oferta_data = {
        "id_oferta": row[0],
        "titulo": row[1],
        "empresa": row[2],
        "descripcion": row[3],
        "ubicacion": row[4],
        "modalidad_trabajo": row[5],
        "url_oferta": row[6],
        "fecha_publicacion": row[7]
    }

    # Extracciones v4.0 y v5.1
    cursor.execute("""
        SELECT
            nlp_version,
            extracted_data,
            quality_score,
            confidence_score
        FROM ofertas_nlp_history
        WHERE id_oferta = ?
        ORDER BY processed_at DESC
    """, (id_oferta,))

    extracciones = {}
    for row in cursor.fetchall():
        version = row[0]
        extracciones[version] = {
            "data": json.loads(row[1]) if row[1] else {},
            "quality_score": row[2],
            "confidence_score": row[3]
        }

    oferta_data["v4"] = extracciones.get("v4.0.0")
    oferta_data["v51"] = extracciones.get("5.1.0")

    return oferta_data


def formatear_valor(valor: Any) -> str:
    """Formatea un valor para display en HTML"""
    if valor is None:
        return '<span class="null">null</span>'

    if isinstance(valor, str):
        # Si es un JSON array string, parsearlo
        if valor.startswith('[') and valor.endswith(']'):
            try:
                lista = json.loads(valor)
                if len(lista) == 0:
                    return '<span class="empty">[]</span>'
                items = ', '.join([f'"{item}"' for item in lista])
                return f'<span class="array">[{items}]</span>'
            except:
                pass
        return f'<span class="string">"{valor}"</span>'

    if isinstance(valor, bool):
        return f'<span class="bool">{str(valor).lower()}</span>'

    if isinstance(valor, (int, float)):
        return f'<span class="number">{valor}</span>'

    return str(valor)


def generar_html(ofertas: List[Dict[str, Any]], output_file: Path):
    """
    Genera el HTML interactivo con la tabla de validación
    """
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validación Humana - NLP v5.1</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header .meta {
            opacity: 0.9;
            font-size: 0.95em;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-card .label {
            color: #666;
            font-size: 0.9em;
        }

        .oferta-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: box-shadow 0.3s;
        }

        .oferta-card:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }

        .oferta-header {
            border-bottom: 2px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .oferta-id {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .oferta-titulo {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .oferta-meta {
            color: #666;
            font-size: 0.9em;
        }

        .oferta-meta span {
            margin-right: 15px;
        }

        .descripcion-original {
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
        }

        .descripcion-original h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .descripcion-texto {
            white-space: pre-wrap;
            color: #333;
            font-size: 0.95em;
            line-height: 1.6;
        }

        .comparacion {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }

        .version-box {
            background: #fafafa;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #e0e0e0;
        }

        .version-box.v4 {
            border-top: 3px solid #f59e0b;
        }

        .version-box.v51 {
            border-top: 3px solid #10b981;
        }

        .version-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .version-box.v4 .version-title {
            color: #f59e0b;
        }

        .version-box.v51 .version-title {
            color: #10b981;
        }

        .version-score {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 15px;
        }

        .campo {
            margin-bottom: 12px;
            padding: 8px;
            background: white;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .campo-nombre {
            font-weight: 600;
            color: #555;
            margin-bottom: 4px;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .campo-valor {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.95em;
        }

        .null {
            color: #999;
            font-style: italic;
        }

        .string {
            color: #059669;
        }

        .number {
            color: #2563eb;
            font-weight: 600;
        }

        .array {
            color: #7c3aed;
        }

        .empty {
            color: #999;
            font-style: italic;
        }

        .bool {
            color: #dc2626;
            font-weight: 600;
        }

        .diferencia {
            background: #fef3c7 !important;
            border-left: 3px solid #f59e0b;
        }

        .mejora {
            background: #d1fae5 !important;
            border-left: 3px solid #10b981;
        }

        .empeora {
            background: #fee2e2 !important;
            border-left: 3px solid #ef4444;
        }

        .filtros {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .filtros label {
            margin-right: 15px;
            font-weight: 500;
        }

        .filtros select, .filtros input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 15px;
            font-size: 0.95em;
        }

        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.95em;
            transition: background 0.3s;
        }

        .btn:hover {
            background: #5568d3;
        }

        .notas-validacion {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-top: 15px;
            border-radius: 4px;
        }

        .notas-validacion h4 {
            color: #856404;
            margin-bottom: 8px;
        }

        .notas-validacion textarea {
            width: 100%;
            min-height: 80px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
            font-size: 0.9em;
            resize: vertical;
        }

        @media print {
            body {
                padding: 0;
            }

            .filtros, .btn {
                display: none;
            }

            .oferta-card {
                page-break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Validación Humana - NLP v5.1</h1>
        <div class="meta">
            Comparación de extracciones: v4.0 (baseline) vs v5.1 (con inferencias contextuales)<br>
            Generado: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
        </div>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="value">""" + str(len(ofertas)) + """</div>
            <div class="label">Ofertas Analizadas</div>
        </div>
        <div class="stat-card">
            <div class="value">""" + f"{sum(1 for o in ofertas if o['v4']) / len(ofertas) * 100:.0f}%" + """</div>
            <div class="label">Cobertura v4.0</div>
        </div>
        <div class="stat-card">
            <div class="value">""" + f"{sum(1 for o in ofertas if o['v51']) / len(ofertas) * 100:.0f}%" + """</div>
            <div class="label">Cobertura v5.1</div>
        </div>
        <div class="stat-card">
            <div class="value">18</div>
            <div class="label">Campos Comparados</div>
        </div>
    </div>

    <div class="filtros">
        <label>Filtrar por:</label>
        <select id="filtro-diferencias">
            <option value="todas">Todas las ofertas</option>
            <option value="con-diferencias">Solo con diferencias</option>
            <option value="mejoras">Solo mejoras de v5.1</option>
            <option value="empeoramientos">Solo empeoramientos de v5.1</option>
        </select>
        <button class="btn" onclick="window.print()">🖨️ Imprimir / Exportar PDF</button>
    </div>
"""

    # Campos a comparar
    campos = [
        ("experiencia_min_anios", "Experiencia Mínima (años)"),
        ("experiencia_max_anios", "Experiencia Máxima (años)"),
        ("nivel_educativo", "Nivel Educativo"),
        ("estado_educativo", "Estado Educativo"),
        ("carrera_especifica", "Carrera Específica"),
        ("idioma_principal", "Idioma Principal"),
        ("nivel_idioma_principal", "Nivel de Idioma"),
        ("skills_tecnicas_list", "Skills Técnicas"),
        ("soft_skills_list", "Soft Skills"),
        ("certificaciones_list", "Certificaciones"),
        ("salario_min", "Salario Mínimo"),
        ("salario_max", "Salario Máximo"),
        ("moneda", "Moneda"),
        ("beneficios_list", "Beneficios"),
        ("requisitos_excluyentes_list", "Requisitos Excluyentes"),
        ("requisitos_deseables_list", "Requisitos Deseables"),
        ("jornada_laboral", "Jornada Laboral"),
        ("horario_flexible", "Horario Flexible")
    ]

    # Generar card para cada oferta
    for oferta in ofertas:
        # Determinar si hay diferencias
        tiene_diferencias = False
        if oferta['v4'] and oferta['v51']:
            for campo_key, _ in campos:
                v4_val = oferta['v4']['data'].get(campo_key)
                v51_val = oferta['v51']['data'].get(campo_key)
                if v4_val != v51_val:
                    tiene_diferencias = True
                    break

        data_diferencias = 'data-tiene-diferencias="true"' if tiene_diferencias else ''

        html += f"""
    <div class="oferta-card" {data_diferencias}>
        <div class="oferta-header">
            <div class="oferta-id">ID: {oferta['id_oferta']}</div>
            <div class="oferta-titulo">{oferta['titulo']}</div>
            <div class="oferta-meta">
                <span>🏢 <strong>{oferta['empresa']}</strong></span>
                <span>📍 {oferta['ubicacion'] or 'Sin ubicación'}</span>
                <span>💼 {oferta['modalidad_trabajo'] or 'Sin modalidad'}</span>
"""
        if oferta['fecha_publicacion']:
            html += f"""                <span>📅 {oferta['fecha_publicacion']}</span>
"""
        if oferta['url_oferta']:
            html += f"""                <span><a href="{oferta['url_oferta']}" target="_blank">🔗 Ver oferta</a></span>
"""

        html += """            </div>
        </div>

        <div class="descripcion-original">
            <h3>📄 Descripción Original</h3>
            <div class="descripcion-texto">"""

        # Truncar descripción si es muy larga
        desc = oferta['descripcion'] or 'Sin descripción'
        if len(desc) > 2000:
            desc = desc[:2000] + "\n\n... [DESCRIPCIÓN TRUNCADA - Ver en base de datos] ..."

        html += desc.replace('<', '&lt;').replace('>', '&gt;')
        html += """</div>
        </div>

        <div class="comparacion">
"""

        # Columna v4.0
        html += """            <div class="version-box v4">
                <div class="version-title">v4.0 (Baseline)</div>
"""

        if oferta['v4']:
            html += f"""                <div class="version-score">Quality Score: {oferta['v4']['quality_score']} | Confidence: {oferta['v4']['confidence_score']:.2f}</div>
"""
            for campo_key, campo_label in campos:
                v4_val = oferta['v4']['data'].get(campo_key)
                v51_val = oferta['v51']['data'].get(campo_key) if oferta['v51'] else None

                clase_extra = ""
                if v4_val != v51_val:
                    if v4_val is None and v51_val is not None:
                        clase_extra = " mejora"
                    elif v4_val is not None and v51_val is None:
                        clase_extra = " empeora"
                    else:
                        clase_extra = " diferencia"

                html += f"""                <div class="campo{clase_extra}">
                    <div class="campo-nombre">{campo_label}</div>
                    <div class="campo-valor">{formatear_valor(v4_val)}</div>
                </div>
"""
        else:
            html += """                <div style="color: #999; font-style: italic; padding: 20px; text-align: center;">No disponible</div>
"""

        html += """            </div>

            <div class="version-box v51">
                <div class="version-title">v5.1 (Con Inferencias)</div>
"""

        if oferta['v51']:
            html += f"""                <div class="version-score">Quality Score: {oferta['v51']['quality_score']} | Confidence: {oferta['v51']['confidence_score']:.2f}</div>
"""
            for campo_key, campo_label in campos:
                v51_val = oferta['v51']['data'].get(campo_key)
                v4_val = oferta['v4']['data'].get(campo_key) if oferta['v4'] else None

                clase_extra = ""
                if v4_val != v51_val:
                    if v4_val is None and v51_val is not None:
                        clase_extra = " mejora"
                    elif v4_val is not None and v51_val is None:
                        clase_extra = " empeora"
                    else:
                        clase_extra = " diferencia"

                html += f"""                <div class="campo{clase_extra}">
                    <div class="campo-nombre">{campo_label}</div>
                    <div class="campo-valor">{formatear_valor(v51_val)}</div>
                </div>
"""
        else:
            html += """                <div style="color: #999; font-style: italic; padding: 20px; text-align: center;">No disponible</div>
"""

        html += """            </div>
        </div>

        <div class="notas-validacion">
            <h4>✏️ Notas de Validación (para revisión manual)</h4>
            <textarea placeholder="Escribe aquí tus observaciones sobre esta extracción..."></textarea>
        </div>
    </div>
"""

    # Cerrar HTML con script de filtros
    html += """
    <script>
        document.getElementById('filtro-diferencias').addEventListener('change', function(e) {
            const filtro = e.target.value;
            const cards = document.querySelectorAll('.oferta-card');

            cards.forEach(card => {
                const tieneDiferencias = card.getAttribute('data-tiene-diferencias') === 'true';
                const tieneMejoras = card.querySelectorAll('.mejora').length > 0;
                const tieneEmpeoramientos = card.querySelectorAll('.empeora').length > 0;

                let mostrar = true;

                if (filtro === 'con-diferencias') {
                    mostrar = tieneDiferencias;
                } else if (filtro === 'mejoras') {
                    mostrar = tieneMejoras;
                } else if (filtro === 'empeoramientos') {
                    mostrar = tieneEmpeoramientos;
                }

                card.style.display = mostrar ? 'block' : 'none';
            });
        });
    </script>
</body>
</html>
"""

    # Guardar archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    print("=" * 80)
    print("GENERADOR DE TABLA DE VALIDACIÓN HUMANA")
    print("=" * 80)
    print()

    conn = conectar_db()

    print("[1/3] Cargando IDs del A/B test...")
    ids_ab_test = cargar_ids_ab_test()
    print(f"      {len(ids_ab_test)} ofertas en el conjunto de test")

    print()
    print("[2/3] Extrayendo datos de ofertas...")
    ofertas = []

    for i, id_oferta in enumerate(ids_ab_test, 1):
        if i % 10 == 0:
            print(f"      Procesadas: {i}/{len(ids_ab_test)}")

        datos = obtener_datos_oferta(conn, id_oferta)
        if datos and datos.get('v51'):  # Solo incluir ofertas con v5.1
            ofertas.append(datos)

    conn.close()

    print(f"      [OK] {len(ofertas)} ofertas con datos completos")

    print()
    print("[3/3] Generando HTML...")
    output_file = Path(__file__).parent / "validacion_humana_v51.html"
    generar_html(ofertas, output_file)

    print(f"      [OK] Archivo generado: {output_file}")
    print()
    print("=" * 80)
    print("TABLA DE VALIDACIÓN GENERADA EXITOSAMENTE")
    print("=" * 80)
    print()
    print(f"📊 Ofertas incluidas: {len(ofertas)}")
    print(f"📁 Archivo: {output_file}")
    print()
    print("Instrucciones:")
    print("  1. Abre el archivo HTML en tu navegador")
    print("  2. Usa los filtros para ver solo ofertas con diferencias")
    print("  3. Revisa cada campo y anota observaciones en el área de notas")
    print("  4. Puedes imprimir o exportar a PDF para compartir con colegas")
    print()
    print("Código de colores:")
    print("  🟢 Verde: Campo que v5.1 agregó (mejora)")
    print("  🔴 Rojo: Campo que v5.1 perdió (empeoramiento)")
    print("  🟡 Amarillo: Campo con valor diferente entre v4.0 y v5.1")
    print()


if __name__ == '__main__':
    main()
