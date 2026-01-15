@echo off
REM =====================================================================
REM Scheduler - Bumeran Scraping
REM =====================================================================
REM
REM Inicia el scheduler automatizado para scraping semanal
REM
REM Uso:
REM   start_scheduler.bat           - Ejecutar en consola (visible)
REM   start_scheduler.bat --hidden  - Ejecutar oculto (background)
REM
REM =====================================================================

echo ======================================================================
echo SCHEDULER - BUMERAN SCRAPING
echo ======================================================================
echo.

cd /d "%~dp0"

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en PATH
    echo.
    echo Instalar Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar si está en modo oculto
if "%1"=="--hidden" (
    echo Iniciando scheduler en modo oculto (background)...
    echo.
    echo El scheduler está corriendo en segundo plano.
    echo Para detenerlo, usar Task Manager y buscar pythonw.exe
    echo.
    start "" pythonw run_scheduler.py
    echo Scheduler iniciado!
    timeout /t 3 /nobreak >nul
    exit /b 0
)

REM Modo normal (consola visible)
echo Iniciando scheduler...
echo.
echo El scheduler ejecutará scraping automático:
echo   - Lunes y Jueves a las 8:00 AM
echo.
echo Presiona Ctrl+C para detener
echo.
echo ======================================================================
echo.

python run_scheduler.py

echo.
echo ======================================================================
echo Scheduler detenido
echo ======================================================================
pause
