# Compartir Dashboard Externamente con Ngrok

**Fecha:** 2025-10-31
**Dashboard:** http://localhost:8051
**Propósito:** Permitir que colegas externos accedan al dashboard desde internet

---

## ¿Qué es Ngrok?

Ngrok es una herramienta que crea un túnel seguro desde tu computadora local hacia internet, generando una URL pública temporal que puedes compartir con tus colegas.

---

## Instalación de Ngrok

### Opción 1: Descargar desde el sitio oficial

1. Ir a: https://ngrok.com/download
2. Descargar la versión para Windows
3. Descomprimir el archivo `ngrok.exe` en una carpeta (ej: `C:\ngrok`)
4. Agregar esa carpeta al PATH de Windows (opcional pero recomendado)

### Opción 2: Instalar con Chocolatey (si lo tienes)

```powershell
choco install ngrok
```

### Opción 3: Instalar con Scoop

```powershell
scoop install ngrok
```

---

## Configuración Inicial (Requerida una sola vez)

### 1. Crear cuenta gratuita en Ngrok

1. Ir a: https://dashboard.ngrok.com/signup
2. Registrarse (gratis)
3. Copiar el "Authtoken" desde: https://dashboard.ngrok.com/get-started/your-authtoken

### 2. Configurar el Authtoken

```powershell
# Desde PowerShell o CMD
ngrok config add-authtoken TU_AUTH_TOKEN_AQUI
```

Ejemplo:
```powershell
ngrok config add-authtoken 2abc123def456ghi789jkl0mn1opqrst
```

---

## Compartir el Dashboard

### Paso 1: Iniciar el Dashboard (si no está corriendo)

```bash
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py
```

El dashboard debe estar corriendo en **http://localhost:8051**

### Paso 2: Abrir nueva terminal y ejecutar Ngrok

```powershell
ngrok http 8051
```

### Paso 3: Copiar la URL pública generada

Ngrok mostrará algo como:

```
ngrok
Session Status                online
Account                       tu_email@ejemplo.com (Plan: Free)
Version                       3.5.0
Region                        United States (us)
Latency                       50ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8051

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

La línea importante es:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:8051
```

### Paso 4: Compartir la URL

Envía la URL pública a tus colegas:
```
https://abc123.ngrok-free.app
```

**IMPORTANTE:** Esta URL es temporal y cambiará cada vez que reinicies ngrok.

---

## Límites de la Versión Gratuita

- **Sesión expira:** Después de 8 horas (debes reiniciar ngrok)
- **URL temporal:** Cambia cada vez que reinicias ngrok
- **40 conexiones/minuto:** Suficiente para visualización de dashboard
- **1 GB de transferencia/mes**

---

## Uso Avanzado (Opcional)

### Mantener la misma URL (requiere cuenta paga)

Con ngrok Pro puedes reservar subdominios personalizados:

```powershell
ngrok http 8051 --subdomain=mi-dashboard-bumeran
```

Esto genera: `https://mi-dashboard-bumeran.ngrok.io`

### Agregar autenticación básica

```powershell
ngrok http 8051 --auth="usuario:password"
```

Tus colegas deberán ingresar usuario y contraseña para acceder.

### Ver conexiones activas

Mientras ngrok está corriendo, puedes ver estadísticas en:
```
http://localhost:4040
```

Esto muestra:
- Requests HTTP realizadas
- Tiempo de respuesta
- Códigos de estado
- Tráfico de red

---

## Comandos Útiles

### Iniciar ngrok con región específica

```powershell
ngrok http 8051 --region=sa  # Sudamérica
```

Regiones disponibles:
- `us` - Estados Unidos
- `eu` - Europa
- `ap` - Asia/Pacífico
- `au` - Australia
- `sa` - Sudamérica
- `jp` - Japón
- `in` - India

### Ver todas las sesiones activas

```powershell
ngrok tunnels list
```

### Detener ngrok

En la terminal donde está corriendo ngrok, presionar: `Ctrl+C`

---

## Alternativas a Ngrok

Si ngrok no funciona para ti, hay alternativas:

1. **LocalTunnel** (gratuito, sin registro)
   ```bash
   npm install -g localtunnel
   lt --port 8051
   ```

2. **Serveo** (gratuito, vía SSH)
   ```bash
   ssh -R 80:localhost:8051 serveo.net
   ```

3. **Pagekite** (pago después de trial)
   ```bash
   pagekite.py 8051 tu-nombre.pagekite.me
   ```

---

## Troubleshooting

### Error: "command not found: ngrok"

**Solución:** Agregar ngrok al PATH o usar ruta completa:
```powershell
C:\ngrok\ngrok.exe http 8051
```

### Error: "authentication failed"

**Solución:** Configurar authtoken correctamente:
```powershell
ngrok config add-authtoken TU_TOKEN
```

### Dashboard no carga en URL pública

**Verificar:**
1. Dashboard está corriendo: `http://localhost:8051`
2. Firewall no está bloqueando ngrok
3. Puerto correcto en comando ngrok

### La URL pública dice "502 Bad Gateway"

**Causa:** El dashboard local no está corriendo

**Solución:** Iniciar el dashboard primero:
```bash
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py
```

---

## Ejemplo Completo Paso a Paso

```powershell
# 1. Abrir terminal 1 - Iniciar dashboard
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py

# 2. Abrir terminal 2 - Iniciar ngrok
ngrok http 8051

# 3. Copiar URL generada (ej: https://abc123.ngrok-free.app)

# 4. Enviar URL a colegas por email/chat

# 5. Para detener:
#    - Terminal 1: Ctrl+C (detiene dashboard)
#    - Terminal 2: Ctrl+C (detiene ngrok)
```

---

## Seguridad y Mejores Prácticas

1. **No compartas la URL públicamente en redes sociales** - Solo con colegas de confianza
2. **Cierra ngrok cuando no lo uses** - Evita dejar túneles abiertos innecesariamente
3. **Considera agregar autenticación** para dashboards con datos sensibles
4. **Monitorea el tráfico** usando la interfaz web de ngrok (http://localhost:4040)
5. **Usa la versión paga** si necesitas URLs permanentes o más tráfico

---

## Recursos Adicionales

- Documentación oficial de ngrok: https://ngrok.com/docs
- Dashboard de ngrok: https://dashboard.ngrok.com
- Ngrok Community Forum: https://community.ngrok.com
- Pricing de ngrok: https://ngrok.com/pricing

---

**Contacto:** Si tienes dudas sobre el dashboard o ngrok, consulta con el equipo técnico.

**Última actualización:** 2025-10-31
