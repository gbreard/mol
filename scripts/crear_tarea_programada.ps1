# ============================================================================
# Script de configuración de Windows Task Scheduler
# ============================================================================
# Crea tarea programada para ejecutar scraping automático
#
# Uso:
#   1. Abrir PowerShell como Administrador
#   2. Ejecutar: .\scripts\crear_tarea_programada.ps1
# ============================================================================

# Configuración
$taskName = "Bumeran_Scraping_Scheduler"
$pythonPath = "python.exe"  # Ajustar si es necesario (ej: C:\Python311\python.exe)
$scriptPath = "D:\OEDE\Webscrapping\run_scheduler.py"
$workingDir = "D:\OEDE\Webscrapping"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "CONFIGURACIÓN DE TAREA PROGRAMADA - BUMERAN SCRAPING" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si la tarea ya existe
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "ATENCIÓN: Ya existe una tarea con el nombre '$taskName'" -ForegroundColor Yellow
    $response = Read-Host "¿Desea eliminarla y crear una nueva? (S/N)"

    if ($response -eq "S" -or $response -eq "s") {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Tarea anterior eliminada." -ForegroundColor Green
    } else {
        Write-Host "Operación cancelada." -ForegroundColor Red
        exit
    }
}

# Crear acción
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory $workingDir

# Crear triggers (Lunes y Jueves a las 8:00 AM)
$triggerMonday = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At "08:00AM"

$triggerThursday = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Thursday `
    -At "08:00AM"

# Configurar settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

# Crear principal (usuario actual)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Registrar tarea con AMBOS triggers
Write-Host "Creando tarea programada..." -ForegroundColor Yellow

# Primero registrar con un trigger
$task = Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggerMonday `
    -Settings $settings `
    -Principal $principal `
    -Description "Scraping automatizado de ofertas laborales Bumeran (Lunes y Jueves 8:00 AM)"

# Luego agregar el segundo trigger
$task.Triggers += $triggerThursday
$task | Set-ScheduledTask

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "TAREA CREADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Nombre de la tarea: $taskName" -ForegroundColor White
Write-Host "Programa: $pythonPath" -ForegroundColor White
Write-Host "Script: $scriptPath" -ForegroundColor White
Write-Host "Directorio de trabajo: $workingDir" -ForegroundColor White
Write-Host ""
Write-Host "Horario de ejecución:" -ForegroundColor Cyan
Write-Host "  • Lunes a las 8:00 AM" -ForegroundColor White
Write-Host "  • Jueves a las 8:00 AM" -ForegroundColor White
Write-Host ""
Write-Host "Próxima ejecución:" -ForegroundColor Cyan
$nextRun = (Get-ScheduledTask -TaskName $taskName).NextRunTime
Write-Host "  $nextRun" -ForegroundColor White
Write-Host ""
Write-Host "Para ejecutar manualmente:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor White
Write-Host ""
Write-Host "Para ver el estado:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Select *" -ForegroundColor White
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
