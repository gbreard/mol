# Configurar Tarea Programada - Bumeran Scraping
$TaskName = "BumeranScrapingAutomatico"
$ScriptPath = "D:\OEDE\Webscrapping\run_scheduler.py"
$PythonPath = (Get-Command pythonw).Source
$WorkingDir = "D:\OEDE\Webscrapping"

Write-Host "Configurando tarea programada..." -ForegroundColor Cyan

# Eliminar tarea existente si existe
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tarea anterior eliminada" -ForegroundColor Yellow
}

# Crear accion
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $WorkingDir

# Crear triggers
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn
$TriggerDaily = New-ScheduledTaskTrigger -Daily -At 7:00AM
$TriggerDaily.Repetition = $(New-ScheduledTaskTrigger -Once -At 7:00AM -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 1)).Repetition

# Configurar opciones
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 3) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 10)

# Principal
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Registrar tarea
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $TriggerLogon, $TriggerDaily -Settings $Settings -Principal $Principal -Description "Scraping automatizado de Bumeran - Lunes y Jueves 8AM" -Force | Out-Null

Write-Host "Tarea registrada exitosamente" -ForegroundColor Green

# Iniciar tarea
Start-ScheduledTask -TaskName $TaskName
Write-Host "Tarea iniciada" -ForegroundColor Green

# Mostrar estado
Write-Host ""
Write-Host "Estado de la tarea:" -ForegroundColor Yellow
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State, LastRunTime, NextRunTime | Format-List

Write-Host ""
Write-Host "LISTO - Todo configurado automaticamente" -ForegroundColor Green
Write-Host "Logs: D:\OEDE\Webscrapping\logs\" -ForegroundColor Gray
Write-Host "Dashboard: http://localhost:8051" -ForegroundColor Gray
Write-Host ""
