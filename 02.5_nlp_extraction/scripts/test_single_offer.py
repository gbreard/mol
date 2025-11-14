# -*- coding: utf-8 -*-
"""Test de extracción híbrida sobre una oferta específica"""

import subprocess
import json
import re

texto = """Recepcionista / Asistente AdministrativoResumen del PuestoEstamos buscando una persona proactiva y organizada para unirse a nuestro equipo como Recepcionista / Asistente Administrativo. El candidato ideal tendrá excelentes habilidades de comunicación y atención al cliente, así como experiencia en tareas administrativas generales.Responsabilidades Atención al público (presencial y telefónica). Ventas de todos los tratamientos y productos ofrecidos en el Centro de estética.  Manejo de agenda y coordinación de reuniones. Gestión de correo electrónico y correspondencia. Administración de bases de datos. Facturación y cobro. Control de stock. Apertura y cierre del local. Mantenimiento del orden del espacio de trabajo. Asistencia general al equipo.Requisitos Experiencia en atención al cliente y tareas administrativas. Experiencia en ventas. Manejo de herramientas informáticas (paquete Office, Google Drive, etc.). Excelentes habilidades de comunicación interpersonal. Capacidad de organización y gestión del tiempo. Proactividad y orientación al detalle. Se valorará experiencia en manejo de caja y facturación."""

print('=' * 70)
print('PROCESANDO CON EL SISTEMA HIBRIDO REAL')
print('=' * 70)
print()

# FASE 1: REGEX
print('FASE 1: EXTRACCION REGEX')
print('-' * 70)

# Soft skills
soft_skills_regex = []
soft_patterns = [
    'comunicación', 'organización', 'proactividad', 'orientación al detalle',
    'atención al cliente', 'trabajo en equipo'
]
for pattern in soft_patterns:
    if pattern.lower() in texto.lower():
        soft_skills_regex.append(pattern)

print(f'Soft skills: {len(soft_skills_regex)}')
for skill in soft_skills_regex:
    print(f'  - {skill}')

# Skills técnicas
tech_skills_regex = []
tech_patterns = ['office', 'excel', 'google drive', 'facturación', 'bases de datos']
for pattern in tech_patterns:
    if pattern.lower() in texto.lower():
        tech_skills_regex.append(pattern)

print(f'\nSkills tecnicas: {len(tech_skills_regex)}')
for skill in tech_skills_regex:
    print(f'  - {skill}')

# Experiencia
exp_match = re.search(r'(\d+)\s*año', texto.lower())
experiencia = exp_match.group(1) if exp_match else None
print(f'\nExperiencia: {experiencia}')

# Educación
edu_match = re.search(r'(secundario|terciario|universitario|posgrado)', texto.lower())
educacion = edu_match.group(1) if edu_match else None
print(f'Educacion: {educacion}')

print()
print('DECISION: Faltan campos -> LLAMAR LLM')
print()

# FASE 2: LLM
print('FASE 2: EXTRACCION LLM (Ollama llama3)')
print('-' * 70)

prompt = f"""Eres un experto extrayendo información de ofertas laborales en español.

OFERTA LABORAL:
\"\"\"
{texto[:1500]}
\"\"\"

TAREA: Extrae SOLO estos campos:

1. nivel_educativo: Nivel educativo requerido (opciones: "secundario", "terciario", "universitario", "posgrado")
2. soft_skills: Lista de habilidades blandas (ej: ["trabajo en equipo", "liderazgo"])

IMPORTANTE:
- Responde SOLO con JSON valido
- Si no encuentras algo, usa null

FORMATO JSON:
{{
    "nivel_educativo": "universitario",
    "soft_skills": ["trabajo en equipo", "liderazgo"]
}}

JSON:"""

try:
    result = subprocess.run(
        ['ollama', 'run', 'llama3'],
        input=prompt,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=20
    )

    response = result.stdout.strip()

    # Extraer JSON
    if '```json' in response:
        response = response.split('```json')[1].split('```')[0].strip()
    elif '```' in response:
        response = response.split('```')[1].split('```')[0].strip()

    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
    if json_match:
        response = json_match.group(0)

    llm_result = json.loads(response)

    print('LLM extrajo:')
    print(json.dumps(llm_result, indent=2, ensure_ascii=False))

    # FASE 3: COMBINACION
    print()
    print('FASE 3: COMBINACION HIBRIDA')
    print('-' * 70)

    # Combinar soft skills
    all_soft_skills = set(soft_skills_regex)
    if llm_result.get('soft_skills'):
        for skill in llm_result['soft_skills']:
            if skill:
                all_soft_skills.add(skill)

    print(f'Soft Skills finales (Regex + LLM): {len(all_soft_skills)}')
    for skill in sorted(all_soft_skills):
        print(f'  - {skill}')

    # Educación
    final_edu = llm_result.get('nivel_educativo') if not educacion else educacion
    print(f'\nEducacion final: {final_edu}')

    print()
    print('=' * 70)
    print('COMO QUEDARIA EN EL CSV LIMPIO')
    print('=' * 70)
    print()
    print(f'soft_skills_clean: "{", ".join(sorted(all_soft_skills))}"')
    print(f'soft_skills_count: {len(all_soft_skills)}')
    print(f'skills_tecnicas_clean: "{", ".join(tech_skills_regex)}"')
    print(f'skills_tecnicas_count: {len(tech_skills_regex)}')
    print(f'final_nivel_educativo: {final_edu}')
    print(f'experiencia_min_anios: {experiencia}')
    print(f'hybrid_method: regex+llm')
    print(f'hybrid_llm_called: True')
    print(f'is_complete: {bool(experiencia and final_edu and all_soft_skills)}')

except Exception as e:
    print(f'Error: {e}')
    print('\nUsando solo Regex (fallback)')
