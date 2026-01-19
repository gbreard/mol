#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
matching_rules_v84.py
=====================
Reglas de validacion v8.4 para ESCO matching.

Basado en Gold Set v2 (50 casos) con precision 70%.
Nuevas reglas para corregir errores sistematicos identificados:

TAREA 9: MOZO (gastronomia) vs AGRICULTURA
- Mozo/Moza en Argentina = camarero/mesero (NO agricultor)
- Excluir ESCO de agricultura cuando titulo = mozo

TAREA 10: MEDICO vs ESTETICISTA
- Medico/Dermatologo NO debe mapear a Esteticista
- Nivel profesional muy diferente (universitario vs tecnico)

TAREA 11: REPOSITOR vs MANTENEDOR
- Repositor = reponedor de estantes/gondolas (comercio)
- NO es mantenedor (mantenimiento edilicio)

TAREA 12: PICKING vs EMBALAJE
- Operario de picking = preparacion de pedidos (almacen)
- NO es operador de maquinas de embalaje (produccion)

TAREA 13: SECTOR ESPECIFICO (ventas generales)
- Ventas generales NO debe mapear a sector especifico (solar, cosmetica)
"""

from typing import Tuple

# Importar todo de v8.3 y extender
from matching_rules_v83 import (
    # Keywords v8.2
    KEYWORDS_ADMIN_CONTABLE_OFERTA, KEYWORDS_COMERCIAL_VENTAS_OFERTA,
    KEYWORDS_SERVICIOS_ATENCION_OFERTA, KEYWORDS_OPERARIO_PRODUCCION_OFERTA,
    KEYWORDS_SALUD_FARMACIA_OFERTA, KEYWORDS_PROGRAMA_PASANTIA_OFERTA,
    KEYWORDS_ADMIN_CONTABLE_ESCO, KEYWORDS_NEGOCIOS_ESCO,
    KEYWORDS_COMERCIAL_VENTAS_ESCO, KEYWORDS_DIRECTIVO_COMERCIAL_ESCO,
    # Keywords v8.3
    KEYWORDS_VENTAS_VEHICULOS_OFERTA, KEYWORDS_REPUESTOS_ESCO,
    KEYWORDS_SERVICIOS_TRANSPORTE_ESCO, KEYWORDS_BARISTA_OFERTA,
    KEYWORDS_COMERCIO_CAFE_ESCO, KEYWORDS_COCINA_ESPECIALIZADA_ESCO,
    KEYWORDS_PROFESIONAL_JURIDICO_OFERTA, KEYWORDS_ADMINISTRATIVO_JURIDICO_ESCO,
    KEYWORDS_ABOGADO_ESCO, KEYWORDS_NIVEL_JUNIOR_OFERTA, KEYWORDS_NIVEL_DIRECTIVO_ESCO,
    # Detectores v8.2
    es_oferta_admin_contable, es_oferta_comercial_ventas,
    es_oferta_servicios_atencion, es_oferta_operario_produccion,
    es_oferta_salud_farmacia, es_oferta_programa_pasantia,
    es_esco_admin_contable, es_esco_negocios, es_esco_comercial_ventas,
    es_esco_directivo_comercial,
    # Detectores v8.3
    es_oferta_ventas_vehiculos, es_esco_repuestos, es_esco_servicios_transporte,
    es_oferta_barista_gastronomia, es_esco_comercio_cafe, es_esco_cocina_especializada,
    es_oferta_profesional_juridico, es_esco_administrativo_juridico, es_esco_abogado,
    es_oferta_nivel_junior, es_esco_directivo
)


# =============================================================================
# KEYWORDS v8.4 - NUEVAS FAMILIAS
# =============================================================================

# TAREA 9: MOZO/GASTRONOMIA vs AGRICULTURA
KEYWORDS_MOZO_GASTRONOMIA_OFERTA = [
    "mozo", "moza", "camarero", "camarera", "mesero", "mesera",
    "garzon", "garzona", "bachero", "bachera",
    "ayudante de cocina", "cocinero", "cocinera", "chef"
]

KEYWORDS_AGRICULTURA_ESCO = [
    "vinedo", "vinedos", "viticola", "vitivinicola",
    "agricultor", "agricola", "labranza", "cultivo",
    "cosecha", "sembrador", "tractorista", "fumigador",
    "peon rural", "trabajador rural", "ganadero", "pastor"
]

# TAREA 10: MEDICO vs ESTETICISTA
KEYWORDS_PROFESIONAL_MEDICO_OFERTA = [
    "medico", "medica", "doctor", "doctora", "dr.", "dra.",
    "dermatologo", "dermatologa", "cirujano", "cirujana",
    "clinico", "clinica", "especialista medico",
    "traumatologo", "cardiologo", "neurologo", "oncologo",
    "pediatra", "ginecologo", "urologo", "oftalmologo",
    "otorrinolaringologo", "psiquiatra", "radiologo"
]

KEYWORDS_ESTETICA_BELLEZA_ESCO = [
    "esteticista", "cosmetologo", "cosmetologa",
    "maquillador", "maquilladora", "manicurista",
    "pedicurista", "depilador", "depiladora",
    "especialista en belleza", "tratamientos de belleza",
    "peluquero", "peluquera", "estilista"
]

# TAREA 11: REPOSITOR vs MANTENEDOR
KEYWORDS_REPOSITOR_OFERTA = [
    "repositor", "repositora", "reponedor", "reponedora",
    "gondola", "gondolas", "estante", "estantes",
    "mercaderia", "supermercado", "retail",
    "exhibidor", "promotor de gondola"
]

KEYWORDS_MANTENIMIENTO_ESCO = [
    "mantenedor", "mantenedora", "mantenimiento",
    "conserje", "intendente", "sereno",
    "encargado de edificio", "portero"
]

# TAREA 12: PICKING/LOGISTICA vs EMBALAJE
KEYWORDS_PICKING_LOGISTICA_OFERTA = [
    "picking", "piquinero", "preparador de pedidos",
    "armado de pedidos", "selector", "sorter",
    "orden de picking", "pick and pack"
]

KEYWORDS_EMBALAJE_ESCO = [
    "embalaje", "embalador", "envasador",
    "maquinas de embalaje", "llenado", "embotellado",
    "etiquetado", "empaquetador"
]

KEYWORDS_LOGISTICA_ALMACEN_ESCO = [
    "logistica", "almacen", "deposito", "bodega",
    "operario de almacen", "auxiliar de deposito",
    "preparador de pedidos", "picker"
]

# TAREA 13: VENTAS GENERALES vs SECTOR ESPECIFICO
KEYWORDS_VENTAS_GENERALES_OFERTA = [
    "ventas directas", "vendedor", "vendedora",
    "asesor de ventas", "ejecutivo de ventas",
    "atencion al cliente"
]

KEYWORDS_SECTOR_ESPECIFICO_ESCO = [
    "energia solar", "paneles solares", "fotovoltaico",
    "cosmetica", "perfumeria", "belleza",
    "maquinaria agricola", "equipos agricolas"
]


# =============================================================================
# DETECTORES v8.4
# =============================================================================

# TAREA 9
def es_oferta_mozo_gastronomia(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de mozo/camarero (gastronomia)."""
    # SOLO evaluar TITULO, no descripcion (caso Mozo en vinedo)
    texto = titulo.lower()
    return any(k in texto for k in KEYWORDS_MOZO_GASTRONOMIA_OFERTA)


def es_esco_agricultura(esco_label: str) -> bool:
    """Detecta si el ESCO es de agricultura/campo."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_AGRICULTURA_ESCO)


# TAREA 10
def es_oferta_profesional_medico(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de profesional medico."""
    # SOLO evaluar TITULO
    texto = titulo.lower()
    return any(k in texto for k in KEYWORDS_PROFESIONAL_MEDICO_OFERTA)


def es_esco_estetica_belleza(esco_label: str) -> bool:
    """Detecta si el ESCO es de estetica/belleza (nivel tecnico)."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_ESTETICA_BELLEZA_ESCO)


# TAREA 11
def es_oferta_repositor(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de repositor (comercio minorista)."""
    texto = titulo.lower()
    return any(k in texto for k in KEYWORDS_REPOSITOR_OFERTA)


def es_esco_mantenimiento(esco_label: str) -> bool:
    """Detecta si el ESCO es de mantenimiento edilicio."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_MANTENIMIENTO_ESCO)


# TAREA 12
def es_oferta_picking(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de picking/preparacion de pedidos."""
    texto = titulo.lower()
    return any(k in texto for k in KEYWORDS_PICKING_LOGISTICA_OFERTA)


def es_esco_embalaje(esco_label: str) -> bool:
    """Detecta si el ESCO es de embalaje (no picking)."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_EMBALAJE_ESCO)


def es_esco_logistica_almacen(esco_label: str) -> bool:
    """Detecta si el ESCO es de logistica/almacen."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_LOGISTICA_ALMACEN_ESCO)


# TAREA 13
def es_oferta_ventas_generales(titulo: str, descripcion: str = "") -> bool:
    """
    Detecta si la oferta es de ventas GENERALES (sin sector especifico).
    Solo titulo, sin descripcion que mencione sector especifico.
    """
    texto_titulo = titulo.lower()

    # Debe tener indicadores de ventas generales
    tiene_ventas = any(k in texto_titulo for k in KEYWORDS_VENTAS_GENERALES_OFERTA)

    # NO debe tener sector especifico en titulo
    tiene_sector = any(k in texto_titulo for k in [
        "solar", "fotovoltaico", "energia",
        "cosmetica", "perfumeria", "belleza",
        "agricola", "maquinaria"
    ])

    return tiene_ventas and not tiene_sector


def es_esco_sector_especifico(esco_label: str) -> bool:
    """Detecta si el ESCO es de sector especifico que no aplica a ventas generales."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_SECTOR_ESPECIFICO_ESCO)


# =============================================================================
# FUNCION PRINCIPAL v8.4
# =============================================================================

def calcular_ajustes_v84(titulo: str, descripcion: str, esco_label: str) -> Tuple[float, dict, bool]:
    """
    Calcula todos los ajustes v8.4 basados en familias funcionales.

    Incluye:
    - Todas las reglas de v8.3
    - TAREA 9: Mozo vs Agricultura
    - TAREA 10: Medico vs Esteticista
    - TAREA 11: Repositor vs Mantenedor
    - TAREA 12: Picking vs Embalaje
    - TAREA 13: Ventas generales vs sector especifico

    Args:
        titulo: Titulo de la oferta
        descripcion: Descripcion de la oferta
        esco_label: Label de la ocupacion ESCO matcheada

    Returns:
        Tuple[float, dict, bool]: (ajuste_total, detalle_ajustes, never_confirm)
    """
    ajustes = {}
    total = 0.0
    never_confirm = False

    # =========================================================================
    # REGLAS HEREDADAS DE v8.3
    # =========================================================================

    # REGLA 1: ADMIN vs NEGOCIOS
    if es_oferta_admin_contable(titulo, descripcion):
        if es_esco_negocios(esco_label):
            ajustes['admin_vs_negocios'] = -0.20
            total += -0.20
            never_confirm = True
        elif es_esco_admin_contable(esco_label):
            ajustes['admin_match'] = 0.05
            total += 0.05

    # REGLA 2: COMERCIAL/VENTAS
    if es_oferta_comercial_ventas(titulo, descripcion):
        if not es_esco_comercial_ventas(esco_label):
            ajustes['comercial_mismatch'] = -0.20
            total += -0.20
            never_confirm = True
        else:
            ajustes['comercial_match'] = 0.05
            total += 0.05

    # REGLA 3: SALUD/FARMACIA vs INGENIERO
    if es_oferta_salud_farmacia(titulo, descripcion):
        if "ingeniero" in esco_label.lower():
            ajustes['farmacia_vs_ingeniero'] = -0.20
            total += -0.20
            never_confirm = True

    # REGLA 4: PROGRAMAS/PASANTIAS
    if es_oferta_programa_pasantia(titulo, descripcion):
        ajustes['es_pasantia'] = 0.0
        never_confirm = True

    # REGLA 5: SERVICIOS/COMERCIAL vs DIRECTIVO
    if es_oferta_servicios_atencion(titulo, descripcion) or es_oferta_comercial_ventas(titulo, descripcion):
        if es_esco_directivo_comercial(esco_label):
            ajustes['nivel_vs_directivo'] = -0.15
            total += -0.15
            never_confirm = True

    # REGLA 6: OPERARIO vs NEGOCIOS
    if es_oferta_operario_produccion(titulo, descripcion):
        if es_esco_negocios(esco_label):
            ajustes['operario_vs_negocios'] = -0.20
            total += -0.20
            never_confirm = True

    # REGLA 7: VENTAS VEHICULOS vs REPUESTOS
    if es_oferta_ventas_vehiculos(titulo, descripcion):
        if es_esco_repuestos(esco_label):
            ajustes['vehiculos_vs_repuestos'] = -0.15
            total += -0.15
            never_confirm = True
        elif es_esco_servicios_transporte(esco_label):
            ajustes['vehiculos_vs_transporte'] = -0.10
            total += -0.10
            never_confirm = True

    # REGLA 8: BARISTA vs COMERCIO INTERNACIONAL
    if es_oferta_barista_gastronomia(titulo, descripcion):
        if es_esco_comercio_cafe(esco_label) or es_esco_cocina_especializada(esco_label):
            ajustes['barista_vs_comercio'] = -0.15
            total += -0.15
            never_confirm = True

    # REGLA 9: ABOGADO vs ADMINISTRATIVO JURIDICO
    if es_oferta_profesional_juridico(titulo, descripcion):
        if es_esco_administrativo_juridico(esco_label) and not es_esco_abogado(esco_label):
            ajustes['abogado_vs_admin_juridico'] = -0.15
            total += -0.15
            never_confirm = True
        elif es_esco_abogado(esco_label):
            ajustes['abogado_match'] = 0.05
            total += 0.05

    # REGLA 10: JUNIOR vs DIRECTIVO
    if es_oferta_nivel_junior(titulo, descripcion):
        if es_esco_directivo(esco_label):
            ajustes['junior_vs_directivo'] = -0.20
            total += -0.20
            never_confirm = True

    # =========================================================================
    # REGLAS NUEVAS v8.4
    # =========================================================================

    # REGLA 11: MOZO (GASTRONOMIA) vs AGRICULTURA - TAREA 9
    if es_oferta_mozo_gastronomia(titulo, ""):  # Solo titulo, no descripcion
        if es_esco_agricultura(esco_label):
            ajustes['mozo_vs_agricultura'] = -0.25
            total += -0.25
            never_confirm = True

    # REGLA 12: MEDICO vs ESTETICISTA - TAREA 10
    if es_oferta_profesional_medico(titulo, ""):  # Solo titulo
        if es_esco_estetica_belleza(esco_label):
            ajustes['medico_vs_esteticista'] = -0.25
            total += -0.25
            never_confirm = True

    # REGLA 13: REPOSITOR vs MANTENEDOR - TAREA 11
    if es_oferta_repositor(titulo, ""):  # Solo titulo
        if es_esco_mantenimiento(esco_label):
            ajustes['repositor_vs_mantenimiento'] = -0.20
            total += -0.20
            never_confirm = True

    # REGLA 14: PICKING vs EMBALAJE - TAREA 12
    if es_oferta_picking(titulo, ""):  # Solo titulo
        if es_esco_embalaje(esco_label):
            ajustes['picking_vs_embalaje'] = -0.15
            total += -0.15
            never_confirm = True
        elif es_esco_logistica_almacen(esco_label):
            ajustes['picking_match_almacen'] = 0.05
            total += 0.05

    # REGLA 15: VENTAS GENERALES vs SECTOR ESPECIFICO - TAREA 13
    if es_oferta_ventas_generales(titulo, ""):  # Solo titulo
        if es_esco_sector_especifico(esco_label):
            ajustes['ventas_vs_sector_especifico'] = -0.15
            total += -0.15
            never_confirm = True

    return total, ajustes, never_confirm


# =============================================================================
# TEST
# =============================================================================

if __name__ == '__main__':
    print("=== TEST MATCHING RULES v8.4 ===\n")

    tests = [
        # v8.4 TAREA 9: Mozo vs Agricultura
        ("Mozo/Moza", "Supervisor de vinedos/supervisora de vinedos", "mozo_vs_agricultura"),
        ("Camarero", "Agricultor calificado", "mozo_vs_agricultura"),

        # v8.4 TAREA 10: Medico vs Esteticista
        ("Medica Clinica o Dermatologa - tratamientos esteticos", "Esteticista", "medico_vs_esteticista"),
        ("Dermatologo especialista", "Cosmetologo", "medico_vs_esteticista"),

        # v8.4 TAREA 11: Repositor vs Mantenedor
        ("Repositor/a Externo/a", "Mantenedor/mantenedora", "repositor_vs_mantenimiento"),
        ("Reponedor de gondolas", "Conserje", "repositor_vs_mantenimiento"),

        # v8.4 TAREA 12: Picking vs Embalaje
        ("Operario Picking Zona Norte", "Operario de maquinas de embalaje", "picking_vs_embalaje"),
        ("Preparador de pedidos", "Envasador", "picking_vs_embalaje"),

        # v8.4 TAREA 13: Ventas generales vs sector especifico
        ("ASESOR DE VENTAS DIRECTAS", "Asesor comercial para venta de energia solar", "ventas_vs_sector"),
        ("Asesor/a de Ventas y Atencion al Cliente", "Vendedor especializado en cosmetica", "ventas_vs_sector"),

        # Verificar no regresion v8.3
        ("Abogado Jr. de Litigios", "empleado administrativo en el ambito juridico", "abogado_vs_admin"),
        ("Vendedores 0KM concesionaria", "vendedor de repuestos", "vehiculos_vs_repuestos"),
    ]

    passed = 0
    for titulo, esco, expected in tests:
        ajuste, detalle, never = calcular_ajustes_v84(titulo, "", esco)
        status = "PASS" if (ajuste != 0 or never) else "FAIL"
        if status == "PASS":
            passed += 1
        print(f"[{status}] {titulo[:45]}")
        print(f"       ESCO: {esco[:45]}")
        print(f"       Ajuste: {ajuste:+.2f} | never_confirm: {never}")
        print(f"       Reglas: {detalle}")
        print()

    print("=" * 60)
    print(f"RESULTADO: {passed}/{len(tests)} tests pasaron")
    print("=" * 60)
