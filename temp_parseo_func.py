def cargar_calidad_parseo():
    """Calcula calidad de parseo NLP"""
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        o.id_oferta,
        o.titulo,
        SUBSTR(o.descripcion, 1, 200) as desc_preview,
        LENGTH(o.descripcion) as desc_length,
        DATE(o.scrapeado_en) as fecha_scraping,
        -- Score: suma de campos parseados (0-7)
        (CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END +
         CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END +
         CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END) as score_calidad,
        -- Desglose individual
        CASE WHEN n.experiencia_min_anios IS NOT NULL THEN 1 ELSE 0 END as tiene_exp,
        CASE WHEN n.nivel_educativo IS NOT NULL THEN 1 ELSE 0 END as tiene_edu,
        CASE WHEN n.soft_skills_list IS NOT NULL AND n.soft_skills_list != '[]' THEN 1 ELSE 0 END as tiene_soft,
        CASE WHEN n.skills_tecnicas_list IS NOT NULL AND n.skills_tecnicas_list != '[]' THEN 1 ELSE 0 END as tiene_tec,
        CASE WHEN n.idioma_principal IS NOT NULL THEN 1 ELSE 0 END as tiene_idioma,
        CASE WHEN n.salario_min IS NOT NULL OR n.salario_max IS NOT NULL THEN 1 ELSE 0 END as tiene_salario,
        CASE WHEN n.jornada_laboral IS NOT NULL THEN 1 ELSE 0 END as tiene_jornada
    FROM ofertas o
    LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
    WHERE o.descripcion IS NOT NULL
    ORDER BY o.scrapeado_en DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convertir fecha
    df['fecha_scraping'] = pd.to_datetime(df['fecha_scraping'])

    # Calcular rangos de longitud
    df['rango_longitud'] = pd.cut(
        df['desc_length'],
        bins=[0, 500, 1000, 2000, 5000, 999999],
        labels=['Muy corta (0-500)', 'Corta (500-1K)', 'Media (1-2K)', 'Larga (2-5K)', 'Muy larga (5K+)']
    )

    return df
