# Script para Obtener URL Publica de Ngrok
# =========================================

Write-Host ""
Write-Host "========================================"
Write-Host "OBTENIENDO URL PUBLICA DE NGROK"
Write-Host "========================================"
Write-Host ""

# Verificar si ngrok esta corriendo
$NgrokProcess = Get-Process ngrok -ErrorAction SilentlyContinue

if (-not $NgrokProcess) {
    Write-Host "ERROR: Ngrok no esta corriendo" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para iniciar ngrok automaticamente:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName 'NgrokDashboardAutomatico'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "O manualmente:" -ForegroundColor Yellow
    Write-Host "  ngrok http 8051" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "Ngrok esta corriendo. Obteniendo URL..." -ForegroundColor Green
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get -ErrorAction Stop
    $tunnel = $response.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1

    if ($tunnel) {
        Write-Host "URL PUBLICA ACTUAL:" -ForegroundColor White
        Write-Host ""
        Write-Host "  $($tunnel.public_url)" -ForegroundColor Green -BackgroundColor DarkGreen
        Write-Host ""
        Write-Host "Dashboard Local:" -ForegroundColor Gray
        Write-Host "  http://localhost:8051" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Panel de control de Ngrok:" -ForegroundColor Gray
        Write-Host "  http://localhost:4040" -ForegroundColor Gray
        Write-Host ""

        # Mostrar metricas
        $metrics = $tunnel.metrics
        Write-Host "Conexiones:" -ForegroundColor White
        Write-Host "  Total: $($metrics.conns.count)" -ForegroundColor Gray
        Write-Host "  Activas: $($metrics.conns.gauge)" -ForegroundColor Gray
        Write-Host ""

    } else {
        Write-Host "ERROR: No se encontro tunel HTTPS" -ForegroundColor Red
        Write-Host "Ngrok esta iniciando. Intenta de nuevo en unos segundos." -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host "ERROR: No se pudo conectar a ngrok API" -ForegroundColor Red
    Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Ngrok puede estar iniciando. Espera unos segundos e intenta de nuevo." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Comando para compartir:" -ForegroundColor White
Write-Host "  Copia la URL verde y enviala por email/chat a tus colegas" -ForegroundColor Gray
Write-Host ""
