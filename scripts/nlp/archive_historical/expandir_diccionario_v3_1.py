"""
Script para expandir master_keywords.json a versión 3.1
Incorpora términos descubiertos del análisis de ofertas scrapeadas
"""

import json
from pathlib import Path
from datetime import datetime

def cargar_diccionario():
    """Carga el diccionario actual"""
    path = Path("D:/OEDE/Webscrapping/data/config/master_keywords.json")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def cargar_analisis():
    """Carga el análisis de términos faltantes"""
    path = Path("D:/OEDE/Webscrapping/data/analysis/keywords/analisis_completo_20251031_091136.json")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def expandir_diccionario(dict_actual, analisis):
    """Expande el diccionario con los nuevos términos descubiertos"""

    # NUEVOS TÉRMINOS A AGREGAR

    # 1. UBICACIONES (NUEVA CATEGORÍA)
    ubicaciones_nuevas = [
        # Ciudades principales (frecuencia >= 10)
        "caba", "buenos-aires", "gba", "gba-norte", "gba-sur", "gba-oeste",
        "rosario", "cordoba", "capital-federal",
        # Zonas/Barrios CABA y GBA (frecuencia >= 10)
        "norte", "sur", "oeste", "pilar", "avellaneda", "nunez", "san-isidro",
        "zarate", "retiro", "pacheco", "palermo", "mar-plata", "san-martin"
    ]

    # 2. MODALIDADES (agregar a categoría existente)
    modalidades_nuevas = [
        "part-time", "full-time", "presencial", "on-site", "site", "mix", "mixto",
        "turno-mañana", "turno-tarde", "turno-noche", "jornada-completa",
        "medio-tiempo", "tiempo-completo"
    ]

    # 3. NIVEL SENIORIDAD (agregar a Modalidad_Jerarquia)
    niveles_nuevos = [
        "semi-senior", "ssr", "avanzado", "medio", "exp", "experiencia",
        "nivel-inicial", "nivel-medio", "nivel-avanzado"
    ]

    # 4. ROLES GENERALES INGLÉS (distribuir en categorías)
    roles_ingles = [
        "analyst", "specialist", "engineer", "designer", "developer",
        "manager", "coordinator", "leader", "officer", "executive"
    ]

    # 5. ATENCIÓN AL CLIENTE (expandir categoría)
    atencion_cliente_nuevos = [
        "center", "contact-center", "customer-service", "customer-support",
        "atencion-telefonica", "atencion-mostrador", "service-desk",
        "mesa-atencion", "atencion-personal", "atencion-presencial"
    ]

    # 6. VENTAS / COMERCIAL (expandir categoría)
    ventas_nuevos = [
        "vendedores", "vendedora", "ejecutivo-comercial", "ejecutivo-ventas",
        "asesor-comercial", "asesor-ventas", "tecnico-comercial",
        "comercial-seguros", "comercial-exterior", "ejecutivo-cuentas-clave"
    ]

    # 7. ADMINISTRACIÓN / CONTABILIDAD (expandir categoría)
    admin_nuevos = [
        "cuentas", "cuentas-pagar", "cuentas-cobrar", "facturacion-clientes",
        "liquidacion", "liquidador-sueldos", "liquidacion-impuestos",
        "sueldos", "payroll-specialist", "analista-contable", "administrativo-contable",
        "asistente-administrativo", "auxiliar-contable"
    ]

    # 8. OPERACIONES / PRODUCCIÓN (expandir categoría)
    operaciones_nuevos = [
        "operaciones", "operarios", "operario-general", "operarios-produccion",
        "operador-general", "ayudante", "ayudante-general", "ayudante-produccion",
        "control", "control-produccion", "control-stock", "control-calidad-produccion"
    ]

    # 9. CONSTRUCCIÓN / OBRAS (expandir categoría)
    construccion_nuevos = [
        "obra", "obras", "obra-civil", "encargado-obra", "jefe-obra",
        "capataz", "oficial-construccion", "ayudante-construccion",
        "maestro-obra", "supervisor-obra", "coordinador-obra", "director-obra",
        "oficial-albanil", "oficial-plomero"
    ]

    # 10. IT / DESARROLLO (expandir categoría)
    it_nuevos = [
        "it", "desarrollo", "desarrollador-web", "desarrollador-mobile",
        "back", "back-end", "backend-developer", "analista-funcional",
        "analista-programador", "analista-sistemas", "analista-sr"
    ]

    # 11. MARKETING / CONTENIDOS (expandir categoría)
    marketing_nuevos = [
        "digital", "marketing-online", "publicidad-digital", "media-strategist",
        "strategist", "content", "contenido", "creador-contenido", "content-creator",
        "community", "community-manager-senior", "social-media-manager"
    ]

    # 12. GASTRONOMÍA (expandir categoría)
    gastronomia_nuevos = [
        "cocina", "cocinero-profesional", "ayudante-cocina", "bachero",
        "bacheros", "lavaplatos", "steward-cocina"
    ]

    # 13. RETAIL / COMERCIOS (expandir categoría)
    retail_nuevos = [
        "mostrador", "vendedor-mostrador", "atencion-mostrador",
        "cajero-supermercado", "repositor-supermercado", "promotor-punto-venta"
    ]

    # 14. SECTORES ESPECÍFICOS (nuevos o expandir)
    sectores_nuevos = [
        # Comercio
        "comercio", "comercio-exterior", "e-commerce", "ecommerce-manager",
        # Servicios
        "servicios", "servicios-generales", "servicios-profesionales",
        # Industria
        "industrial-general", "sector-industrial", "manufactura-general",
        # Alimentos
        "alimentos", "industria-alimenticia", "produccion-alimentos",
        # Salud
        "prestaciones-medicas", "servicios-salud", "centro-medico",
        # Automotriz
        "autos", "automotriz-general", "concesionario-oficial", "service-oficial",
        # Electrónica
        "electronico", "tecnologia-electronica", "servicio-tecnico-electronico",
        # Seguros
        "broker-seguros", "analista-siniestros", "productor-seguros-senior",
        # Legal
        "estudio-juridico", "estudio-contable", "estudio-profesional"
    ]

    # 15. LOGÍSTICA / TRANSPORTE (expandir categoría)
    logistica_nuevos = [
        "centro-distribucion", "cd", "gestion-stock", "gestion-deposito",
        "chofer-profesional", "conductor-profesional", "repartidor-delivery"
    ]

    # 16. EDUCACIÓN (expandir categoría)
    educacion_nuevos = [
        "estudiante", "practicante", "estudiante-avanzado", "pasante-estudiante",
        "apoyo-educativo", "clases-apoyo"
    ]

    # 17. OTROS ROLES IMPORTANTES
    otros_roles = [
        "general", "personal", "empleado-general", "gestor", "base-talentos",
        "interno", "externo", "corporativo", "publico", "privado",
        "temporario", "temporal-seis-meses", "eventual-reemplazo"
    ]

    # 18. TÉRMINOS DE COMPENSACIÓN
    compensacion = [
        "sueldo", "fijo", "comisiones", "sueldo-fijo-comisiones",
        "fijo-comisiones", "variable", "beneficios", "techo-beneficios"
    ]

    # 19. INGLÉS / IDIOMAS (expandir categoría)
    idiomas_nuevos = [
        "ingles-avanzado", "ingles-intermedio", "bilingue-ingles",
        "portugues-avanzado", "idiomas"
    ]

    # 20. PROYECTOS / GESTIÓN
    proyectos_nuevos = [
        "proyectos", "project", "project-manager-senior", "coordinador-proyectos",
        "gestion-proyectos", "proyectista", "proyectista-civil"
    ]

    # 21. B2B / SECTORES COMERCIALES
    sectores_comerciales = [
        "b2b", "b2c", "retail-b2b", "mayorista", "distribuidor",
        "agencia", "consultora", "estudio", "taller"
    ]

    # 22. TECNOLOGÍA ADICIONAL
    tech_adicional = [
        "office", "microsoft-office", "excel-avanzado", "sap",
        "erp", "sistemas-gestion"
    ]

    # 23. CALIDAD / PROCESOS
    calidad_procesos = [
        "procesos", "mejora-procesos", "analista-procesos", "gestion-procesos",
        "calidad-total", "gestion-calidad"
    ]

    # 24. RECURSOS HUMANOS
    rrhh_nuevos = [
        "recursos-humanos-senior", "analista-rrhh-senior", "coordinador-rrhh",
        "liquidador-sueldos-senior"
    ]

    # 25. VIAJES / EXTERIOR
    viajes_exterior = [
        "viajes", "disponibilidad-viajar", "exterior", "comercio-exterior-senior",
        "forwarder", "freight-forwarder-senior"
    ]

    # 26. SEGURIDAD E HIGIENE
    seguridad_higiene = [
        "seguridad-higiene", "higiene-seguridad-trabajo", "prevencionista-senior",
        "tecnico-seguridad-higiene", "coordinador-seguridad-higiene"
    ]

    # 27. ROLES EN PORTUGUÉS/NEUTRO (mercado regional)
    regional = [
        "trabajo-argentina", "empleo-argentina", "oportunidad-laboral"
    ]

    # 28. OTROS IMPORTANTES (frecuencia >= 14)
    otros_importantes = [
        "importante-empresa", "reconocida-empresa", "multinacional",
        "pyme", "startup", "empresa-familiar", "grupo-empresarial"
    ]

    # CONSOLIDAR TODOS LOS NUEVOS TÉRMINOS
    nuevos_terminos = {
        "Ubicaciones_Argentina": ubicaciones_nuevas,
        "Modalidad_Horarios": modalidades_nuevas + niveles_nuevos + compensacion,
        "Atencion_Cliente_Expansion": atencion_cliente_nuevos,
        "Ventas_Comercial_Expansion": ventas_nuevos,
        "Administracion_Contabilidad_Expansion": admin_nuevos,
        "Operaciones_Produccion_Expansion": operaciones_nuevos,
        "Construccion_Obras_Expansion": construccion_nuevos,
        "IT_Desarrollo_Expansion": it_nuevos,
        "Marketing_Digital_Expansion": marketing_nuevos,
        "Gastronomia_Expansion": gastronomia_nuevos,
        "Retail_Expansion": retail_nuevos,
        "Sectores_Industrias": sectores_nuevos,
        "Logistica_Transporte_Expansion": logistica_nuevos,
        "Educacion_Estudiantes": educacion_nuevos,
        "Proyectos_Gestion": proyectos_nuevos,
        "Sectores_Comerciales": sectores_comerciales,
        "Tecnologia_Herramientas": tech_adicional,
        "Calidad_Procesos": calidad_procesos,
        "RRHH_Expansion": rrhh_nuevos,
        "Viajes_Comercio_Exterior": viajes_exterior,
        "Seguridad_Higiene_Expansion": seguridad_higiene,
        "Otros_Roles_Generales": otros_roles + roles_ingles + otros_importantes,
        "Idiomas_Expansion": idiomas_nuevos
    }

    # Contar total de nuevos términos
    total_nuevos = sum(len(v) for v in nuevos_terminos.values())
    print(f"Total términos nuevos a agregar: {total_nuevos}")

    # Agregar a categorías del diccionario
    dict_expandido = dict_actual.copy()

    # Integrar nuevos términos en categorías existentes o crear nuevas
    for categoria, terminos in nuevos_terminos.items():
        # Buscar categoría similar existente o crear nueva
        categoria_base = categoria.replace("_Expansion", "").replace("_Argentina", "").replace("_Horarios", "_Jerarquia")

        if categoria_base in dict_expandido["categorias"]:
            # Agregar a categoría existente (sin duplicados)
            existentes = set(dict_expandido["categorias"][categoria_base])
            nuevos_unicos = [t for t in terminos if t not in existentes]
            dict_expandido["categorias"][categoria_base].extend(nuevos_unicos)
            print(f"  Agregados {len(nuevos_unicos)} términos a categoría existente: {categoria_base}")
        else:
            # Crear nueva categoría
            dict_expandido["categorias"][categoria] = terminos
            print(f"  Creada nueva categoría: {categoria} con {len(terminos)} términos")

    # Actualizar estrategia exhaustiva
    keywords_exhaustiva = set(dict_expandido["estrategias"]["exhaustiva"]["keywords"])

    # Agregar todos los nuevos términos a exhaustiva
    for terminos in nuevos_terminos.values():
        keywords_exhaustiva.update(terminos)

    dict_expandido["estrategias"]["exhaustiva"]["keywords"] = sorted(list(keywords_exhaustiva))

    # Crear estrategia ULTRA_EXHAUSTIVA (top ~1000 keywords)
    ultra_exhaustiva = sorted(list(keywords_exhaustiva))[:1000]
    dict_expandido["estrategias"]["ultra_exhaustiva"] = {
        "descripcion": "Máxima cobertura ULTRA exhaustiva - NUEVO (~1000 keywords)",
        "keywords": ultra_exhaustiva
    }

    # Actualizar metadatos
    dict_expandido["version"] = "3.1"
    dict_expandido["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
    dict_expandido["nota_version"] = f"EXPANSIÓN v3.1: +{total_nuevos} términos basados en análisis de 3,484 ofertas reales"

    # Actualizar notas
    dict_expandido["notas"].append(f"Versión 3.1: Agregados {total_nuevos} términos descubiertos por análisis de ofertas scrapeadas")
    dict_expandido["notas"].append("Nuevas categorías v3.1: Ubicaciones_Argentina, Modalidad_Horarios, Sectores_Industrias, etc.")
    dict_expandido["notas"].append("Estrategia 'ultra_exhaustiva' NUEVA: ~1,000 keywords para cobertura >95%")

    # Actualizar recomendaciones
    dict_expandido["recomendaciones"]["cobertura_maxima_95"] = "Usar estrategia 'ultra_exhaustiva' (~1,000 keywords) para cobertura >95%"

    return dict_expandido, total_nuevos

def guardar_diccionario(diccionario, ruta_backup=True):
    """Guarda el diccionario expandido"""
    path = Path("D:/OEDE/Webscrapping/data/config/master_keywords.json")

    # Backup del actual
    if ruta_backup and path.exists():
        backup_path = Path("D:/OEDE/Webscrapping/data/config/master_keywords_v3.0_backup.json")
        with open(path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Backup creado: {backup_path}")

    # Guardar nuevo
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, indent=2, ensure_ascii=False)
    print(f"Diccionario v3.1 guardado: {path}")

    return path

def main():
    print("="*70)
    print("EXPANSION DICCIONARIO MASTER_KEYWORDS v3.0 a v3.1")
    print("="*70)
    print()

    # 1. Cargar diccionario y análisis
    print("1. Cargando diccionario actual v3.0...")
    dict_actual = cargar_diccionario()
    print(f"   Versión actual: {dict_actual['version']}")
    print(f"   Keywords exhaustiva actual: {len(dict_actual['estrategias']['exhaustiva']['keywords'])}")
    print(f"   Categorías actuales: {len(dict_actual['categorias'])}")
    print()

    print("2. Cargando análisis de términos faltantes...")
    analisis = cargar_analisis()
    print(f"   Ofertas analizadas: {analisis['ofertas_analizadas']}")
    print(f"   Términos faltantes encontrados: {analisis['terminos_faltantes']}")
    print(f"   Impacto estimado: {analisis['impacto_estimado']['porcentaje']:.1f}% de ofertas")
    print()

    # 2. Expandir diccionario
    print("3. Expandiendo diccionario con términos descubiertos...")
    dict_expandido, total_nuevos = expandir_diccionario(dict_actual, analisis)
    print()

    # 3. Mostrar resumen
    print("="*70)
    print("RESUMEN EXPANSIÓN")
    print("="*70)
    print(f"Versión nueva: {dict_expandido['version']}")
    print(f"Términos nuevos agregados: {total_nuevos}")
    print(f"Keywords exhaustiva nueva: {len(dict_expandido['estrategias']['exhaustiva']['keywords'])}")
    print(f"Keywords ultra_exhaustiva (NUEVA): {len(dict_expandido['estrategias']['ultra_exhaustiva']['keywords'])}")
    print(f"Categorías totales: {len(dict_expandido['categorias'])}")
    print()

    # 4. Guardar
    print("4. Guardando diccionario expandido...")
    path_guardado = guardar_diccionario(dict_expandido, ruta_backup=True)
    print()

    print("="*70)
    print("EXPANSIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)
    print()
    print("PRÓXIMOS PASOS:")
    print("1. Re-ejecutar scraping con estrategia 'ultra_exhaustiva'")
    print("2. Validar nueva cobertura (objetivo: >60% desde actual 36%)")
    print("3. Analizar eficiencia de nuevos keywords")
    print()

if __name__ == "__main__":
    main()
