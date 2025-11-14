@echo off
chcp 65001 > nul
cd /d D:\OEDE\Webscrapping\database

echo =================================================================================
echo EJECUCION COMPLETA DE SCRIPTS DE POBLACION DB
echo =================================================================================
echo Fecha: %DATE% %TIME%
echo.

echo FASE 1.1: Corrigiendo encoding UTF-8...
python fix_encoding_db.py > logs\fix_encoding.log 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] fix_encoding_db.py completado
) else (
    echo [ERROR] fix_encoding_db.py fallo - Ver logs\fix_encoding.log
    exit /b 1
)

echo.
echo FASE 1.2: Creando tablas...
python create_tables_nlp_esco.py > logs\create_tables.log 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] create_tables_nlp_esco.py completado
) else (
    echo [ERROR] create_tables_nlp_esco.py fallo - Ver logs\create_tables.log
    exit /b 1
)

echo.
echo FASE 2: Poblando ESCO desde RDF...
python populate_esco_from_rdf.py > logs\populate_esco.log 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] populate_esco_from_rdf.py completado
) else (
    echo [ERROR] populate_esco_from_rdf.py fallo - Ver logs\populate_esco.log
    exit /b 1
)

echo.
echo FASE 3: Poblando diccionarios...
python populate_dictionaries.py > logs\populate_dictionaries.log 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] populate_dictionaries.py completado
) else (
    echo [ERROR] populate_dictionaries.py fallo - Ver logs\populate_dictionaries.log
    exit /b 1
)

echo.
echo FASE 4: Migrando NLP...
python migrate_nlp_csv_to_db.py > logs\migrate_nlp.log 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] migrate_nlp_csv_to_db.py completado
) else (
    echo [ERROR] migrate_nlp_csv_to_db.py fallo - Ver logs\migrate_nlp.log
    exit /b 1
)

echo.
echo FASE 5: Matching Ofertas-ESCO...
python match_ofertas_to_esco.py > logs\match_ofertas.log 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] match_ofertas_to_esco.py completado
) else (
    echo [ERROR] match_ofertas_to_esco.py fallo - Ver logs\match_ofertas.log
    exit /b 1
)

echo.
echo =================================================================================
echo PROCESO COMPLETADO EXITOSAMENTE
echo =================================================================================
echo Ver logs detallados en: logs\
echo.
