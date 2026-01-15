# Configurar Tarea Programada - Ngrok Automatico
# ===================================================================
# Este script configura ngrok para iniciarse automaticamente
# al arrancar Windows y mantener el dashboard accesible externamente

$TaskName = "NgrokDashboardAutomatico"
$NgrokPath = (Get-Command ngrok).Source
$WorkingDir = "D:\OEDE\Webscrapping"

Write-Host "========================================"
Write-Host "CONFIGURANDO NGROK AUTOMATICO"
Write-Host "========================================"
Write-Host ""

# 1. Verificar si ya existe y eliminarla
Write-Host "[1/4] Verificando tareas existentes..." -ForegroundColor Yellow
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "  - Tarea existente encontrada. Eliminando..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "  - Tarea anterior eliminada" -ForegroundColor Green
}

# 2. Crear accion (ejecutar ngrok)
Write-Host ""
Write-Host "[2/4] Configurando accion..." -ForegroundColor Yellow
$Action = New-ScheduledTaskAction `
    -Execute $NgrokPath `
    -Argument "http 8051" `
    -WorkingDirectory $WorkingDir

Write-Host "  - Ngrok: $NgrokPath" -ForegroundColor Gray
Write-Host "  - Puerto: 8051" -ForegroundColor Gray
Write-Host "  - Accion configurada" -ForegroundColor Green

# 3. Crear desencadenador (trigger) - Al iniciar sesion
Write-Host ""
Write-Host "[3/4] Configurando desencadenadores..." -ForegroundColor Yellow
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn

Write-Host "  - Trigger: Al iniciar sesion" -ForegroundColor Gray
Write-Host "  - Desencadenador configurado" -ForegroundColor Green

# 4. Configurar opciones de la tarea
Write-Host ""
Write-Host "[4/4] Registrando tarea..." -ForegroundColor Yellow
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $TriggerLogon `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Inicia ngrok automaticamente para compartir dashboard externamente" `
    -Force | Out-Null

Write-Host "  - Tarea registrada exitosamente" -ForegroundColor Green

# 5. Detener ngrok actual si esta corriendo
Write-Host ""
Write-Host "[EXTRA] Deteniendo ngrok actual..." -ForegroundColor Yellow
$NgrokProcess = Get-Process ngrok -ErrorAction SilentlyContinue
if ($NgrokProcess) {
    Stop-Process -Name ngrok -Force
    Start-Sleep -Seconds 2
    Write-Host "  - Ngrok anterior detenido" -ForegroundColor Green
}

# 6. Iniciar la tarea inmediatamente
Write-Host ""
Write-Host "[EXTRA] Iniciando tarea ahora..." -ForegroundColor Yellow
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 3
Write-Host "  - Tarea iniciada" -ForegroundColor Green

# 7. Obtener URL publica
Write-Host ""
Write-Host "Esperando que ngrok inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
    $tunnel = $response.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1

    if ($tunnel) {
        Write-Host ""
        Write-Host "========================================"
        Write-Host "NGROK CONFIGURADO EXITOSAMENTE"
        Write-Host "========================================"
        Write-Host ""
        Write-Host "URL PUBLICA NUEVA:" -ForegroundColor White
        Write-Host "  $($tunnel.public_url)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Esta URL se genera automaticamente cada vez que:" -ForegroundColor Gray
        Write-Host "  - Reinicies la PC" -ForegroundColor Gray
        Write-Host "  - Inicies sesion en Windows" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Para obtener la URL actual en cualquier momento:" -ForegroundColor White
        Write-Host "  powershell -ExecutionPolicy Bypass -File obtener_url_ngrok.ps1" -ForegroundColor Cyan
        Write-Host ""
    } else {
        Write-Host "Ngrok iniciado pero aun no esta listo. Espera unos segundos." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Ngrok se esta iniciando. Usa el script obtener_url_ngrok.ps1 en unos segundos." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "COMANDOS UTILES:" -ForegroundColor White
Write-Host "  Ver estado:  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Detener:     Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Iniciar:     Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  Ver URL:     powershell -File obtener_url_ngrok.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Script completado exitosamente." -ForegroundColor Green
Write-Host ""
