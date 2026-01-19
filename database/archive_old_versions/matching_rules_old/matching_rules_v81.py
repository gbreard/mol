#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
matching_rules_v81.py
=====================
Reglas de validacion para ESCO matching v8.1

Basado en analisis del gold set de 19 casos (2025-11-28):
- Precision base v8.0: 57.9% (11/19 correctos)
- Errores identificados:
  * sector_funcion: 4 casos (account exec -> agente empleo, etc)
  * nivel_jerarquico: 2 casos (vendedora -> director)
  * programa_general: 1 caso (pasantia -> disenador interiores)
  * tipo_ocupacion: 1 caso (farmaceutico -> ing. farmaceutico)
"""

from typing import Optional, Tuple

# =============================================================================
# REGLA 1: DETECCION DE NIVEL JERARQUICO
# =============================================================================

# Palabras clave para detectar nivel alto en titulo de oferta
PALABRAS_NIVEL_ALTA = [
    "director", "directora", "gerente", "jefe", "jefa",
    "head", "líder", "lider", "manager", "coordinador", "coordinadora",
    "supervisor", "supervisora", "chief", "cto", "ceo", "cfo", "coo"
]

# Palabras clave para detectar nivel medio
PALABRAS_NIVEL_MEDIA = [
    "analista", "ejecutivo", "ejecutiva", "account executive",
    "especialista", "asesor", "asesora", "representante", "senior", "sr"
]

# Palabras clave para detectar nivel bajo/operativo
PALABRAS_NIVEL_BAJA = [
    "vendedor", "vendedora", "operario", "operaria", "auxiliar",
    "asistente", "recepcionista", "repositor", "repositora",
    "cajero", "cajera", "ayudante", "trainee", "pasante", "junior", "jr"
]


def detectar_nivel_oferta(titulo: str) -> str:
    """
    Detecta el nivel jerarquico en el titulo de la oferta.

    Returns:
        "alta", "media", "baja" o "desconocido"
    """
    t = titulo.lower()

    if any(p in t for p in PALABRAS_NIVEL_ALTA):
        return "alta"
    if any(p in t for p in PALABRAS_NIVEL_MEDIA):
        return "media"
    if any(p in t for p in PALABRAS_NIVEL_BAJA):
        return "baja"
    return "desconocido"


def detectar_nivel_esco(label: str) -> str:
    """
    Detecta el nivel jerarquico en el label ESCO.

    Returns:
        "alta", "media" o "baja"
    """
    l = label.lower()

    palabras_alta_esco = [
        "director", "directora", "gerente", "jefe", "jefa",
        "manager", "chief", "presidente", "presidenta"
    ]
    palabras_media_esco = [
        "supervisor", "supervisora", "analista",
        "ejecutivo", "ejecutiva", "especialista", "coordinador", "coordinadora"
    ]

    if any(p in l for p in palabras_alta_esco):
        return "alta"
    if any(p in l for p in palabras_media_esco):
        return "media"
    return "baja"


def calcular_ajuste_jerarquico(titulo_oferta: str, esco_label: str) -> float:
    """
    Calcula ajuste al score basado en consistencia de nivel jerarquico.

    Returns:
        float: Ajuste a aplicar al score (-0.15 a 0)
    """
    nivel_oferta = detectar_nivel_oferta(titulo_oferta)
    nivel_esco = detectar_nivel_esco(esco_label)

    ajuste = 0.0

    # Oferta baja o media, pero ESCO alta -> penalizacion fuerte
    if nivel_oferta in ("baja", "media") and nivel_esco == "alta":
        ajuste = -0.15

    # Oferta baja y ESCO media -> penalizacion suave
    elif nivel_oferta == "baja" and nivel_esco == "media":
        ajuste = -0.05

    return ajuste


# =============================================================================
# REGLA 2: DETECCION DE PROGRAMAS DE PASANTIAS / TRAINEE
# =============================================================================

PATRONES_PASANTIA = [
    "pasantía", "pasantia", "pasantías", "pasantias",
    "programa de pasantías", "programa de pasantias",
    "jóvenes profesionales", "jovenes profesionales",
    "trainee", "graduate program", "young professionals",
    "programa de inserción", "programa de insercion",
    "primer empleo", "sin experiencia previa"
]


def es_programa_pasantias_o_trainee(titulo: str) -> bool:
    """
    Detecta si la oferta es un programa de pasantias o trainee generico.
    Estos casos no deberian auto-confirmarse.
    """
    t = titulo.lower()
    return any(p in t for p in PATRONES_PASANTIA)


# =============================================================================
# REGLA 3: FARMACEUTICO DE FARMACIA vs INGENIERO FARMACEUTICO
# =============================================================================

def es_farmaceutico_de_farmacia(titulo: str, descripcion: str = "") -> bool:
    """
    Detecta si la oferta es para farmaceutico de farmacia comunitaria/minorista.
    """
    texto = (titulo + " " + descripcion).lower()

    keywords_farmacia = [
        "farmacéutico", "farmaceutico", "farmacia", "farmacias",
        "farmacéutica", "farmaceutica"
    ]

    # Si no menciona farmacia/farmaceutico, no aplica esta regla
    if not any(k in texto for k in keywords_farmacia):
        return False

    # Keywords que indican contexto industrial (no aplica penalizacion)
    industria_keywords = [
        "industria", "industrial", "planta", "producción farmacéutica",
        "produccion farmaceutica", "laboratorio de producción",
        "laboratorio de produccion", "manufactura", "i+d", "r&d"
    ]

    # Si no menciona contexto industrial, asumimos farmacia comunitaria
    if not any(k in texto for k in industria_keywords):
        return True

    return False


def ajuste_farmaceutico(titulo: str, descripcion: str, esco_label: str) -> float:
    """
    Penaliza matches de farmaceutico de farmacia -> ingeniero farmaceutico.

    Returns:
        float: Ajuste a aplicar (-0.20 o 0)
    """
    if not es_farmaceutico_de_farmacia(titulo, descripcion):
        return 0.0

    # Si el ESCO es ingeniero, penalizar
    if "ingeniero" in esco_label.lower():
        return -0.20

    return 0.0


# =============================================================================
# REGLA 4: FAMILIA FUNCIONAL COMERCIAL / VENTAS
# =============================================================================

KEYWORDS_COMERCIAL_TITULO = [
    "ejecutivo de cuentas", "ejecutiva de cuentas",
    "ejecutivo comercial", "ejecutiva comercial",
    "account executive", "sales", "sales executive",
    "asesor comercial", "asesora comercial",
    "vendedor", "vendedora", "representante comercial",
    "representante de ventas", "representante de comercio",
    "hunter", "desarrollo de negocios", "business development",
    "ejecutivo de ventas", "ejecutiva de ventas",
    "key account", "account manager", "kam"
]

KEYWORDS_ESCO_COMERCIAL = [
    "representante comercial", "representante de ventas",
    "agente comercial", "vendedor", "vendedora",
    "empleado de ventanilla", "teleoperador", "teleoperadora",
    "agente de call center", "comercial",
    "ejecutivo de cuentas", "ejecutiva de cuentas",
    "dependiente", "dependienta"
]

# IDs de area comercial (ajustar segun la BD real)
AREA_COMERCIAL_IDS = {"COMERCIAL", "VENTAS", "ATENCION_CLIENTE", "MARKETING", "1", "2"}


def es_oferta_comercial(titulo: str, id_area: Optional[str] = None,
                        id_subarea: Optional[str] = None) -> bool:
    """
    Detecta si la oferta es de area comercial/ventas.
    """
    t = titulo.lower()

    if any(k in t for k in KEYWORDS_COMERCIAL_TITULO):
        return True

    if id_area and id_area.upper() in AREA_COMERCIAL_IDS:
        return True

    return False


def es_ocupacion_esco_comercial(label: str) -> bool:
    """
    Detecta si la ocupacion ESCO es de area comercial.
    """
    l = label.lower()
    return any(k in l for k in KEYWORDS_ESCO_COMERCIAL)


def ajuste_funcional_comercial(titulo: str, esco_label: str,
                               id_area: Optional[str] = None) -> float:
    """
    Calcula ajuste por consistencia funcional comercial.

    Returns:
        float: Ajuste a aplicar (-0.20 a +0.05)
    """
    oferta_es_comercial = es_oferta_comercial(titulo, id_area)
    esco_es_comercial = es_ocupacion_esco_comercial(esco_label)

    ajuste = 0.0

    # Oferta comercial pero ESCO no comercial -> penalizacion fuerte
    if oferta_es_comercial and not esco_es_comercial:
        ajuste = -0.20

    # Ambos comerciales -> pequeno bonus
    elif oferta_es_comercial and esco_es_comercial:
        ajuste = 0.05

    return ajuste


# =============================================================================
# FUNCION PRINCIPAL DE AJUSTES v8.1
# =============================================================================

def calcular_ajustes_v81(titulo: str, descripcion: str, esco_label: str,
                         id_area: Optional[str] = None) -> Tuple[float, dict]:
    """
    Calcula todos los ajustes v8.1 para un match.

    Args:
        titulo: Titulo de la oferta
        descripcion: Descripcion de la oferta
        esco_label: Label de la ocupacion ESCO matcheada
        id_area: ID del area de la oferta (opcional)

    Returns:
        Tuple[float, dict]: (ajuste_total, detalle_ajustes)
    """
    ajustes = {}
    total = 0.0

    # 1. Ajuste jerarquico
    aj_jerarquico = calcular_ajuste_jerarquico(titulo, esco_label)
    if aj_jerarquico != 0:
        ajustes['jerarquico'] = aj_jerarquico
        total += aj_jerarquico

    # 2. Ajuste farmaceutico
    aj_farmacia = ajuste_farmaceutico(titulo, descripcion, esco_label)
    if aj_farmacia != 0:
        ajustes['farmacia'] = aj_farmacia
        total += aj_farmacia

    # 3. Ajuste funcional comercial
    aj_comercial = ajuste_funcional_comercial(titulo, esco_label, id_area)
    if aj_comercial != 0:
        ajustes['comercial'] = aj_comercial
        total += aj_comercial

    return total, ajustes


def requiere_revision_forzada(titulo: str) -> bool:
    """
    Determina si la oferta debe ir a REVISION independientemente del score.

    Casos:
        - Programas de pasantias/trainee genericos
    """
    return es_programa_pasantias_o_trainee(titulo)


# =============================================================================
# TEST BASICO
# =============================================================================

if __name__ == '__main__':
    # Test rapido
    print("=== TEST MATCHING RULES v8.1 ===\n")

    # Caso 1: Vendedora -> Director (nivel_jerarquico)
    t1 = "Vendedora Digital / Atención al Cliente"
    e1 = "director de comercialización y ventas por canales digitales"
    aj1, det1 = calcular_ajustes_v81(t1, "", e1)
    print(f"1. {t1[:40]}...")
    print(f"   ESCO: {e1[:40]}...")
    print(f"   Ajuste: {aj1:.2f} | Detalle: {det1}\n")

    # Caso 2: Farmaceutico -> Ingeniero (tipo_ocupacion)
    t2 = "Farmacéutico/a para farmacias en Rio Cuarto"
    e2 = "ingeniero farmacéutico/ingeniera farmacéutica"
    aj2, det2 = calcular_ajustes_v81(t2, "", e2)
    print(f"2. {t2[:40]}...")
    print(f"   ESCO: {e2[:40]}...")
    print(f"   Ajuste: {aj2:.2f} | Detalle: {det2}\n")

    # Caso 3: Account Executive -> Agente empleo (sector_funcion)
    t3 = "Account Executive (Hunter)"
    e3 = "agente de empleo"
    aj3, det3 = calcular_ajustes_v81(t3, "", e3)
    print(f"3. {t3[:40]}...")
    print(f"   ESCO: {e3[:40]}...")
    print(f"   Ajuste: {aj3:.2f} | Detalle: {det3}\n")

    # Caso 4: Pasantias
    t4 = "Programa de pasantías \"Crear Futuro\""
    print(f"4. {t4}")
    print(f"   Es pasantia/trainee: {es_programa_pasantias_o_trainee(t4)}")
    print(f"   Requiere revision forzada: {requiere_revision_forzada(t4)}\n")

    # Caso 5: Match correcto (vendedor -> vendedor)
    t5 = "VENDEDOR DE REPUESTOS AUTOMOTOR"
    e5 = "vendedor de piezas de repuesto de automóviles"
    aj5, det5 = calcular_ajustes_v81(t5, "", e5)
    print(f"5. {t5[:40]}...")
    print(f"   ESCO: {e5[:40]}...")
    print(f"   Ajuste: {aj5:.2f} | Detalle: {det5}")
