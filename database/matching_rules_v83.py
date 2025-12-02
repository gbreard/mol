#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
matching_rules_v83.py
=====================
Reglas de validacion v8.3 con Familias Funcionales extendidas para ESCO matching.

Basado en plan v8.3 (2025-11-28):
- Hereda v8.2 (6 familias funcionales, never_confirm)
- TAREA 5: Ventas de vehiculos vs repuestos
- TAREA 6: Barista/gastronomia vs comercio cafe
- TAREA 7: Abogados vs administrativo juridico
- TAREA 8: Filtro jerarquico refinado (junior vs directivo)

Problemas resueltos:
- Ventas de autos 0KM -> vendedor de repuestos (incorrecto)
- Barista -> especialista en comercio de cafe (incorrecto)
- Abogado -> empleado administrativo juridico (incorrecto)
- Junior/Auxiliar -> Director/Gerente (jerarquia)
"""

from typing import Tuple

# =============================================================================
# KEYWORDS POR FAMILIA - OFERTAS (titulo + descripcion) [v8.2]
# =============================================================================

KEYWORDS_ADMIN_CONTABLE_OFERTA = [
    "administrativo", "administrativa", "auxiliar administrativo",
    "auxiliar contable", "facturacion", "cuentas a pagar",
    "cuentas a cobrar", "registro contable", "liquidacion",
    "archivo", "secretaria", "recepcionista", "data entry",
    "ingreso de datos", "back office", "asistente de oficina"
]

KEYWORDS_COMERCIAL_VENTAS_OFERTA = [
    "vendedor", "vendedora", "ejecutivo de cuentas", "ejecutiva de cuentas",
    "ejecutivo comercial", "ejecutiva comercial", "account executive",
    "asesor comercial", "asesora comercial", "sales", "ventas",
    "representante comercial", "representante de ventas", "hunter",
    "business development", "desarrollo de negocios", "kam",
    "key account", "account manager", "plan de ahorro"
]

KEYWORDS_SERVICIOS_ATENCION_OFERTA = [
    "atencion al cliente", "customer service", "soporte tecnico",
    "help desk", "call center", "telefonista", "operador telefonico",
    "recepcion", "front desk", "mesero", "mozo", "camarero",
    "servicio al cliente", "asistencia al cliente"
]

KEYWORDS_OPERARIO_PRODUCCION_OFERTA = [
    "operario", "operaria", "operador", "operadora", "produccion",
    "manufactura", "planta", "fabrica", "almacen", "deposito",
    "logistica", "chofer", "conductor", "camionero", "repartidor",
    "repositor", "repositora", "picking", "packing", "montacargas"
]

KEYWORDS_SALUD_FARMACIA_OFERTA = [
    "farmaceutico", "farmaceutica", "farmacia", "farmacias",
    "enfermero", "enfermera", "medico", "medica", "doctor", "doctora",
    "kinesiologo", "fisioterapeuta", "nutricionista", "psicologo",
    "odontologo", "laboratorio clinico", "bioquimico"
]

KEYWORDS_PROGRAMA_PASANTIA_OFERTA = [
    "pasantia", "pasantias", "pasantia", "programa de pasantias",
    "trainee", "jovenes profesionales", "joven profesional",
    "primer empleo", "sin experiencia previa", "graduate program",
    "young professionals", "programa de insercion"
]

# =============================================================================
# KEYWORDS v8.3 - NUEVAS FAMILIAS
# =============================================================================

# TAREA 5: VENTAS DE VEHICULOS
KEYWORDS_VENTAS_VEHICULOS_OFERTA = [
    "0km", "0 km", "okm",
    "concesionaria", "concesionario",
    "autos", "automotor", "automotriz",
    "vehiculos", "vehiculo",
    "motos", "motocicletas", "motovehiculos",
    "automoviles", "automovil"
]

KEYWORDS_REPUESTOS_ESCO = [
    "repuestos", "piezas de repuesto", "recambios",
    "taller", "servicio de reparacion", "mecanico"
]

KEYWORDS_SERVICIOS_TRANSPORTE_ESCO = [
    "representante de ventas de servicios de transporte",
    "agente de viajes", "operador turistico"
]

# TAREA 6: BARISTA/GASTRONOMIA
KEYWORDS_BARISTA_OFERTA = [
    "barista", "cafeteria", "cafe de especialidad",
    "barman", "bartender", "coctelero",
    "servicio de bebidas"
]

KEYWORDS_COMERCIO_CAFE_ESCO = [
    "especialista en importacion y exportacion de cafe",
    "importacion y exportacion de cafe, te, cacao",
    "importacion de cafe",
    "exportacion de cafe",
    "comercio internacional de alimentos",
    "comercio de cafe"
]

KEYWORDS_COCINA_ESPECIALIZADA_ESCO = [
    "cocinero especializado en pescados",
    "cocinero especializado en mariscos",
    "chef de pescados", "chef de mariscos"
]

# TAREA 7: ABOGADOS/PROFESIONALES JURIDICOS
KEYWORDS_PROFESIONAL_JURIDICO_OFERTA = [
    "abogado", "abogada", "abog.",
    "letrado", "letrada",
    "litigios", "litigante",
    "derecho penal", "derecho civil", "derecho comercial", "derecho laboral",
    "derecho", "jurista", "juridico profesional"
]

KEYWORDS_ADMINISTRATIVO_JURIDICO_ESCO = [
    "empleado administrativo en el ambito juridico",
    "auxiliar juridico", "asistente juridico",
    "secretario juridico", "secretaria juridica",
    "administrativo legal"
]

KEYWORDS_ABOGADO_ESCO = [
    "abogado", "abogada", "jurista",
    "asesor juridico", "asesora juridica",
    "letrado", "letrada", "fiscal"
]

# TAREA 8: FILTRO JERARQUICO
KEYWORDS_NIVEL_JUNIOR_OFERTA = [
    "junior", "jr", "jr.",
    "asistente", "auxiliar",
    "administrativo", "administrativa",
    "liquidador", "liquidadora",
    "analista jr", "analista junior",
    "entry level", "sin experiencia"
]

KEYWORDS_NIVEL_DIRECTIVO_ESCO = [
    "director", "directora",
    "gerente", "gerenta",
    "jefe de departamento", "jefa de departamento",
    "tesorero corporativo", "tesorera corporativa",
    "director comercial", "director de operaciones",
    "ceo", "cfo", "coo", "cto"
]


# =============================================================================
# KEYWORDS POR FAMILIA - ESCO LABELS [v8.2]
# =============================================================================

KEYWORDS_ADMIN_CONTABLE_ESCO = [
    "empleado administrativo", "auxiliar contable", "empleado de oficina",
    "recepcionista", "secretario", "secretaria", "oficinista",
    "empleado de archivo", "archivista", "asistente administrativo"
]

KEYWORDS_NEGOCIOS_ESCO = [
    "analista de negocios", "business analyst", "consultor de negocios",
    "analista de inteligencia de negocios", "business development",
    "consultor empresarial", "analista de gestion"
]

KEYWORDS_COMERCIAL_VENTAS_ESCO = [
    "representante comercial", "representante de ventas", "agente comercial",
    "vendedor", "vendedora", "ejecutivo de cuentas", "ejecutiva de cuentas",
    "dependiente", "dependienta", "promotor de ventas", "promotora de ventas",
    "empleado de ventanilla", "teleoperador", "teleoperadora",
    "agente de call center"
]

KEYWORDS_DIRECTIVO_COMERCIAL_ESCO = [
    "director comercial", "director de comercializacion",
    "director de ventas", "jefe de ventas", "gerente comercial",
    "gerente de ventas", "director de comercializacion y ventas",
    "director de mercadeo"
]


# =============================================================================
# DETECTORES DE OFERTA (titulo + descripcion) [v8.2]
# =============================================================================

def es_oferta_admin_contable(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de familia ADMIN/CONTABLE."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_ADMIN_CONTABLE_OFERTA)


def es_oferta_comercial_ventas(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de familia COMERCIAL/VENTAS."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_COMERCIAL_VENTAS_OFERTA)


def es_oferta_servicios_atencion(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de familia SERVICIOS/ATENCION."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_SERVICIOS_ATENCION_OFERTA)


def es_oferta_operario_produccion(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de familia OPERARIOS/PRODUCCION/LOGISTICA."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_OPERARIO_PRODUCCION_OFERTA)


def es_oferta_salud_farmacia(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de familia SALUD/FARMACIA."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_SALUD_FARMACIA_OFERTA)


def es_oferta_programa_pasantia(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de familia PROGRAMAS/PASANTIAS."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_PROGRAMA_PASANTIA_OFERTA)


# =============================================================================
# DETECTORES v8.3 - NUEVAS FAMILIAS
# =============================================================================

# TAREA 5: VENTAS VEHICULOS
def es_oferta_ventas_vehiculos(titulo: str, descripcion: str = "") -> bool:
    """
    Detecta si la oferta es de VENTAS de vehiculos NUEVOS (no repuestos).
    La oferta debe tener indicadores de vehiculos nuevos (0km, concesionaria)
    y NO contener "repuestos" o similares.
    """
    texto = (titulo + " " + descripcion).lower()

    # Debe tener indicadores de ventas
    tiene_ventas = any(k in texto for k in KEYWORDS_COMERCIAL_VENTAS_OFERTA)

    # Debe tener indicadores de vehiculos
    tiene_vehiculos = any(k in texto for k in KEYWORDS_VENTAS_VEHICULOS_OFERTA)

    # NO debe ser de repuestos (estos son matches correctos)
    es_repuestos = any(k in texto for k in ["repuesto", "repuestos", "autopartes", "piezas"])

    return tiene_ventas and tiene_vehiculos and not es_repuestos


def es_esco_repuestos(esco_label: str) -> bool:
    """Detecta si el ESCO es de repuestos/taller."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_REPUESTOS_ESCO)


def es_esco_servicios_transporte(esco_label: str) -> bool:
    """Detecta si el ESCO es de servicios de transporte/viajes."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_SERVICIOS_TRANSPORTE_ESCO)


# TAREA 6: BARISTA/GASTRONOMIA
def es_oferta_barista_gastronomia(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de barista/servicio de bebidas."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_BARISTA_OFERTA)


def es_esco_comercio_cafe(esco_label: str) -> bool:
    """Detecta si el ESCO es comercio internacional de cafe."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_COMERCIO_CAFE_ESCO)


def es_esco_cocina_especializada(esco_label: str) -> bool:
    """Detecta si el ESCO es cocina especializada (pescados/mariscos)."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_COCINA_ESPECIALIZADA_ESCO)


# TAREA 7: ABOGADOS
def es_oferta_profesional_juridico(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de profesional juridico (abogado)."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_PROFESIONAL_JURIDICO_OFERTA)


def es_esco_administrativo_juridico(esco_label: str) -> bool:
    """Detecta si el ESCO es administrativo juridico (no profesional)."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_ADMINISTRATIVO_JURIDICO_ESCO)


def es_esco_abogado(esco_label: str) -> bool:
    """Detecta si el ESCO es abogado/profesional juridico."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_ABOGADO_ESCO)


# TAREA 8: JERARQUICO
def es_oferta_nivel_junior(titulo: str, descripcion: str = "") -> bool:
    """Detecta si la oferta es de nivel junior/entry."""
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_NIVEL_JUNIOR_OFERTA)


def es_esco_directivo(esco_label: str) -> bool:
    """Detecta si el ESCO es de nivel directivo."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_NIVEL_DIRECTIVO_ESCO)


# =============================================================================
# DETECTORES DE ESCO LABEL [v8.2]
# =============================================================================

def es_esco_admin_contable(esco_label: str) -> bool:
    """Detecta si el ESCO label es de familia ADMIN/CONTABLE."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_ADMIN_CONTABLE_ESCO)


def es_esco_negocios(esco_label: str) -> bool:
    """
    Detecta si el ESCO label es de familia NEGOCIOS.
    NUEVO en v8.2 - para detectar "analista de negocios" y similares.
    """
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_NEGOCIOS_ESCO)


def es_esco_comercial_ventas(esco_label: str) -> bool:
    """Detecta si el ESCO label es de familia COMERCIAL/VENTAS."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_COMERCIAL_VENTAS_ESCO)


def es_esco_directivo_comercial(esco_label: str) -> bool:
    """Detecta si el ESCO label es de familia DIRECTIVO COMERCIAL."""
    label = esco_label.lower()
    return any(k in label for k in KEYWORDS_DIRECTIVO_COMERCIAL_ESCO)


# =============================================================================
# REGLAS v8.3 - AJUSTES POR FAMILIA FUNCIONAL
# =============================================================================

def calcular_ajustes_v83(titulo: str, descripcion: str, esco_label: str) -> Tuple[float, dict, bool]:
    """
    Calcula todos los ajustes v8.3 basados en familias funcionales extendidas.

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
    # REGLA 1: ADMIN vs NEGOCIOS [v8.2]
    # =========================================================================
    if es_oferta_admin_contable(titulo, descripcion):
        if es_esco_negocios(esco_label):
            ajustes['admin_vs_negocios'] = -0.20
            total += -0.20
            never_confirm = True
        elif es_esco_admin_contable(esco_label):
            ajustes['admin_match'] = 0.05
            total += 0.05

    # =========================================================================
    # REGLA 2: COMERCIAL/VENTAS [v8.2]
    # =========================================================================
    if es_oferta_comercial_ventas(titulo, descripcion):
        if not es_esco_comercial_ventas(esco_label):
            ajustes['comercial_mismatch'] = -0.20
            total += -0.20
            never_confirm = True
        else:
            ajustes['comercial_match'] = 0.05
            total += 0.05

    # =========================================================================
    # REGLA 3: SALUD/FARMACIA vs INGENIERO [v8.2]
    # =========================================================================
    if es_oferta_salud_farmacia(titulo, descripcion):
        if "ingeniero" in esco_label.lower():
            ajustes['farmacia_vs_ingeniero'] = -0.20
            total += -0.20
            never_confirm = True

    # =========================================================================
    # REGLA 4: PROGRAMAS/PASANTIAS [v8.2]
    # =========================================================================
    if es_oferta_programa_pasantia(titulo, descripcion):
        ajustes['es_pasantia'] = 0.0
        never_confirm = True

    # =========================================================================
    # REGLA 5: SERVICIOS/COMERCIAL vs DIRECTIVO [v8.2]
    # =========================================================================
    if es_oferta_servicios_atencion(titulo, descripcion) or es_oferta_comercial_ventas(titulo, descripcion):
        if es_esco_directivo_comercial(esco_label):
            ajustes['nivel_vs_directivo'] = -0.15
            total += -0.15
            never_confirm = True

    # =========================================================================
    # REGLA 6: OPERARIO vs NEGOCIOS [v8.2]
    # =========================================================================
    if es_oferta_operario_produccion(titulo, descripcion):
        if es_esco_negocios(esco_label):
            ajustes['operario_vs_negocios'] = -0.20
            total += -0.20
            never_confirm = True

    # =========================================================================
    # REGLA 7: VENTAS VEHICULOS vs REPUESTOS [v8.3 - TAREA 5]
    # =========================================================================
    if es_oferta_ventas_vehiculos(titulo, descripcion):
        if es_esco_repuestos(esco_label):
            ajustes['vehiculos_vs_repuestos'] = -0.15
            total += -0.15
            never_confirm = True
        elif es_esco_servicios_transporte(esco_label):
            ajustes['vehiculos_vs_transporte'] = -0.10
            total += -0.10
            never_confirm = True

    # =========================================================================
    # REGLA 8: BARISTA vs COMERCIO INTERNACIONAL [v8.3 - TAREA 6]
    # =========================================================================
    if es_oferta_barista_gastronomia(titulo, descripcion):
        if es_esco_comercio_cafe(esco_label) or es_esco_cocina_especializada(esco_label):
            ajustes['barista_vs_comercio'] = -0.15
            total += -0.15
            never_confirm = True

    # =========================================================================
    # REGLA 9: ABOGADO vs ADMINISTRATIVO JURIDICO [v8.3 - TAREA 7]
    # =========================================================================
    if es_oferta_profesional_juridico(titulo, descripcion):
        if es_esco_administrativo_juridico(esco_label) and not es_esco_abogado(esco_label):
            ajustes['abogado_vs_admin_juridico'] = -0.15
            total += -0.15
            never_confirm = True
        elif es_esco_abogado(esco_label):
            ajustes['abogado_match'] = 0.05
            total += 0.05

    # =========================================================================
    # REGLA 10: JUNIOR vs DIRECTIVO (refuerzo) [v8.3 - TAREA 8]
    # =========================================================================
    if es_oferta_nivel_junior(titulo, descripcion):
        if es_esco_directivo(esco_label):
            ajustes['junior_vs_directivo'] = -0.20
            total += -0.20
            never_confirm = True

    return total, ajustes, never_confirm


# =============================================================================
# TEST BASICO
# =============================================================================

if __name__ == '__main__':
    print("=== TEST MATCHING RULES v8.3 ===\n")

    tests = [
        # v8.2 tests (verificar no regresion)
        ("Analista administrativo/a", "analista de negocios", "admin_vs_negocios"),
        ("Vendedora Digital / Atencion al Cliente", "director de comercializacion y ventas", "vendedor->director"),
        ("Farmaceutico/a para farmacias en Rio Cuarto", "ingeniero farmaceutico", "farmacia->ingeniero"),

        # v8.3 tests - TAREA 5
        ("Vendedores Convencionales de Autos 0KM", "vendedor de piezas de repuesto", "vehiculos_vs_repuestos"),
        ("Vendedor Viajante Autos 0 KM", "vendedor de repuestos de automoviles", "vehiculos_vs_repuestos"),
        ("Asesor de ventas para concesionaria", "representante de servicios de transporte", "vehiculos_vs_transporte"),

        # v8.3 tests - TAREA 6
        ("Oportunidades en Gastronomia: Baristas", "especialista en importacion de cafe", "barista_vs_comercio"),

        # v8.3 tests - TAREA 7
        ("Abogado Jr. de Litigios (Civil y Comercial)", "empleado administrativo en el ambito juridico", "abogado_vs_admin"),
        ("Abogado Jr. de Litigios (Civil y Comercial)", "abogado", "abogado_match"),

        # v8.3 tests - TAREA 8
        ("Liquidador de sueldos junior", "tesorero corporativo", "junior_vs_directivo"),
        ("Auxiliar contable", "director de operaciones", "junior_vs_directivo"),
    ]

    for titulo, esco, expected in tests:
        ajuste, detalle, never = calcular_ajustes_v83(titulo, "", esco)
        status = "OK" if (ajuste != 0 or never) else "FALTA REGLA"
        print(f"[{status}] {titulo[:40]}")
        print(f"       ESCO: {esco[:40]}")
        print(f"       Ajuste: {ajuste:+.2f} | never_confirm: {never} | {detalle}")
        print()

    print("=" * 60)
