#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
limpiar_titulos.py v2.8.1
========================
Limpia titulos de ofertas eliminando ruido empresarial/geografico.
Lee patrones desde config/nlp_titulo_limpieza.json

v2.8.1 (2026-02-09): Second pass cleanup, zona de trabajo, // modalidad, validator false positives
v2.8.0 (2026-02-08): Fix sobre-limpieza + sub-limpieza + cosméticos
- Fix regex contexto_empresarial: \b word boundary + \s+-\s+ (evita DI-Vendedor)
- Fix Sucursal sin guión obligatorio (destruía "Jefe De Sucursal para Santiago")
- Fix zonas_ubicaciones greedy .*$ → match explícito
- Fix contexto_empresarial_sin_guion greedy → máx 1-3 palabras
- Fix parentesis_eliminar 15+ chars → lookahead con keywords o 40+ chars
- Safety guard: si titulo_limpio < 5 chars, mantener original
- Nuevas localidades: Burzaco, Spegazzini, Los Cardales, etc.
- Nuevos patrones: pipes al inicio, (ref XXX), puntuación final, guión inicio
- regenerar_titulo_limpio() para re-procesar títulos sin tocar matching/NLP

v2.7.0 (2026-02-08): Fix acrónimos destruidos por normalización
- normalizar_capitalizacion() ahora preserva acrónimos via whitelist ACRONYMS
- DBA, SAP, QA, SQL, PHP, etc. se mantienen en mayúsculas
- Antes: "DBA Senior" → "Dba senior" (INCORRECTO)
- Ahora: "DBA Senior" → "DBA senior" (CORRECTO)

v2.6.3 (2026-02-02): Fix 7 errores de validación
- Nueva sección: modalidad_ubicacion_combinado (eventual MAR DEL PLATA)
- Procesa ANTES de modalidad_final para capturar bloques completos
- Patrones para guion largo + modalidad (– Modalidad Híbrida)
- Localidades en paréntesis minúsculas (boulogne, caba, etc)

v2.6.2 (2026-01-30): Fix 3 errores detectados
- BUSCAMOS (mayusculas): re.IGNORECASE para prefijos_genericos
- Capital Federal / Zona Sur: patron expandido
- Part Time con guion: agregar a modalidad_guion

v2.6 (2026-01-28): Normalización capitalización (Sentence case)
- Todos los títulos con formato uniforme: "Analista de marketing"
- Primera letra mayúscula, resto minúsculas

v2.5 (2026-01-28): Fix 60 errores detectados en análisis completo
- Ubicaciones SIN guión al final (CABA, Tucumán, etc)
- Códigos inicio ampliados (H -, 1289CC/)
- Prefijo "Aviso de Empleo:"
- Contexto empresarial ampliado

v2.4 (2026-01-28): Fix títulos detectados en dashboard
- Zona Sur/Norte con punto opcional al final
- "en Zona Sur." ahora se limpia
- Playa Grande y otras localidades costeras agregadas
- contexto_empresarial_sin_guion: "para Empresa de X"

v2.2 (2026-01-13): Agregados patrones FASE 1 optimizacion
- codigos_final: "DevOps - Remoto - 1729" -> "DevOps"
- modalidad_guion: "Java - Mix (On Site & Remoto)" -> "Java"
- requisitos_edad: "Vendedor +45 años" -> "Vendedor"
- ubicacion_guion_extendido: "Analista - Retiro" -> "Analista"

Patrones de ruido:
- Ubicaciones: "- Roque Perez - BA", "Z/Escobar", "zona CABA"
- Empresas/sectores: "(Consumo Masivo)", "para Maderera (PYME)"
- Codigos: "(req199380)", "(Eventual)", "- 1729"
- Modalidad: "- Remoto -", "- Mix (On Site & Remoto)"
- Contexto excesivo: "importante Concesionario Oficial..."
"""

import os
import re
import sqlite3
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

base = Path(__file__).parent
config_dir = base.parent / "config"


def cargar_config() -> Dict[str, Any]:
    """Carga configuracion desde JSON"""
    config_path = config_dir / "nlp_titulo_limpieza.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# Cargar config una vez al importar
_CONFIG = cargar_config()


# Whitelist de acrónimos que NO se deben convertir a minúsculas
ACRONYMS = {
    "DBA", "SAP", "ABAP", "PM", "QA", "UX", "UI", "HR", "IT", "BI",
    "CRM", "ERP", "SQL", "ETL", "KAM", "CFO", "CEO", "CTO", "COO",
    "RRHH", "CCTV", "CAD", "BIM", "GIS", "AWS", "API", "DEVOPS",
    "SRE", "SSR", "SR", "JR", "RRPP", "IOT", "ML", "IA", "AI",
    "PHP", "NET", "PLC", "HVAC", "SAP", "SCRUM", "ITIL",
    "HTML", "CSS", "SEM", "SEO", "KPI", "EHS", "HSE", "QHSE",
}


def normalizar_capitalizacion(titulo: str) -> str:
    """
    Normaliza capitalización a Sentence case, preservando acrónimos.
    Primera palabra capitalizada, resto minúsculas EXCEPTO acrónimos de la whitelist.

    Args:
        titulo: Título a normalizar

    Returns:
        Título normalizado preservando acrónimos

    Ejemplos:
        "OPERARIO/A DE PRODUCCIÓN" -> "Operario/a de producción"
        "analista de marketing" -> "Analista de marketing"
        "Gerente De Ventas" -> "Gerente de ventas"
        "DBA SENIOR" -> "DBA senior"
        "Analista SAP ABAP" -> "Analista SAP ABAP"
        "QA Tester" -> "QA tester"
        "PM Digital" -> "PM digital"
    """
    if not titulo:
        return titulo

    words = titulo.split()
    result = []
    for i, word in enumerate(words):
        # Extraer solo letras para comparar con whitelist
        clean = re.sub(r'[^a-zA-Z]', '', word)
        if clean.upper() in ACRONYMS:
            # Preservar acrónimo en mayúsculas (mantener puntuación original)
            result.append(re.sub(r'[a-zA-Z]+', lambda m: m.group().upper(), word))
        elif i == 0:
            # Primera palabra: capitalizar
            result.append(word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper())
        else:
            result.append(word.lower())
    return " ".join(result)


def limpiar_titulo(titulo: str, config: Dict[str, Any] = None) -> str:
    """
    Limpia un titulo de oferta eliminando ruido.

    Args:
        titulo: Titulo original de la oferta
        config: Config opcional (usa _CONFIG global si no se pasa)

    Returns:
        Titulo limpio, solo con la ocupacion

    Ejemplos:
        "Gerente de Operaciones - Gastronomia corporativa" -> "Gerente de Operaciones"
        "Analista de Cultivo - Roque Perez - BA" -> "Analista de Cultivo"
        "Representante Comercial (Consumo Masivo)" -> "Representante Comercial"
        "Venado Tuerto -Gerente de Ventas importante Concesionario" -> "Gerente de Ventas"
        "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10..." -> "Operarios industria Alimenticia"
    """
    if not titulo:
        return titulo

    if config is None:
        config = _CONFIG

    original = titulo

    # 0a. Eliminar codigos alfanumericos AL INICIO (671SI, ABC123, REF-12345)
    for patron_info in config.get("codigos_inicio", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo)

    # 0a1. [v2.5.1] Eliminar codigos de empresa (631 BE |, BE |)
    for patron_info in config.get("codigos_empresa", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo)

    # 0a2. Eliminar prefijos genericos (Busqueda Laboral:, Se busca:, etc)
    for patron_info in config.get("prefijos_genericos", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 0b. Eliminar ubicaciones AL INICIO del titulo
    ciudades = config.get("ciudades_inicio", {}).get("lista", [])
    for ciudad in ciudades:
        titulo = re.sub(rf'^{re.escape(ciudad)}\s*[-–]\s*', '', titulo, flags=re.IGNORECASE)

    # 0c. Eliminar info administrativa (fechas, presentaciones, sucursales)
    for patron_info in config.get("info_administrativa", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 1. Eliminar codigos de referencia
    for patron_info in config.get("codigos_referencia", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 1b. [v2.6.3] Eliminar modalidad + ubicación COMBINADOS (eventual MAR DEL PLATA)
    # DEBE ejecutarse ANTES de modalidad_final para capturar el bloque completo
    for patron_info in config.get("modalidad_ubicacion_combinado", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 2. Eliminar palabras de modalidad al final
    modalidades = config.get("modalidad_final", {}).get("palabras", [])
    if modalidades:
        modalidad_pattern = '|'.join(re.escape(m) for m in modalidades)
        titulo = re.sub(rf'\s*\(?\s*({modalidad_pattern})\s*\)?$', '', titulo, flags=re.IGNORECASE)

    # 3. Eliminar zonas/ubicaciones al final
    for patron_info in config.get("zonas_ubicaciones", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 3b. Eliminar localidades especificas al final (- Caballito, - Belgrano, etc)
    localidades = config.get("localidades_final", {}).get("lista", [])
    for localidad in localidades:
        # Patron: " - Localidad" al final del titulo (con guion normal o largo)
        titulo = re.sub(rf'\s*[-–—]\s*{re.escape(localidad)}$', '', titulo, flags=re.IGNORECASE)

    # 4. Eliminar ubicacion con guion (– Vicente López)
    for patron_info in config.get("ubicacion_con_guion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo)

    # 4b. Eliminar contexto + ubicacion (para farmacias en Rio Cuarto)
    for patron_info in config.get("contexto_ubicacion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 4c. [v2.5] Eliminar ubicaciones SIN guion al final (CABA, Tucumán, etc)
    for patron_info in config.get("ubicacion_sin_guion_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 5. Eliminar parentesis especificos
    for patron_info in config.get("parentesis_eliminar", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6. Eliminar texto despues de guion que sea contexto empresarial
    palabras_contexto = config.get("contexto_empresarial", {}).get("palabras", [])
    for palabra in palabras_contexto:
        # Requiere espacios alrededor del guión (evita "DI-Vendedor") + word boundary (evita "Industrial" por "industria")
        titulo = re.sub(rf'\s+[-–—]\s+[^-]*\b{re.escape(palabra)}\b[^-]*$', '', titulo, flags=re.IGNORECASE)

    # 6a2. [v2.4] Eliminar contexto empresarial SIN guion (para Empresa de X)
    for patron_info in config.get("contexto_empresarial_sin_guion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6c. [v2.2] Eliminar codigos numericos al FINAL (- 1729, - 4521)
    for patron_info in config.get("codigos_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6c2. [v2.4] Eliminar contexto complejo (- Laboratorio X - Turno Y - CABA)
    for patron_info in config.get("contexto_complejo", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6d. [v2.2] Eliminar modalidad con guion (- Remoto - CABA, - Mix (On Site & Remoto))
    for patron_info in config.get("modalidad_guion", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6e. [v2.2] Eliminar requisitos de edad (+45 años, 25-35 años)
    for patron_info in config.get("requisitos_edad", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6e2. [v2.5] Eliminar turno al final (Turno tarde, Turno mañana)
    for patron_info in config.get("turno_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6f. [v2.2] Eliminar ubicaciones con guion - extendido
    for patron_info in config.get("ubicacion_guion_extendido", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 6b. Eliminar preposiciones sueltas al final
    preposiciones = config.get("preposiciones_final", {}).get("palabras", [])
    if preposiciones:
        prep_pattern = '|'.join(re.escape(p) for p in preposiciones)
        titulo = re.sub(rf'\s+({prep_pattern})\s*$', '', titulo, flags=re.IGNORECASE)

    # 6b2. [v2.5.1] Eliminar pipes y contenido entre pipes al final
    for patron_info in config.get("pipes_limpiar", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # 7. Expandir/eliminar abreviaturas (al final para que no interfiera con contexto_empresarial)
    for patron_info in config.get("abreviaturas_expandir", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        reemplazo = patron_info.get("reemplazo", "")
        if patron:
            titulo = re.sub(patron, reemplazo, titulo, flags=re.IGNORECASE)

    # 8. Limpieza final
    for patron_info in config.get("limpieza_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        reemplazo = patron_info.get("reemplazo", "")
        if patron:
            titulo = re.sub(patron, reemplazo, titulo)

    titulo = titulo.strip()

    # 8b. [v2.8.1] Second pass: re-run location/zona/modalidad cleanup
    # Steps 2-3b run BEFORE contexto_empresarial (step 6) which exposes trailing locations
    # limpieza_final (step 8) removes trailing dashes that blocked ubicacion_guion_extendido
    # Result: zona/city/modalidad patterns left at the end that were missed in first pass

    # Re-run modalidad_final (was step 2)
    if modalidades:
        titulo = re.sub(rf'\s*\(?\s*({modalidad_pattern})\s*\)?$', '', titulo, flags=re.IGNORECASE)

    # Re-run zonas_ubicaciones (was step 3)
    for patron_info in config.get("zonas_ubicaciones", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # Re-run localidades_final (was step 3b)
    for localidad in localidades:
        titulo = re.sub(rf'\s*[-–—]\s*{re.escape(localidad)}$', '', titulo, flags=re.IGNORECASE)

    # Re-run ubicacion_sin_guion_final (was step 4c)
    for patron_info in config.get("ubicacion_sin_guion_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # Re-run ubicacion_guion_extendido (was step 6f)
    for patron_info in config.get("ubicacion_guion_extendido", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        if patron:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)

    # Re-run contexto_empresarial (was step 6) — exposed after GBA/localidades removed in second pass
    for palabra in palabras_contexto:
        titulo = re.sub(rf'\s+[-–—]\s+[^-]*\b{re.escape(palabra)}\b[^-]*$', '', titulo, flags=re.IGNORECASE)

    # Re-run preposiciones sueltas (was step 6b)
    if preposiciones:
        titulo = re.sub(rf'\s+({prep_pattern})\s*$', '', titulo, flags=re.IGNORECASE)

    # Re-run limpieza_final for trailing junk from second pass
    for patron_info in config.get("limpieza_final", {}).get("patrones", []):
        patron = patron_info.get("patron", "")
        reemplazo = patron_info.get("reemplazo", "")
        if patron:
            titulo = re.sub(patron, reemplazo, titulo)

    titulo = titulo.strip()

    # 9. [v2.8] Safety guard: si limpieza destruyó el título, usar original
    min_length = config.get("safety", {}).get("min_length", 5)
    if len(titulo) < min_length and len(original.strip()) >= min_length:
        titulo = original.strip()

    # 10. [v2.6] Normalizar capitalización a Sentence case
    titulo = normalizar_capitalizacion(titulo)

    return titulo


def detectar_multi_perfil(titulo: str, config: Dict[str, Any] = None) -> List[str]:
    """
    Detecta si un titulo tiene multiples perfiles y los separa.

    Args:
        titulo: Titulo (ya limpio) de la oferta
        config: Config opcional

    Returns:
        Lista de perfiles si es multi-perfil, lista con titulo original si no

    Ejemplos:
        "CAJEROS, BARISTAS, COCINEROS" -> ["CAJEROS", "BARISTAS", "COCINEROS"]
        "Desarrollador Python" -> ["Desarrollador Python"]
        "AUTOS OKM, USADOS" -> ["AUTOS OKM, USADOS"] (no es multi-perfil)
        "Cajero/a" -> ["Cajero/a"] (género inclusivo, NO es multi-perfil)
        "CAJERO/ENCARGADO" -> ["CAJERO", "ENCARGADO"] (candidato a multi-perfil)
    """
    if not titulo:
        return [titulo] if titulo else []

    if config is None:
        config = _CONFIG

    multi_config = config.get("multi_perfil", {})
    separadores = multi_config.get("separadores", [", "])
    min_perfiles = multi_config.get("min_perfiles", 2)
    min_largo_perfil = multi_config.get("min_largo_perfil", 5)
    no_ocupacion = multi_config.get("no_ocupacion", [])

    # Patrones de género inclusivo que NO son multi-perfil
    # Ej: "Vendedor/a", "Cajeros/as", "Operario/a"
    patrones_genero = [
        r'/a\b', r'/as\b', r'/o\b', r'/os\b',  # Vendedor/a, Cajeros/as
        r'o/a\b', r'os/as\b', r'a/o\b', r'as/os\b',  # Vendedor o/a
        r'\(a\)', r'\(o\)', r'\(as\)', r'\(os\)',  # Vendedor(a)
    ]

    # Verificar si es patrón de género inclusivo
    import re
    for patron in patrones_genero:
        if re.search(patron, titulo, re.IGNORECASE):
            # Es género inclusivo, no multi-perfil
            return [titulo]

    # Probar cada separador en orden de prioridad
    for sep in separadores:
        if sep not in titulo:
            continue

        perfiles = [p.strip() for p in titulo.split(sep)]
        # Filtrar perfiles vacíos o muy cortos
        perfiles = [p for p in perfiles if len(p) >= 3]

        if len(perfiles) < min_perfiles:
            continue

        # Verificar que los items parezcan ocupaciones
        perfiles_validos = []
        for perfil in perfiles:
            perfil_lower = perfil.lower()
            # Excluir si contiene palabras que no son ocupaciones
            es_ocupacion = True
            for palabra in no_ocupacion:
                if palabra in perfil_lower:
                    es_ocupacion = False
                    break
            # Excluir si es muy corto y no es mayúsculas
            if len(perfil) < min_largo_perfil and not perfil.isupper():
                es_ocupacion = False
            if es_ocupacion:
                perfiles_validos.append(perfil)

        # Solo es multi-perfil si al menos min_perfiles son válidos
        if len(perfiles_validos) >= min_perfiles:
            return perfiles_validos

    # Ningún separador funcionó, devolver titulo original
    return [titulo]


# Configuración LLM para validación multi-perfil
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434/api/generate"
# Modelo optimizado: 7b es suficiente para extracción JSON (3x más rápido que 14b)
OLLAMA_MODEL = "qwen2.5:7b"


def validar_multi_perfil_con_llm(
    titulo: str,
    descripcion: str,
    perfiles_candidatos: List[str],
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Valida con LLM si un título realmente representa múltiples perfiles.

    Analiza el título + descripción para determinar si la empresa busca:
    - MÚLTIPLES PERFILES: personas para posiciones DIFERENTES
    - UN SOLO PERFIL: una persona polivalente con múltiples habilidades

    Args:
        titulo: Título de la oferta
        descripcion: Descripción completa de la oferta
        perfiles_candidatos: Lista de perfiles detectados por regex
        timeout: Timeout en segundos para la llamada LLM

    Returns:
        {
            "es_multiple_perfil": bool,
            "perfiles_confirmados": List[str],
            "razon": str,
            "confianza": float
        }
    """
    prompt = f"""Analiza esta oferta laboral y determina si busca MÚLTIPLES PERFILES DISTINTOS
o UN SOLO PERFIL con múltiples habilidades/tareas.

TÍTULO: {titulo}
PERFILES DETECTADOS POR REGEX: {perfiles_candidatos}

DESCRIPCIÓN (extracto):
{descripcion[:1500] if descripcion else "(sin descripción)"}

---

CRITERIOS:
1. ES MÚLTIPLE PERFIL (es_multiple_perfil=true) si:
   - Buscan personas para POSICIONES/PUESTOS DIFERENTES
   - Mencionan vacantes separadas ("cajero y encargado para diferentes turnos")
   - Hay referencias a múltiples roles independientes

2. NO ES MÚLTIPLE PERFIL (es_multiple_perfil=false) si:
   - Buscan UNA persona que haga varias tareas
   - Es un perfil "polivalente", "multitarea", "integral"
   - Las palabras separadas son especializaciones del mismo rol
   - Ejemplo: "Vendedor Electrónica y Electrodomésticos" = 1 vendedor con 2 rubros
   - Ejemplo: "Desarrollador Python y Java" = 1 desarrollador que sepa ambos

Responde SOLO con JSON válido (sin texto adicional):
{{
    "es_multiple_perfil": true o false,
    "perfiles_confirmados": ["Perfil1", "Perfil2"] si es múltiple, o ["{titulo}"] si es uno solo,
    "razon": "explicación breve de 1 línea",
    "confianza": 0.0 a 1.0
}}"""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Bajo para respuestas consistentes
                "num_predict": 256,
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        text = result.get("response", "").strip()

        # Parsear JSON de la respuesta
        # Buscar el JSON en la respuesta (puede tener texto antes/después)
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "es_multiple_perfil": parsed.get("es_multiple_perfil", False),
                "perfiles_confirmados": parsed.get("perfiles_confirmados", [titulo]),
                "razon": parsed.get("razon", ""),
                "confianza": float(parsed.get("confianza", 0.5))
            }
        else:
            print(f"[WARN] No se encontró JSON en respuesta LLM: {text[:200]}")
            # Fallback: asumir que NO es múltiple (más conservador)
            return {
                "es_multiple_perfil": False,
                "perfiles_confirmados": [titulo],
                "razon": "No se pudo parsear respuesta LLM",
                "confianza": 0.0
            }

    except requests.exceptions.Timeout:
        print(f"[WARN] Timeout validando multi-perfil para: {titulo[:50]}")
        return {
            "es_multiple_perfil": False,
            "perfiles_confirmados": [titulo],
            "razon": "Timeout LLM",
            "confianza": 0.0
        }
    except Exception as e:
        print(f"[ERROR] Error validando multi-perfil: {e}")
        return {
            "es_multiple_perfil": False,
            "perfiles_confirmados": [titulo],
            "razon": f"Error: {str(e)}",
            "confianza": 0.0
        }


def descomponer_multi_perfil_con_llm(
    titulo: str,
    descripcion: str,
    tareas: str = None,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    LLM analiza la oferta COMPLETA y descompone en posiciones individuales.

    A diferencia de validar_multi_perfil_con_llm (que confirma candidatos regex),
    esta función DESCUBRE posiciones desde la descripción.

    Returns:
        {
            "es_multi": bool,
            "posiciones": [
                {"titulo": "Jefe de Mantenimiento Mecánico", "tareas": "Liderar mant...;Garantizar..."},
                {"titulo": "Jefe de Calidad", "tareas": "Implementar SGC...;Gestionar cert..."}
            ],
            "razon": str,
            "confianza": float
        }
    """
    desc_truncado = (descripcion or "")[:2000]
    tareas_texto = f"\nTAREAS EXTRAÍDAS: {tareas[:500]}" if tareas else ""

    prompt = f"""Analiza esta oferta laboral y determina si contiene MÚLTIPLES POSICIONES/PUESTOS DISTINTOS.

TÍTULO: {titulo}
{tareas_texto}

DESCRIPCIÓN:
{desc_truncado}

---

INSTRUCCIONES:
1. Lee toda la descripción buscando puestos/posiciones/roles DIFERENTES
2. Si hay múltiples posiciones, separá cada una con su título y tareas específicas
3. Las tareas de cada posición deben estar separadas por punto y coma (;)
4. Si es UNA SOLA posición (persona polivalente), indicar es_multi=false

CRITERIOS para MÚLTIPLE POSICIÓN:
- La descripción menciona puestos/cargos distintos explícitamente
- Hay secciones separadas para cada rol
- Título tiene separadores (/, y, |) entre cargos de diferente nivel/área

CRITERIOS para posición ÚNICA:
- Una persona con múltiples tareas/habilidades
- Especialización dual del mismo rol (ej: "Vendedor Electrónica y Electrodomésticos")
- Género inclusivo (ej: "Cajero/a")

Responde SOLO con JSON válido:
{{
    "es_multi": true o false,
    "posiciones": [
        {{"titulo": "Título del puesto 1", "tareas": "tarea1;tarea2;tarea3"}},
        {{"titulo": "Título del puesto 2", "tareas": "tarea1;tarea2"}}
    ],
    "razon": "explicación breve",
    "confianza": 0.0 a 1.0
}}

Si es posición única, devolver una sola posición en el array."""

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 512,
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        text = result.get("response", "").strip()

        # Buscar JSON en la respuesta (puede tener texto antes/después)
        # Intentar encontrar el JSON completo con arrays anidados
        json_start = text.find('{')
        if json_start >= 0:
            # Encontrar el cierre correspondiente
            depth = 0
            for i in range(json_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        json_str = text[json_start:i + 1]
                        break
            else:
                json_str = text[json_start:]

            parsed = json.loads(json_str)

            posiciones = parsed.get("posiciones", [])
            confianza = float(parsed.get("confianza", 0.5))

            # Validar: necesita >= 2 posiciones para ser multi
            es_multi = parsed.get("es_multi", False) and len(posiciones) >= 2

            return {
                "es_multi": es_multi,
                "posiciones": posiciones if es_multi else [{"titulo": titulo, "tareas": tareas or ""}],
                "razon": parsed.get("razon", ""),
                "confianza": confianza
            }

        print(f"[WARN] No se encontró JSON en respuesta LLM decompose: {text[:200]}")
        return {
            "es_multi": False,
            "posiciones": [{"titulo": titulo, "tareas": tareas or ""}],
            "razon": "No se pudo parsear respuesta LLM",
            "confianza": 0.0
        }

    except requests.exceptions.Timeout:
        print(f"[WARN] Timeout descomponiendo multi-perfil para: {titulo[:50]}")
        return {
            "es_multi": False,
            "posiciones": [{"titulo": titulo, "tareas": tareas or ""}],
            "razon": "Timeout LLM",
            "confianza": 0.0
        }
    except Exception as e:
        print(f"[ERROR] Error descomponiendo multi-perfil: {e}")
        return {
            "es_multi": False,
            "posiciones": [{"titulo": titulo, "tareas": tareas or ""}],
            "razon": f"Error: {str(e)}",
            "confianza": 0.0
        }


def expandir_ofertas_multi_perfil(ids: List[str] = None, dry_run: bool = True, usar_llm: bool = True):
    """
    Expande ofertas con multiples perfiles en registros separados.

    Detección híbrida:
    1. Regex en título (detectar_multi_perfil) → candidatos obvios
    2. Regex en descripción (patrones_descripcion) → candidatos por contenido
    3. LLM decompose → descubre y descompone posiciones con tareas

    Cada perfil genera un nuevo registro con id_oferta derivado:
    - Original: 2123908 (se marca como parent, multi_position_status='expanded')
    - Expandidos: 2123908_2, 2123908_3, etc. (es_suboferta=1, parent_id_oferta=2123908)

    Args:
        ids: Lista de IDs a procesar (None = Gold Set)
        dry_run: Si True, solo muestra qué haría sin modificar BD
        usar_llm: Si True, usa LLM para descomponer posiciones (título + descripción)

    Returns:
        Dict con estadísticas e ids_nuevos
    """
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    multi_config = _CONFIG.get("multi_perfil", {})
    min_confianza = multi_config.get("llm_decompose", {}).get("min_confianza", 0.7)
    patrones_desc = multi_config.get("patrones_descripcion", [])
    patrones_titulo_sosp = multi_config.get("patrones_titulo_sospechoso", [])

    # Cargar IDs
    if ids is None:
        gold_set_100 = base / 'gold_set_nlp_100_ids.json'
        gold_set_49 = base / 'gold_set_manual_v2.json'

        if gold_set_100.exists():
            with open(gold_set_100, 'r', encoding='utf-8') as f:
                ids = json.load(f)
        else:
            with open(gold_set_49, 'r', encoding='utf-8') as f:
                gold_set = json.load(f)
            ids = [str(x['id_oferta']) for x in gold_set]

    # Filtrar sub-ofertas ya existentes (no reprocesar)
    ids = [str(i) for i in ids if '_' not in str(i)]

    print(f"Buscando ofertas multi-perfil en {len(ids)} ofertas...")
    print(f"Validación LLM: {'ACTIVADA' if usar_llm else 'DESACTIVADA'}")
    print("-" * 70)

    # Obtener datos de ofertas_nlp (excluir ya expandidas)
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT n.*
        FROM ofertas_nlp n
        WHERE n.id_oferta IN ({placeholders})
        AND (n.multi_position_status IS NULL OR n.multi_position_status NOT IN ('expanded', 'single'))
    """, ids)

    rows = c.fetchall()
    columnas = [desc[0] for desc in c.description]

    if not rows:
        print("No hay ofertas pendientes de evaluación multi-posición.")
        conn.close()
        return {'multi_perfil': 0, 'nuevos': 0, 'aplicado': False, 'ids_nuevos': []}

    # Obtener descripciones y tareas de tabla ofertas + ofertas_nlp
    descripciones = {}
    tareas_map = {}
    c.execute(f"""
        SELECT o.id_oferta, o.descripcion, n.tareas_explicitas
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE o.id_oferta IN ({placeholders})
    """, ids)
    for row in c.fetchall():
        descripciones[str(row[0])] = row[1] or ""
        tareas_map[str(row[0])] = row[2] or ""

    ofertas_expandir = []
    ofertas_single = []
    ofertas_rechazadas = []
    total_nuevos = 0
    ids_creados = []

    for row in rows:
        row_dict = dict(zip(columnas, row))
        id_oferta = str(row_dict['id_oferta'])
        titulo_limpio = row_dict.get('titulo_limpio') or ''
        descripcion = descripciones.get(id_oferta, "")
        tareas = tareas_map.get(id_oferta, "")

        # --- Paso 1: Detección por regex en título ---
        perfiles_regex = detectar_multi_perfil(titulo_limpio)
        es_candidato_titulo = len(perfiles_regex) > 1

        # --- Paso 2: Detección por regex en descripción ---
        es_candidato_desc = False
        for patron in patrones_desc:
            if re.search(patron, descripcion, re.IGNORECASE):
                es_candidato_desc = True
                break

        # --- Paso 2b: Detección por patrones sospechosos en título ---
        if not es_candidato_titulo and not es_candidato_desc:
            for patron in patrones_titulo_sosp:
                if re.search(patron, titulo_limpio, re.IGNORECASE):
                    es_candidato_desc = True  # Tratar como candidato para LLM
                    break

        es_candidato = es_candidato_titulo or es_candidato_desc

        if not es_candidato:
            ofertas_single.append(id_oferta)
            continue

        # --- Paso 3: Resolución (regex-only o LLM) ---
        if usar_llm:
            # LLM decompose: descubre posiciones desde título + descripción + tareas
            resultado_llm = descomponer_multi_perfil_con_llm(
                titulo_limpio, descripcion, tareas
            )

            if resultado_llm["es_multi"] and resultado_llm["confianza"] >= min_confianza:
                posiciones = resultado_llm["posiciones"]
                metodo = "LLM_DECOMPOSE"
                print(f"  {id_oferta}: {len(posiciones)} posiciones [{metodo}] (conf={resultado_llm['confianza']:.2f})")
                print(f"    Razón: {resultado_llm['razon']}")
            else:
                # LLM dice NO o baja confianza
                ofertas_rechazadas.append({
                    'id': id_oferta,
                    'titulo': titulo_limpio,
                    'razon': resultado_llm['razon'],
                    'confianza': resultado_llm['confianza'],
                    'fuente': 'titulo' if es_candidato_titulo else 'descripcion'
                })
                ofertas_single.append(id_oferta)
                print(f"  {id_oferta}: SINGLE [{resultado_llm['razon'][:60]}] (conf={resultado_llm['confianza']:.2f})")
                continue
        else:
            if not es_candidato_titulo:
                # Sin LLM, solo regex en título puede confirmar
                ofertas_single.append(id_oferta)
                continue
            # Usar perfiles del regex como posiciones (sin tareas splitteadas)
            posiciones = [{"titulo": p, "tareas": tareas} for p in perfiles_regex]
            metodo = "REGEX"
            print(f"  {id_oferta}: {len(posiciones)} posiciones [{metodo}]")

        ofertas_expandir.append({
            'id_original': id_oferta,
            'posiciones': posiciones,
            'row_dict': row_dict,
            'metodo': metodo
        })
        total_nuevos += len(posiciones) - 1  # -1 porque el original ya existe
        for i, p in enumerate(posiciones, 1):
            titulo_pos = p.get('titulo', '?')
            tareas_pos = (p.get('tareas', '') or '')[:50]
            print(f"    {id_oferta}{'_' + str(i) if i > 1 else ''}: {titulo_pos} | {tareas_pos}...")
        print()

    print(f"\nResumen:")
    print(f"  Ofertas multi-posición confirmadas: {len(ofertas_expandir)}")
    print(f"  Ofertas single (confirmadas): {len(ofertas_single)}")
    print(f"  Rechazadas por LLM: {len(ofertas_rechazadas)}")
    print(f"  Registros nuevos a crear: {total_nuevos}")

    if ofertas_rechazadas:
        print(f"\n  Rechazos (NO son multi-posición):")
        for r in ofertas_rechazadas[:5]:
            print(f"    - {r['id']}: {r['titulo'][:40]}... -> {r['razon'][:50]}")
        if len(ofertas_rechazadas) > 5:
            print(f"    ... y {len(ofertas_rechazadas) - 5} más")

    if dry_run:
        print(f"\n[DRY RUN] No se modificó la BD. Usar dry_run=False para aplicar.")
        conn.close()
        return {
            'multi_perfil': len(ofertas_expandir),
            'rechazados_llm': len(ofertas_rechazadas),
            'nuevos': total_nuevos,
            'aplicado': False,
            'ids_nuevos': [],
            'rechazos_detalle': ofertas_rechazadas
        }

    # Aplicar cambios
    print(f"\nAplicando cambios...")

    # Marcar ofertas single
    for id_s in ofertas_single:
        c.execute(
            "UPDATE ofertas_nlp SET multi_position_status = 'single' WHERE id_oferta = ?",
            (id_s,)
        )

    for oferta in ofertas_expandir:
        id_original = oferta['id_original']
        posiciones = oferta['posiciones']
        row_dict = oferta['row_dict']

        # Actualizar registro original: primer perfil + marcar como expanded
        primer_titulo = posiciones[0].get('titulo', row_dict.get('titulo_limpio', ''))
        primer_tareas = posiciones[0].get('tareas', '')

        update_fields = {
            'titulo_limpio': primer_titulo,
            'multi_position_status': 'expanded'
        }
        if primer_tareas:
            update_fields['tareas_explicitas'] = primer_tareas

        set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
        c.execute(
            f"UPDATE ofertas_nlp SET {set_clause} WHERE id_oferta = ?",
            list(update_fields.values()) + [id_original]
        )

        # Crear registros nuevos para posiciones adicionales
        for i, pos in enumerate(posiciones[1:], 2):
            nuevo_id = f"{id_original}_{i}"
            ids_creados.append(nuevo_id)

            # Copiar todos los campos del original
            campos = [col for col in columnas]
            valores = []
            for col in campos:
                if col == 'id_oferta':
                    valores.append(nuevo_id)
                elif col == 'titulo_limpio':
                    valores.append(pos.get('titulo', ''))
                elif col == 'tareas_explicitas' and pos.get('tareas'):
                    valores.append(pos['tareas'])
                elif col == 'parent_id_oferta':
                    valores.append(str(id_original))
                elif col == 'es_suboferta':
                    valores.append(1)
                elif col == 'numero_suboferta':
                    valores.append(i)
                elif col == 'multi_position_status':
                    valores.append('expanded')
                else:
                    valores.append(row_dict[col])

            placeholders_insert = ','.join(['?' for _ in campos])
            campos_str = ','.join(campos)

            try:
                c.execute(f"INSERT INTO ofertas_nlp ({campos_str}) VALUES ({placeholders_insert})", valores)
            except sqlite3.IntegrityError:
                # Ya existe, actualizar campos clave
                c.execute("""
                    UPDATE ofertas_nlp
                    SET titulo_limpio = ?, tareas_explicitas = ?,
                        parent_id_oferta = ?, es_suboferta = 1,
                        numero_suboferta = ?, multi_position_status = 'expanded'
                    WHERE id_oferta = ?
                """, (pos.get('titulo', ''), pos.get('tareas', ''),
                      str(id_original), i, nuevo_id))

    conn.commit()
    print(f"[OK] Expandidas {len(ofertas_expandir)} ofertas, creados {len(ids_creados)} registros nuevos")
    conn.close()

    return {
        'multi_perfil': len(ofertas_expandir),
        'nuevos': len(ids_creados),
        'aplicado': True,
        'ids_nuevos': ids_creados
    }


def agregar_columna_titulo_limpio():
    """Agrega columna titulo_limpio a ofertas_nlp si no existe"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    c = conn.cursor()

    c.execute("PRAGMA table_info(ofertas_nlp)")
    columnas = [col[1] for col in c.fetchall()]

    if 'titulo_limpio' not in columnas:
        print("Agregando columna titulo_limpio a ofertas_nlp...")
        c.execute("ALTER TABLE ofertas_nlp ADD COLUMN titulo_limpio TEXT")
        conn.commit()
        print("  [OK] Columna agregada")
    else:
        print("  [OK] Columna titulo_limpio ya existe")

    conn.close()


def procesar_gold_set():
    """Procesa titulos del Gold Set y guarda titulo_limpio"""
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Cargar IDs del Gold Set (usar expandido si existe)
    gold_set_100 = base / 'gold_set_nlp_100_ids.json'
    gold_set_49 = base / 'gold_set_manual_v2.json'

    if gold_set_100.exists():
        with open(gold_set_100, 'r', encoding='utf-8') as f:
            ids = json.load(f)
        print(f"Usando Gold Set expandido: {len(ids)} ofertas")
    else:
        with open(gold_set_49, 'r', encoding='utf-8') as f:
            gold_set = json.load(f)
        ids = [str(x['id_oferta']) for x in gold_set]
        print(f"Usando Gold Set original: {len(ids)} ofertas")

    print(f"\nProcesando {len(ids)} titulos...")
    print("-" * 70)

    # Obtener titulos
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT o.id_oferta, o.titulo
        FROM ofertas o
        WHERE o.id_oferta IN ({placeholders})
    """, ids)

    resultados = []
    cambios = 0

    for row in c.fetchall():
        id_oferta = row['id_oferta']
        titulo_original = row['titulo'] or ''
        titulo_limpio = limpiar_titulo(titulo_original)

        # Mostrar cambios
        if titulo_limpio != titulo_original:
            cambios += 1
            if cambios <= 10:  # Solo mostrar primeros 10
                print(f"  {id_oferta}:")
                print(f"    ANTES:  {titulo_original[:60]}")
                print(f"    DESPUES:{titulo_limpio[:60]}")
                print()

        resultados.append((titulo_limpio, str(id_oferta)))

    # Actualizar BD
    print(f"\nActualizando {len(resultados)} registros en ofertas_nlp...")
    c.executemany("""
        UPDATE ofertas_nlp
        SET titulo_limpio = ?
        WHERE id_oferta = ?
    """, resultados)
    conn.commit()

    print(f"\n[OK] {cambios}/{len(resultados)} titulos modificados")
    conn.close()

    return cambios


def regenerar_titulo_limpio(ids=None, dry_run=True):
    """
    Regenera titulo_limpio para ofertas existentes.
    NO toca matching, NLP, ni validación.

    Args:
        ids: Lista de IDs (None = todas las ofertas con NLP)
        dry_run: Si True, solo muestra cambios sin escribir BD

    Returns:
        Dict con estadísticas de cambios
    """
    conn = sqlite3.connect(base / 'bumeran_scraping.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Obtener ofertas
    if ids:
        placeholders = ','.join(['?' for _ in ids])
        c.execute(f"""
            SELECT o.id_oferta, o.titulo, n.titulo_limpio
            FROM ofertas o
            JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
            WHERE o.id_oferta IN ({placeholders})
        """, [str(i) for i in ids])
    else:
        c.execute("""
            SELECT o.id_oferta, o.titulo, n.titulo_limpio
            FROM ofertas o
            JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        """)

    rows = c.fetchall()
    print(f"Regenerando titulo_limpio para {len(rows)} ofertas...")
    print(f"Modo: {'DRY RUN (sin escribir BD)' if dry_run else 'APLICAR CAMBIOS'}")
    print("-" * 70)

    cambios = []
    warnings = []
    sin_cambio = 0

    for row in rows:
        id_oferta = row['id_oferta']
        titulo_original = row['titulo'] or ''
        titulo_limpio_actual = row['titulo_limpio'] or ''

        # Aplicar limpieza con config actual
        titulo_limpio_nuevo = limpiar_titulo(titulo_original)

        if titulo_limpio_nuevo == titulo_limpio_actual:
            sin_cambio += 1
            continue

        # Detectar regresiones: si el nuevo es < 50% del anterior
        len_actual = len(titulo_limpio_actual)
        len_nuevo = len(titulo_limpio_nuevo)
        es_regresion = len_actual > 0 and len_nuevo < len_actual * 0.5

        cambio = {
            'id': id_oferta,
            'antes': titulo_limpio_actual,
            'despues': titulo_limpio_nuevo,
            'chars_diff': len_nuevo - len_actual,
            'regresion': es_regresion
        }
        cambios.append(cambio)

        if es_regresion:
            warnings.append(cambio)

    # Reporte
    print(f"\nResultados:")
    print(f"  Sin cambio: {sin_cambio}")
    print(f"  Con cambio: {len(cambios)}")
    print(f"  Warnings (regresión): {len(warnings)}")

    if cambios:
        # Mostrar primeros 20 cambios
        print(f"\nCambios (primeros {min(20, len(cambios))}):")
        for c_info in cambios[:20]:
            flag = " ⚠️ REGRESIÓN" if c_info['regresion'] else ""
            print(f"  {c_info['id']}:{flag}")
            print(f"    ANTES:  {c_info['antes'][:60]}")
            print(f"    DESPUÉS:{c_info['despues'][:60]}")
            print(f"    Δ chars: {c_info['chars_diff']:+d}")

    if warnings:
        print(f"\n⚠️  REGRESIONES DETECTADAS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w['id']}: '{w['antes'][:40]}' → '{w['despues'][:40]}' (Δ{w['chars_diff']:+d})")

    if dry_run:
        print(f"\n[DRY RUN] No se modificó la BD. Usar --apply para aplicar.")
        conn.close()
        return {'cambios': len(cambios), 'sin_cambio': sin_cambio, 'warnings': len(warnings), 'aplicado': False}

    # Aplicar cambios (excluyendo regresiones)
    cambios_aplicar = [c_info for c_info in cambios if not c_info['regresion']]
    cambios_excluidos = len(cambios) - len(cambios_aplicar)

    if cambios_excluidos > 0:
        print(f"\n⚠️  Excluyendo {cambios_excluidos} regresiones del update.")

    cursor = conn.cursor()
    for c_info in cambios_aplicar:
        cursor.execute(
            "UPDATE ofertas_nlp SET titulo_limpio = ? WHERE id_oferta = ?",
            (c_info['despues'], str(c_info['id']))
        )
    conn.commit()

    print(f"\n[OK] Actualizados {len(cambios_aplicar)} títulos en BD")
    if cambios_excluidos > 0:
        print(f"[SKIP] {cambios_excluidos} regresiones NO aplicadas (revisar manualmente)")
    conn.close()

    return {
        'cambios': len(cambios_aplicar),
        'sin_cambio': sin_cambio,
        'warnings': len(warnings),
        'excluidos': cambios_excluidos,
        'aplicado': True
    }


# Test standalone
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Limpieza de títulos v2.8.1')
    parser.add_argument('--regenerar', action='store_true', help='Regenerar titulo_limpio para ofertas existentes')
    parser.add_argument('--ids', type=str, help='IDs específicos (comma-separated)')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (sin esto es dry_run)')
    args = parser.parse_args()

    if args.regenerar:
        ids_list = [x.strip() for x in args.ids.split(',')] if args.ids else None
        regenerar_titulo_limpio(ids=ids_list, dry_run=not args.apply)
        exit(0)

    print("=" * 70)
    print("LIMPIEZA DE TITULOS v2.8 - Config desde JSON")
    print("=" * 70)

    # Mostrar config cargada
    print(f"\nConfig cargada: {len(_CONFIG)} secciones")
    for key in _CONFIG:
        if not key.startswith('_'):
            print(f"  - {key}")

    # Tests unitarios
    print("\nTESTS UNITARIOS:")
    print("-" * 70)
    tests = [
        # Sentence case + acrónimos preservados (v2.7)
        ("Gerente de Operaciones - Gastronomia corporativa y Facility management", "Gerente de operaciones"),
        ("Analista de Cultivo - Roque Perez - BA", "Analista de cultivo"),
        ("Representante Comercial (Consumo Masivo / Grandes Cuentas)", "Representante comercial"),
        ("Operario de Almacen/Logistica Z/Escobar", "Operario de almacen/logistica"),
        ("Repositor/a Externo/a (Eventual) Moreno", "Repositor/a externo/a"),
        ("Administrativa Comercio Exterior (req199380) Eventual", "Administrativa comercio exterior"),
        # TODO: "importante Concesionario..." no se limpia - bug pre-existente en contexto_empresarial
        ("Venado Tuerto -Gerente de Ventas importante Concesionario Oficial Maquinaria Agricola", "Gerente de ventas importante concesionario oficial maquinaria agricola"),
        ("Gerente General para Maderera (PYME)", "Gerente general para maderera"),
        ("Vendedor con Experiencia (Corredor)", "Vendedor con experiencia"),
        ("Asistente Compliance (part time)", "Asistente compliance"),
        ("Chofer - Repartidor", "Chofer - repartidor"),
        ("Mozo/Moza", "Mozo/moza"),
        # Nuevos casos v2.0
        ("671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10 de 10 a 1130 NUEVA Suc. SAN ISIDRO", "Operarios industria alimenticia"),
        ("ABC123 Vendedor Jr", "Vendedor JR"),
        ("12345 Analista Contable", "Analista contable"),
        ("REF-9876 Cajero/a - Suc. Palermo", "Cajero/a"),
        ("Recepcionista - presentarse lunes 9hs", "Recepcionista"),
        # Casos v2.1 - prefijos y ubicaciones
        ("Búsqueda Laboral: Modelista – Vicente López (Florida Oeste)", "Modelista"),
        ("Se busca: Contador Junior", "Contador junior"),
        ("Buscamos Desarrollador Python", "Desarrollador python"),
        ("Farmacéutico/a para farmacias en Rio Cuarto", "Farmacéutico/a"),
        ("Vendedor en Mar del Plata", "Vendedor"),
        # Casos v2.1 - localidades con guion normal
        ("Personal de limpieza - Caballito", "Personal de limpieza"),
        ("Analista de Cuentas a Pagar - GBA Norte", "Analista de cuentas a pagar"),
        ("Vendedor - Zona Rosario", "Vendedor"),
        ("Arquitecto - Belgrano", "Arquitecto"),
        ("Contador - Roque Perez", "Contador"),
        # NO eliminar - son especializaciones, no ubicaciones
        ("Chofer - Repartidor", "Chofer - repartidor"),
        ("Abogado/a - Impuestos", "Abogado/a - impuestos"),
        # Casos v2.4 - detectados en dashboard 2026-01-28
        ("Administrativa/o para Cementerio en Zona Sur.", "Administrativa/o para cementerio"),
        ("Vendedora ambulante Playa Grande - Mar del Plata", "Vendedora ambulante"),
        ("Encargado/a para Empresa de Limpieza", "Encargado/a"),
        ("Analista para Consultora de RRHH", "Analista"),
        ("Operario para Industria Alimenticia", "Operario"),
        ("Contador para PYME", "Contador"),
        # Casos v2.7 - preservar acrónimos
        ("DBA Senior", "DBA senior"),
        ("SAP ABAP Consultor", "SAP ABAP consultor"),
        ("QA Tester", "QA tester"),
        ("PM Digital", "PM digital"),
        ("ANALISTA SQL SERVER", "Analista SQL server"),
        ("Desarrollador PHP Senior", "Desarrollador PHP senior"),
        # v2.8: Sobre-limpieza corregida
        ("DI-Vendedor/a Técnico/a de Almacenamiento Industrial para Zona AMBA y SUR",
         "Di-vendedor/a técnico/a de almacenamiento industrial"),
        ("Jefe De Sucursal para Santiago del Estero",
         "Jefe de sucursal"),
        ("Fullstack Ssr (Node, React, Typescript)",
         "Fullstack SSR (node, react, typescript)"),
        ("Herrero para industria plástica",
         "Herrero"),
        ("Cajera (EVENTUAL)",
         "Cajera"),
        # v2.8: Sub-limpieza corregida
        ("Cocinero/a especialista en pastas - restaurante en martinez (ref fel121)",
         "Cocinero/a especialista en pastas"),
        # v2.8: Cosméticos
        ("Soldador/a tig y mig, caba.",
         "Soldador/a tig y mig"),
        ("- clarkista con res 960 vigente",
         "Clarkista con res 960 vigente"),
        # v2.8: NO debe romper (regresión)
        ("Gerente de Operaciones - Gastronomia corporativa",
         "Gerente de operaciones"),
        # v2.8.1: Second pass — zona exposed after contexto_empresarial
        ("Encargado de Local Zona CABA - Grupo Gastronómico",
         "Encargado de local"),
        ("Cocinero Zona Caba - Importante Grupo Gastronómico",
         "Cocinero"),
        ("Operario de Producción - GBA SUR - Spegazzini",
         "Operario de producción"),
        ("Vendedor paquetes turísticos ZONA SUR (excluyente)",
         "Vendedor paquetes turísticos"),
        # v2.8.1: zona de trabajo residual
        ("Gestor/a de Cobranzas Telefónicas zona de trabajo Microcentro",
         "Gestor/a de cobranzas telefónicas"),
        # v2.8.1: - city exposed after trailing dash removed
        ("Ayudante de Cocina - Ezeiza-",
         "Ayudante de cocina"),
        ("Peón de Cocina - Córdoba -",
         "Peón de cocina"),
        ("Peón de Cocina - zona Balcarce-",
         "Peón de cocina"),
        # v2.8.1: modalidad exposed after parenthesis removed
        ("Vendedor/a de Salón de Tecnología Full Time (Buenos Aires)",
         "Vendedor/a de salón de tecnología"),
        # v2.8.1: // modalidad
        ("BACKEND Engineering Manager // Plataforma de Streaming // REMOTO para residentes en BUENOS AIRES",
         "Backend engineering manager // plataforma de streaming"),
        # v2.8.1: multi-pipe context
        ("BU705 ANALISTA CONTABLE JR | EVENTUAL | MULTINACIONAL | GESTIÓN DE ACTIVOS - GBA SUR - BURZACO",
         "Analista contable JR"),
        # v2.8.1: valid parentheses NOT removed (false positives)
        ("Operador de Contact Center (Representante Comercial Telefónico) Turno tarde",
         "Operador de contact center (representante comercial telefónico)"),
        ("Analista de Marketing y Comunicación (Marcom) - Part Time",
         "Analista de marketing y comunicación (marcom)"),
        ("Data Science (Python IA) - Remoto - 1731",
         "Data science (python IA)"),
        # v2.8.1: preposición "en" + ubicación, sucursal pegada con guión
        ("Asesor Técnico Comercial-Sucursal en CABA-.",
         "Asesor técnico comercial"),
        ("Cocinero/a de Cocina China para Hotel 5 Estrellas ubicado en Capital Federal (CABA).",
         "Cocinero/a de cocina china"),
    ]

    ok = 0
    for original, esperado in tests:
        resultado = limpiar_titulo(original)
        status = "OK" if resultado == esperado else "FAIL"
        if status == "OK":
            ok += 1
        print(f"  [{status}] {original[:50]}...")
        if status == "FAIL":
            print(f"       Esperado: {esperado}")
            print(f"       Obtenido: {resultado}")

    print(f"\nTests: {ok}/{len(tests)} OK")

    # Agregar columna y procesar
    print("\n" + "=" * 70)
    agregar_columna_titulo_limpio()
    procesar_gold_set()
