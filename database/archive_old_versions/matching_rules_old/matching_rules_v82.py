#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
matching_rules_v82.py
=====================
Reglas de validacion v8.2 con Familias Funcionales para ESCO matching.

Basado en plan v8.2 (2025-11-28):
- Generaliza v8.1 con 6 familias funcionales
- Nuevo detector: es_esco_negocios() para "analista de negocios"
- Variable never_confirm para prevenir auto-confirmacion problematica
- Objetivo: que caso "Analista administrativo" -> "analista de negocios" NO quede CONFIRMADO

Familias:
1. ADMIN/CONTABLE
2. COMERCIAL/VENTAS
3. SERVICIOS/ATENCION
4. OPERARIOS/PRODUCCION/LOGISTICA
5. SALUD/FARMACIA
6. PROGRAMAS/PASANTIAS
"""

from typing import Tuple

# =============================================================================
# KEYWORDS POR FAMILIA - OFERTAS (titulo + descripcion)
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
# KEYWORDS POR FAMILIA - ESCO LABELS
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
# DETECTORES DE OFERTA (titulo + descripcion)
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
# DETECTORES DE ESCO LABEL
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
# REGLAS v8.2 - AJUSTES POR FAMILIA FUNCIONAL
# =============================================================================

def calcular_ajustes_v82(titulo: str, descripcion: str, esco_label: str) -> Tuple[float, dict, bool]:
    """
    Calcula todos los ajustes v8.2 basados en familias funcionales.

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
    # REGLA 1: ADMIN vs NEGOCIOS (NUEVA - resuelve caso Analista administrativo)
    # =========================================================================
    if es_oferta_admin_contable(titulo, descripcion):
        if es_esco_negocios(esco_label):
            # Oferta ADMIN pero ESCO es de NEGOCIOS -> penalizacion fuerte
            ajustes['admin_vs_negocios'] = -0.20
            total += -0.20
            never_confirm = True
        elif es_esco_admin_contable(esco_label):
            # Ambos ADMIN -> bonus
            ajustes['admin_match'] = 0.05
            total += 0.05

    # =========================================================================
    # REGLA 2: COMERCIAL/VENTAS
    # =========================================================================
    if es_oferta_comercial_ventas(titulo, descripcion):
        if not es_esco_comercial_ventas(esco_label):
            # Oferta COMERCIAL pero ESCO no es comercial
            ajustes['comercial_mismatch'] = -0.20
            total += -0.20
            never_confirm = True
        else:
            # Ambos comerciales -> bonus
            ajustes['comercial_match'] = 0.05
            total += 0.05

    # =========================================================================
    # REGLA 3: SALUD/FARMACIA vs INGENIERO
    # =========================================================================
    if es_oferta_salud_farmacia(titulo, descripcion):
        if "ingeniero" in esco_label.lower():
            # Farmaceutico de farmacia -> ingeniero farmaceutico: penalizar
            ajustes['farmacia_vs_ingeniero'] = -0.20
            total += -0.20
            never_confirm = True

    # =========================================================================
    # REGLA 4: PROGRAMAS/PASANTIAS
    # =========================================================================
    if es_oferta_programa_pasantia(titulo, descripcion):
        # Pasantias/trainee no deben auto-confirmarse
        ajustes['es_pasantia'] = 0.0
        never_confirm = True

    # =========================================================================
    # REGLA 5: SERVICIOS/COMERCIAL vs DIRECTIVO
    # =========================================================================
    if es_oferta_servicios_atencion(titulo, descripcion) or es_oferta_comercial_ventas(titulo, descripcion):
        if es_esco_directivo_comercial(esco_label):
            # Vendedora/atencion -> Director comercial: penalizar
            ajustes['nivel_vs_directivo'] = -0.15
            total += -0.15
            never_confirm = True

    # =========================================================================
    # REGLA 6: OPERARIO vs NEGOCIOS
    # =========================================================================
    if es_oferta_operario_produccion(titulo, descripcion):
        if es_esco_negocios(esco_label):
            # Operario -> analista de negocios: penalizar
            ajustes['operario_vs_negocios'] = -0.20
            total += -0.20
            never_confirm = True

    return total, ajustes, never_confirm


# =============================================================================
# TEST BASICO
# =============================================================================

if __name__ == '__main__':
    print("=== TEST MATCHING RULES v8.2 ===\n")

    # Caso 1: Analista administrativo -> analista de negocios (DEBE PENALIZAR)
    t1 = "Analista administrativo/a"
    e1 = "analista de negocios"
    aj1, det1, nc1 = calcular_ajustes_v82(t1, "", e1)
    print(f"1. {t1}")
    print(f"   ESCO: {e1}")
    print(f"   Ajuste: {aj1:.2f} | Never confirm: {nc1} | Detalle: {det1}\n")

    # Caso 2: Vendedora -> Director comercial (DEBE PENALIZAR)
    t2 = "Vendedora Digital / Atencion al Cliente"
    e2 = "director de comercializacion y ventas por canales digitales"
    aj2, det2, nc2 = calcular_ajustes_v82(t2, "", e2)
    print(f"2. {t2}")
    print(f"   ESCO: {e2}")
    print(f"   Ajuste: {aj2:.2f} | Never confirm: {nc2} | Detalle: {det2}\n")

    # Caso 3: Farmaceutico -> Ingeniero (DEBE PENALIZAR)
    t3 = "Farmaceutico/a para farmacias en Rio Cuarto"
    e3 = "ingeniero farmaceutico/ingeniera farmaceutica"
    aj3, det3, nc3 = calcular_ajustes_v82(t3, "", e3)
    print(f"3. {t3}")
    print(f"   ESCO: {e3}")
    print(f"   Ajuste: {aj3:.2f} | Never confirm: {nc3} | Detalle: {det3}\n")

    # Caso 4: Account Executive -> agente de empleo (DEBE PENALIZAR)
    t4 = "Account Executive (Hunter)"
    e4 = "agente de empleo"
    aj4, det4, nc4 = calcular_ajustes_v82(t4, "", e4)
    print(f"4. {t4}")
    print(f"   ESCO: {e4}")
    print(f"   Ajuste: {aj4:.2f} | Never confirm: {nc4} | Detalle: {det4}\n")

    # Caso 5: Pasantias (DEBE never_confirm)
    t5 = "Programa de pasantias Crear Futuro"
    e5 = "disenador de interiores"
    aj5, det5, nc5 = calcular_ajustes_v82(t5, "", e5)
    print(f"5. {t5}")
    print(f"   ESCO: {e5}")
    print(f"   Ajuste: {aj5:.2f} | Never confirm: {nc5} | Detalle: {det5}\n")

    # Caso 6: Vendedor repuestos -> vendedor repuestos (DEBE DAR BONUS)
    t6 = "VENDEDOR DE REPUESTOS AUTOMOTOR"
    e6 = "vendedor de piezas de repuesto de automoviles"
    aj6, det6, nc6 = calcular_ajustes_v82(t6, "", e6)
    print(f"6. {t6}")
    print(f"   ESCO: {e6}")
    print(f"   Ajuste: {aj6:.2f} | Never confirm: {nc6} | Detalle: {det6}\n")

    print("=" * 60)
