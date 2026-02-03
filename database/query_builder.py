"""
Query Builder con protección contra SQL Injection.

Este módulo provee funciones seguras para construir queries dinámicas
usando whitelists de tablas y columnas permitidas.

Uso:
    from database.query_builder import safe_table, safe_column, safe_columns

    # Validar tabla
    tabla = safe_table(user_input)  # Raises ValueError si no está en whitelist

    # Validar columna
    col = safe_column(user_input)

    # Validar múltiples columnas
    cols = safe_columns(['id', 'titulo', 'empresa'])

    # Construir query segura
    query = f"SELECT {cols} FROM {tabla} WHERE id = ?"
    cursor.execute(query, (id_value,))
"""

from typing import FrozenSet, List, Optional, Set

# ============================================
# WHITELISTS DE TABLAS
# ============================================

# Tablas principales del sistema
CORE_TABLES: FrozenSet[str] = frozenset({
    'ofertas',
    'ofertas_nlp',
    'ofertas_esco_matching',
    'ofertas_esco_skills_detalle',
    'ofertas_skills_norm',
    'ofertas_nlp_history',
    'ofertas_prioridad',
    'ofertas_raw',
    'ofertas_historial',
})

# Tablas ESCO (catálogos de referencia)
ESCO_TABLES: FrozenSet[str] = frozenset({
    'esco_occupations',
    'esco_skills',
    'esco_associations',
    'esco_occupation_alternative_labels',
    'esco_skill_alternative_labels',
    'esco_isco_hierarchy',
})

# Tablas de tracking y auditoría
TRACKING_TABLES: FrozenSet[str] = frozenset({
    'pipeline_runs',
    'validation_errors',
    'learning_history',
    'validacion_historial',
})

# Tablas de scraping
SCRAPING_TABLES: FrozenSet[str] = frozenset({
    'metricas_scraping',
    'alertas',
    'scraping_sessions',
    'keywords_performance',
})

# Tablas auxiliares
AUX_TABLES: FrozenSet[str] = frozenset({
    'diccionario_arg_esco',
    'sinonimos_regionales',
    'nlp_versions',
    'skills',
    'schema_migrations',
})

# Todas las tablas permitidas
ALLOWED_TABLES: FrozenSet[str] = (
    CORE_TABLES |
    ESCO_TABLES |
    TRACKING_TABLES |
    SCRAPING_TABLES |
    AUX_TABLES
)

# ============================================
# WHITELISTS DE COLUMNAS
# ============================================

# Columnas de ofertas
OFERTAS_COLUMNS: FrozenSet[str] = frozenset({
    'id_oferta', 'id_empresa', 'titulo', 'empresa', 'descripcion',
    'localizacion', 'modalidad_trabajo', 'tipo_trabajo',
    'fecha_publicacion_iso', 'fecha_hora_publicacion_iso',
    'cantidad_vacantes', 'portal', 'url_oferta', 'scrapeado_en',
    'estado_oferta', 'fecha_baja', 'categoria_permanencia',
})

# Columnas de ofertas_nlp
OFERTAS_NLP_COLUMNS: FrozenSet[str] = frozenset({
    'id_oferta', 'titulo_limpio', 'provincia', 'localidad', 'modalidad',
    'experiencia_min_anios', 'experiencia_max_anios',
    'nivel_educativo', 'estado_educativo', 'carrera_especifica',
    'skills_tecnicas_list', 'soft_skills_list', 'certificaciones_list',
    'salario_min', 'salario_max', 'moneda',
    'area_funcional', 'nivel_seniority', 'sector_empresa',
    'tipo_contrato', 'jornada_laboral',
    'nlp_version', 'nlp_confidence_score',
    'clae_code', 'clae_grupo',
})

# Columnas de ofertas_esco_matching
MATCHING_COLUMNS: FrozenSet[str] = frozenset({
    'id_oferta', 'run_id',
    'esco_occupation_uri', 'esco_occupation_label',
    'isco_code', 'isco_label', 'occupation_match_score',
    'isco_regla', 'isco_semantico', 'score_semantico',
    'regla_aplicada', 'dual_coinciden', 'decision_metodo',
    'skills_oferta_json', 'skills_regla_json', 'skills_semantico_json',
    'estado_validacion', 'validado_timestamp', 'validado_por',
    'confidence_score', 'matching_version',
})

# Columnas de skills normalizados
SKILLS_NORM_COLUMNS: FrozenSet[str] = frozenset({
    'id', 'id_oferta', 'skill_uri', 'preferred_label',
    'L1', 'L1_nombre', 'L2', 'L2_nombre',
    'es_digital', 'origen', 'score', 'es_esencial',
    'run_id', 'created_at',
})

# Columnas de validation_errors
ERRORS_COLUMNS: FrozenSet[str] = frozenset({
    'id', 'id_oferta', 'run_id', 'error_id', 'error_tipo',
    'severidad', 'mensaje', 'campo_afectado', 'valor_actual',
    'detectado_timestamp', 'corregido', 'escalado_claude', 'resuelto',
})

# Columnas comunes (usadas en múltiples tablas)
COMMON_COLUMNS: FrozenSet[str] = frozenset({
    'id', 'id_oferta', 'run_id', 'created_at', 'updated_at',
    'timestamp', 'score', 'estado', 'tipo',
})

# Todas las columnas permitidas
ALLOWED_COLUMNS: FrozenSet[str] = (
    OFERTAS_COLUMNS |
    OFERTAS_NLP_COLUMNS |
    MATCHING_COLUMNS |
    SKILLS_NORM_COLUMNS |
    ERRORS_COLUMNS |
    COMMON_COLUMNS
)

# ============================================
# FUNCIONES DE VALIDACIÓN
# ============================================


def safe_table(table: str, allowed: Optional[FrozenSet[str]] = None) -> str:
    """
    Valida que una tabla esté en la whitelist.

    Args:
        table: Nombre de la tabla a validar
        allowed: Whitelist custom (opcional, usa ALLOWED_TABLES por defecto)

    Returns:
        El nombre de la tabla si es válida

    Raises:
        ValueError: Si la tabla no está en la whitelist
    """
    if allowed is None:
        allowed = ALLOWED_TABLES

    table = table.strip().lower()

    if table not in allowed:
        raise ValueError(
            f"Tabla no permitida: '{table}'. "
            f"Tablas válidas: {sorted(allowed)[:10]}..."
        )

    return table


def safe_column(column: str, allowed: Optional[FrozenSet[str]] = None) -> str:
    """
    Valida que una columna esté en la whitelist.

    Args:
        column: Nombre de la columna a validar
        allowed: Whitelist custom (opcional, usa ALLOWED_COLUMNS por defecto)

    Returns:
        El nombre de la columna si es válida

    Raises:
        ValueError: Si la columna no está en la whitelist
    """
    if allowed is None:
        allowed = ALLOWED_COLUMNS

    column = column.strip().lower()

    if column not in allowed:
        raise ValueError(
            f"Columna no permitida: '{column}'. "
            f"Columnas válidas: {sorted(allowed)[:10]}..."
        )

    return column


def safe_columns(columns: List[str], allowed: Optional[FrozenSet[str]] = None) -> str:
    """
    Valida múltiples columnas y las une con comas.

    Args:
        columns: Lista de nombres de columnas
        allowed: Whitelist custom

    Returns:
        String con columnas separadas por comas

    Raises:
        ValueError: Si alguna columna no está en la whitelist
    """
    validated = [safe_column(col, allowed) for col in columns]
    return ', '.join(validated)


def safe_order_by(column: str, direction: str = 'ASC') -> str:
    """
    Valida columna y dirección para ORDER BY.

    Args:
        column: Columna para ordenar
        direction: ASC o DESC

    Returns:
        String seguro para ORDER BY

    Raises:
        ValueError: Si la columna o dirección no son válidas
    """
    col = safe_column(column)
    dir_upper = direction.upper().strip()

    if dir_upper not in ('ASC', 'DESC'):
        raise ValueError(f"Dirección no válida: '{direction}'. Use 'ASC' o 'DESC'.")

    return f"{col} {dir_upper}"


def safe_limit(limit: int, max_limit: int = 10000) -> int:
    """
    Valida que el límite sea un entero positivo razonable.

    Args:
        limit: Límite a validar
        max_limit: Límite máximo permitido

    Returns:
        El límite si es válido

    Raises:
        ValueError: Si el límite no es válido
    """
    if not isinstance(limit, int):
        raise ValueError(f"Límite debe ser entero, recibido: {type(limit)}")

    if limit < 1:
        raise ValueError(f"Límite debe ser positivo, recibido: {limit}")

    if limit > max_limit:
        raise ValueError(f"Límite máximo es {max_limit}, recibido: {limit}")

    return limit


# ============================================
# QUERY BUILDERS
# ============================================


def build_select(
    table: str,
    columns: List[str],
    where: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """
    Construye un SELECT seguro.

    IMPORTANTE: Los valores del WHERE deben pasarse como parámetros,
    NO interpolados en el string.

    Args:
        table: Nombre de la tabla
        columns: Lista de columnas
        where: Cláusula WHERE (sin la palabra "WHERE")
        order_by: Columna para ordenar
        limit: Límite de filas

    Returns:
        Query SQL segura

    Example:
        query = build_select(
            'ofertas',
            ['id_oferta', 'titulo', 'empresa'],
            where='provincia = ?',
            order_by='fecha_publicacion_iso DESC',
            limit=100
        )
        cursor.execute(query, ('Buenos Aires',))
    """
    # Validar tabla y columnas
    safe_tbl = safe_table(table)
    safe_cols = safe_columns(columns)

    query = f"SELECT {safe_cols} FROM {safe_tbl}"

    if where:
        # NOTA: No validamos el WHERE porque debe contener placeholders (?)
        # La validación de valores es responsabilidad del caller
        query += f" WHERE {where}"

    if order_by:
        # Validar orden
        parts = order_by.split()
        col = safe_column(parts[0])
        direction = parts[1].upper() if len(parts) > 1 else 'ASC'
        if direction not in ('ASC', 'DESC'):
            direction = 'ASC'
        query += f" ORDER BY {col} {direction}"

    if limit is not None:
        safe_lim = safe_limit(limit)
        query += f" LIMIT {safe_lim}"

    return query


def build_count(table: str, where: Optional[str] = None) -> str:
    """
    Construye un COUNT(*) seguro.

    Args:
        table: Nombre de la tabla
        where: Cláusula WHERE opcional

    Returns:
        Query SQL segura
    """
    safe_tbl = safe_table(table)
    query = f"SELECT COUNT(*) FROM {safe_tbl}"

    if where:
        query += f" WHERE {where}"

    return query


# ============================================
# VALIDADORES DE CONTEXTO
# ============================================


def get_table_columns(table: str) -> FrozenSet[str]:
    """
    Retorna las columnas permitidas para una tabla específica.

    Args:
        table: Nombre de la tabla

    Returns:
        Set de columnas permitidas para esa tabla
    """
    table = table.lower().strip()

    mapping = {
        'ofertas': OFERTAS_COLUMNS,
        'ofertas_nlp': OFERTAS_NLP_COLUMNS,
        'ofertas_esco_matching': MATCHING_COLUMNS,
        'ofertas_skills_norm': SKILLS_NORM_COLUMNS,
        'validation_errors': ERRORS_COLUMNS,
    }

    return mapping.get(table, COMMON_COLUMNS)


def validate_column_for_table(column: str, table: str) -> str:
    """
    Valida que una columna exista en una tabla específica.

    Args:
        column: Nombre de la columna
        table: Nombre de la tabla

    Returns:
        El nombre de la columna si es válida

    Raises:
        ValueError: Si la columna no existe en esa tabla
    """
    allowed = get_table_columns(table)
    return safe_column(column, allowed)


# ============================================
# PARA USO EN CÓDIGO LEGACY
# ============================================


def sanitize_identifier(identifier: str) -> str:
    """
    Sanitiza un identificador SQL (tabla o columna).

    Solo permite letras, números y guiones bajos.
    Para código legacy que no puede usar whitelists.

    Args:
        identifier: Identificador a sanitizar

    Returns:
        Identificador sanitizado

    Raises:
        ValueError: Si el identificador contiene caracteres inválidos
    """
    import re

    identifier = identifier.strip()

    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(
            f"Identificador inválido: '{identifier}'. "
            "Solo se permiten letras, números y guiones bajos."
        )

    return identifier.lower()
