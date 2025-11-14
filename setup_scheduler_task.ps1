# Script para Crear Tarea Programada de Windows - Bumeran Scraping
# ===================================================================
#
# Este script crea una tarea que:
# - Se inicia automáticamente al encender la PC
# - Ejecuta el scraping los Lunes y Jueves a las 8:00 AM
# - Guarda logs automáticamente
# - Actualiza la base de datos
# - El dashboard se actualiza automáticamente al leer la DB

$TaskName = "BumeranScrapingAutomatico"
$ScriptPath = "D:\OEDE\Webscrapping\run_scheduler.py"
$PythonPath = (Get-Command pythonw).Source
$WorkingDir = "D:\OEDE\Webscrapping"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CONFIGURANDO TAREA PROGRAMADA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar si ya existe y eliminarla
Write-Host "[1/5] Verificando tareas existentes..." -ForegroundColor Yellow
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "  - Tarea existente encontrada. Eliminando..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "  - Tarea anterior eliminada" -ForegroundColor Green
}

# 2. Crear acción (ejecutar pythonw con el scheduler)
Write-Host ""
Write-Host "[2/5] Configurando acción..." -ForegroundColor Yellow
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

Write-Host "  - Python: $PythonPath" -ForegroundColor Gray
Write-Host "  - Script: $ScriptPath" -ForegroundColor Gray
Write-Host "  - Acción configurada" -ForegroundColor Green

# 3. Crear desencadenador (trigger) - Al iniciar sesión + cada hora
Write-Host ""
Write-Host "[3/5] Configurando desencadenadores..." -ForegroundColor Yellow

# Trigger 1: Al iniciar sesión del usuario
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn

# Trigger 2: Repetir cada 1 hora (para verificar si es hora de scrapear)
$TriggerDaily = New-ScheduledTaskTrigger -Daily -At 7:00AM
$TriggerDaily.Repetition = $(New-ScheduledTaskTrigger -Once -At 7:00AM -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 1)).Repetition

Write-Host "  - Trigger 1: Al iniciar sesión" -ForegroundColor Gray
Write-Host "  - Trigger 2: Cada 1 hora desde las 7:00 AM" -ForegroundColor Gray
Write-Host "  - Desencadenadores configurados" -ForegroundColor Green

# 4. Configurar opciones de la tarea
Write-Host ""
Write-Host "[4/5] Configurando opciones..." -ForegroundColor Yellow
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

Write-Host "  - Ejecutar incluso con batería" -ForegroundColor Gray
Write-Host "  - Reintentar automáticamente si falla" -ForegroundColor Gray
Write-Host "  - Requiere conexión de red" -ForegroundColor Gray
Write-Host "  - Opciones configuradas" -ForegroundColor Green

# 5. Crear la tarea
Write-Host ""
Write-Host "[5/5] Registrando tarea en el sistema..." -ForegroundColor Yellow
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $TriggerLogon, $TriggerDaily `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Scraping automatizado de Bumeran - Ejecuta Lunes y Jueves a las 8:00 AM. Modo incremental con 1,148 keywords." `
    -Force | Out-Null

Write-Host "  - Tarea registrada exitosamente" -ForegroundColor Green

# 6. Iniciar la tarea inmediatamente
Write-Host ""
Write-Host "[EXTRA] Iniciando tarea ahora..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName
Write-Host "  - Tarea iniciada" -ForegroundColor Green

# 7. Mostrar resumen
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TAREA CONFIGURADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "CONFIGURACIÓN:" -ForegroundColor White
Write-Host "  Nombre:      $TaskName" -ForegroundColor Gray
Write-Host "  Calendario:  Lunes y Jueves a las 8:00 AM" -ForegroundColor Gray
Write-Host "  Modo:        Incremental (solo ofertas nuevas)" -ForegroundColor Gray
Write-Host "  Keywords:    1,148" -ForegroundColor Gray
Write-Host "  Estado:      CORRIENDO AHORA" -ForegroundColor Green
Write-Host ""
Write-Host "MONITOREO:" -ForegroundColor White
Write-Host "  Logs:        D:\OEDE\Webscrapping\logs\" -ForegroundColor Gray
Write-Host "  Dashboard:   http://localhost:8051" -ForegroundColor Gray
Write-Host "  Público:     https://24f5f11dd7c9.ngrok-free.app" -ForegroundColor Gray
Write-Host ""
Write-Host "COMANDOS ÚTILES:" -ForegroundColor White
Write-Host "  Ver estado:  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Ver logs:    Get-Content D:\OEDE\Webscrapping\logs\scheduler_*.log -Tail 50" -ForegroundColor Gray
Write-Host "  Detener:     Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Iniciar:     Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AHORA SOLO TENÉS QUE MONITOREAR" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 8. Mostrar estado actual
Write-Host "Estado actual de la tarea:" -ForegroundColor Yellow
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State, LastRunTime, NextRunTime | Format-List

Write-Host ""
Write-Host "Script completado exitosamente." -ForegroundColor Green
Write-Host ""
