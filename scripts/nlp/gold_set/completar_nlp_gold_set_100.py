# -*- coding: utf-8 -*-
"""
Completar NLP para Gold Set 100
================================
Ejecuta postprocessor sobre ofertas seleccionadas para completar campos vacíos.
"""
import sqlite3
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.parent  # Subir a raíz del proyecto
sys.path.insert(0, str(BASE_DIR / "database"))

from nlp_postprocessor import NLPPostprocessor
from limpiar_titulos import limpiar_titulo

DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = BASE_DIR / "database" / "gold_set_manual_v2.json"

# Cargar Gold Set actual
with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
ids_originales = set(str(item['id_oferta']) for item in gold_set)

# Conectar BD
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Seleccionar 51 ofertas adicionales con mejor NLP
cursor.execute("""
    SELECT n.id_oferta
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE o.descripcion IS NOT NULL
    AND LENGTH(o.descripcion) > 200
    AND n.id_oferta NOT IN ({})
    ORDER BY
        CASE WHEN n.provincia IS NOT NULL THEN 0 ELSE 1 END,
        CASE WHEN n.modalidad IS NOT NULL THEN 0 ELSE 1 END,
        CASE WHEN n.area_funcional IS NOT NULL THEN 0 ELSE 1 END
    LIMIT 51
""".format(','.join([f"'{i}'" for i in ids_originales])))

ids_nuevos = [row['id_oferta'] for row in cursor.fetchall()]
ids_total = list(ids_originales) + [str(i) for i in ids_nuevos]
print(f"IDs totales: {len(ids_total)} (49 originales + {len(ids_nuevos)} nuevos)")

# Inicializar postprocessor
pp = NLPPostprocessor(verbose=False)

# Procesar cada oferta para completar campos
completados = 0
for id_oferta in ids_total:
    # Obtener datos actuales
    cursor.execute("""
        SELECT n.*, o.titulo, o.descripcion, o.localizacion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta = ?
    """, (id_oferta,))
    row = cursor.fetchone()

    if not row:
        continue

    row_dict = dict(row)
    titulo = row_dict.get('titulo', '')
    descripcion = row_dict.get('descripcion', '')
    localizacion = row_dict.get('localizacion', '')

    # Preprocesar ubicación (campo debe ser 'localizacion' como en nlp_preprocessing.json)
    pre_data = pp.preprocess({'localizacion': localizacion, 'titulo': titulo})

    # Limpiar título ANTES de postprocess (para que esté disponible en inferencia)
    titulo_limpio = limpiar_titulo(titulo) if titulo else None

    # Postprocesar (incluir titulo_limpio para inferencia de area_funcional)
    nlp_data = {k: v for k, v in row_dict.items() if k not in ['titulo', 'descripcion', 'localizacion']}
    nlp_data['titulo_limpio'] = titulo_limpio or nlp_data.get('titulo_limpio')
    post_data = pp.postprocess(nlp_data, descripcion)

    # Normalizar campos que pueden venir como array
    def normalizar_valor(valor):
        """Si el valor es un array, toma el primero. Si es string JSON, parsea."""
        if valor is None:
            return None
        if isinstance(valor, list):
            return valor[0] if valor else None
        if isinstance(valor, str) and valor.startswith('['):
            try:
                lista = json.loads(valor)
                return lista[0] if lista else None
            except:
                pass
        return valor

    # Actualizar campos vacíos
    updates = []
    params = []

    # Provincia (normalizar si es array)
    provincia = normalizar_valor(pre_data.get('provincia'))
    if not row_dict.get('provincia') and provincia:
        updates.append('provincia = ?')
        params.append(provincia)

    # Localidad (normalizar si es array)
    localidad = normalizar_valor(pre_data.get('localidad'))
    if not row_dict.get('localidad') and localidad:
        updates.append('localidad = ?')
        params.append(localidad)

    if not row_dict.get('modalidad') and post_data.get('modalidad'):
        updates.append('modalidad = ?')
        params.append(post_data['modalidad'])

    if not row_dict.get('nivel_seniority') and post_data.get('nivel_seniority'):
        updates.append('nivel_seniority = ?')
        params.append(post_data['nivel_seniority'])

    if not row_dict.get('area_funcional') and post_data.get('area_funcional'):
        updates.append('area_funcional = ?')
        params.append(post_data['area_funcional'])

    if not row_dict.get('titulo_limpio') and titulo_limpio:
        updates.append('titulo_limpio = ?')
        params.append(titulo_limpio)

    # NUEVO: Agregar tareas_explicitas
    if not row_dict.get('tareas_explicitas') and post_data.get('tareas_explicitas'):
        updates.append('tareas_explicitas = ?')
        params.append(post_data['tareas_explicitas'])

    if updates:
        params.append(id_oferta)
        cursor.execute(f"UPDATE ofertas_nlp SET {', '.join(updates)} WHERE id_oferta = ?", params)
        completados += 1

conn.commit()
print(f"Ofertas actualizadas: {completados}")

# Verificar cobertura final
print("\nCOBERTURA FINAL:")
campos = ['provincia', 'localidad', 'modalidad', 'nivel_seniority', 'area_funcional', 'titulo_limpio', 'tareas_explicitas']
placeholders = ','.join([f"'{i}'" for i in ids_total])

for campo in campos:
    cursor.execute(f"""
        SELECT COUNT(*) FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders}) AND {campo} IS NOT NULL AND {campo} != ''
    """)
    count = cursor.fetchone()[0]
    pct = count / len(ids_total) * 100
    print(f"  {campo}: {pct:.0f}% ({count}/{len(ids_total)})")

conn.close()

# Guardar IDs del Gold Set expandido
output = BASE_DIR / "database" / "gold_set_nlp_100_ids.json"
with open(output, 'w', encoding='utf-8') as f:
    json.dump(ids_total, f, indent=2)
print(f"\nIDs guardados en: {output}")
