# Ejemplos de Uso - ZonaJobs Scraper

Esta guía contiene ejemplos prácticos de cómo usar el scraper de ZonaJobs para diferentes casos de uso.

---

## Instalación Rápida

```bash
# 1. Navegar al directorio
cd D:\OEDE\Webscrapping

# 2. Instalar dependencias (si no están instaladas)
pip install requests pandas openpyxl

# 3. Listo para usar
```

---

## Ejemplo 1: Scraping Básico

Scrapear las primeras 100 ofertas y guardarlas en Excel:

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal

# Crear scraper
scraper = ZonaJobsScraperFinal(delay_between_requests=2.0)

# Scrapear
ofertas = scraper.scrapear_todo(max_paginas=5, max_resultados=100)

# Guardar
scraper.save_to_excel(ofertas, "ofertas_zonajobs.xlsx")

print(f"Se scrapearon {len(ofertas)} ofertas")
```

---

## Ejemplo 2: Buscar Ofertas de Python

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal

scraper = ZonaJobsScraperFinal()

# Scrapear primeras 200 ofertas
todas = scraper.scrapear_todo(max_resultados=200)

# Filtrar por "python"
python_jobs = scraper.filtrar_local(todas, "python")

# Guardar solo ofertas de Python
scraper.save_to_excel(python_jobs, "ofertas_python.xlsx")

# Ver resumen
scraper.print_resumen(python_jobs)
```

**Salida esperada:**
```
[FILTER] Filtradas 15 de 200 ofertas con keyword 'python'

================================================================================
RESUMEN
================================================================================
Total de ofertas: 15
Empresas únicas: 12
...
```

---

## Ejemplo 3: Análisis de Modalidades de Trabajo

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal
import pandas as pd

scraper = ZonaJobsScraperFinal()

# Scrapear 500 ofertas
ofertas = scraper.scrapear_todo(max_resultados=500)

# Convertir a DataFrame
df = pd.DataFrame(ofertas)

# Análisis por modalidad
print("\nOfertas por Modalidad:")
print(df['modalidad_trabajo'].value_counts())

# Filtrar solo remotas
remotas = df[df['modalidad_trabajo'] == 'Remoto']

# Filtrar híbridas
hibridas = df[df['modalidad_trabajo'] == 'Híbrido']

# Guardar cada grupo
remotas.to_excel("ofertas_remotas.xlsx", index=False)
hibridas.to_excel("ofertas_hibridas.xlsx", index=False)

print(f"\nRemotas: {len(remotas)}")
print(f"Híbridas: {len(hibridas)}")
```

---

## Ejemplo 4: Seguimiento Diario de Ofertas

Script para ejecutar diariamente y rastrear nuevas ofertas:

```python
# script_diario.py
from zonajobs_scraper_final import ZonaJobsScraperFinal
from datetime import datetime
import json
from pathlib import Path

def scraping_diario():
    scraper = ZonaJobsScraperFinal(delay_between_requests=2.5)

    # Scrapear primeras 3 páginas (rápido)
    ofertas = scraper.scrapear_todo(max_paginas=3)

    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d")

    # Guardar con fecha
    scraper.save_to_json(ofertas, f"zonajobs_{timestamp}.json")

    # Leer archivo anterior si existe
    yesterday_file = Path(f"zonajobs_{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}.json")

    if yesterday_file.exists():
        with open(yesterday_file, 'r', encoding='utf-8') as f:
            ofertas_ayer = json.load(f)

        # IDs de ayer
        ids_ayer = {o['id_oferta'] for o in ofertas_ayer}

        # Nuevas ofertas
        nuevas = [o for o in ofertas if o['id_oferta'] not in ids_ayer]

        if nuevas:
            print(f"\n🔔 {len(nuevas)} nuevas ofertas hoy!")
            scraper.save_to_excel(nuevas, f"nuevas_{timestamp}.xlsx")
        else:
            print("\n✓ No hay nuevas ofertas")

    else:
        print("\n📝 Primera ejecución, no hay comparación")

if __name__ == "__main__":
    scraping_diario()
```

**Automatizar en Windows:**
```cmd
schtasks /create /tn "ZonaJobs Daily" /tr "python D:\OEDE\Webscrapping\script_diario.py" /sc daily /st 09:00
```

---

## Ejemplo 5: Buscar por Múltiples Keywords

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal

scraper = ZonaJobsScraperFinal()

# Scrapear dataset completo
ofertas = scraper.scrapear_todo(max_resultados=1000)

# Keywords de interés
keywords = ["python", "javascript", "react", "angular", "node", "java", "c#"]

# Buscar cada keyword
resultados = {}

for keyword in keywords:
    filtered = scraper.filtrar_local(ofertas, keyword)
    resultados[keyword] = len(filtered)

    if filtered:
        scraper.save_to_excel(filtered, f"ofertas_{keyword}.xlsx")

# Mostrar ranking
print("\nRanking de Tecnologías:")
print("=" * 40)
for tech, count in sorted(resultados.items(), key=lambda x: x[1], reverse=True):
    print(f"{tech:15} : {count:4} ofertas")
```

**Salida esperada:**
```
Ranking de Tecnologías:
========================================
javascript      :   45 ofertas
python          :   32 ofertas
react           :   28 ofertas
java            :   18 ofertas
node            :   15 ofertas
angular         :   12 ofertas
c#              :    8 ofertas
```

---

## Ejemplo 6: Análisis de Empresas

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal
import pandas as pd

scraper = ZonaJobsScraperFinal()

# Scrapear
ofertas = scraper.scrapear_todo(max_resultados=500)

# DataFrame
df = pd.DataFrame(ofertas)

# Excluir confidenciales
df_publico = df[df['empresa_confidencial'] == False]

# Top empresas
top_empresas = df_publico['empresa'].value_counts().head(20)

print("\nTop 20 Empresas Contratando:")
print("=" * 60)
for empresa, count in top_empresas.items():
    print(f"{empresa:40} : {count:3} ofertas")

# Guardar ofertas de una empresa específica
empresa_interes = "Bumeran"
ofertas_empresa = df[df['empresa'] == empresa_interes]

if not ofertas_empresa.empty:
    scraper.save_to_excel(
        ofertas_empresa.to_dict('records'),
        f"ofertas_{empresa_interes.replace(' ', '_')}.xlsx"
    )
```

---

## Ejemplo 7: Dataset Completo

Scrapear TODO el sitio (~12,000 ofertas):

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal
from datetime import datetime

scraper = ZonaJobsScraperFinal(delay_between_requests=3.0)  # Más delay para ser respetuoso

print("⚠️  SCRAPING COMPLETO - Esto tomará ~1-2 horas")
print("=" * 60)

# Scrapear todas las páginas disponibles
todas_ofertas = scraper.scrapear_todo(
    max_paginas=600,  # ~12,000 ofertas / 22 por página
    max_resultados=None  # Sin límite
)

# Guardar
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
scraper.save_to_json(todas_ofertas, f"zonajobs_completo_{timestamp}.json")
scraper.save_to_csv(todas_ofertas, f"zonajobs_completo_{timestamp}.csv")
scraper.save_to_excel(todas_ofertas, f"zonajobs_completo_{timestamp}.xlsx")

# Estadísticas
scraper.print_resumen(todas_ofertas)

print(f"\n✅ Scraping completo: {len(todas_ofertas)} ofertas")
```

---

## Ejemplo 8: Integración con Base de Datos

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal
import sqlite3
import pandas as pd
from datetime import datetime

# Crear/conectar DB
conn = sqlite3.connect('zonajobs.db')

# Scrapear
scraper = ZonaJobsScraperFinal()
ofertas = scraper.scrapear_todo(max_resultados=200)

# DataFrame
df = pd.DataFrame(ofertas)

# Guardar en DB
df.to_sql(
    'ofertas',
    conn,
    if_exists='append',  # Agregar a las existentes
    index=False
)

# Consultar
query = """
SELECT
    titulo,
    empresa,
    modalidad_trabajo,
    localizacion
FROM ofertas
WHERE modalidad_trabajo = 'Remoto'
ORDER BY fecha_publicacion DESC
LIMIT 10
"""

resultados = pd.read_sql_query(query, conn)
print(resultados)

conn.close()
```

---

## Ejemplo 9: Notificaciones por Email

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_alerta(ofertas_nuevas):
    """Envía email con nuevas ofertas"""

    # Configurar email
    sender = "tu_email@gmail.com"
    receiver = "destino@gmail.com"
    password = "tu_contraseña_app"  # Usa contraseña de aplicación

    # Crear mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = sender
    mensaje['To'] = receiver
    mensaje['Subject'] = f"🔔 {len(ofertas_nuevas)} nuevas ofertas en ZonaJobs"

    # Cuerpo
    cuerpo = "Nuevas ofertas encontradas:\n\n"
    for oferta in ofertas_nuevas[:10]:  # Primeras 10
        cuerpo += f"• {oferta['titulo']} - {oferta['empresa']}\n"
        cuerpo += f"  {oferta['url_oferta']}\n\n"

    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Enviar
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(mensaje)

    print("✓ Email enviado")

# Uso
scraper = ZonaJobsScraperFinal()
ofertas = scraper.scrapear_todo(max_paginas=2)

# Filtrar Python
python_jobs = scraper.filtrar_local(ofertas, "python")

if python_jobs:
    enviar_alerta(python_jobs)
```

---

## Ejemplo 10: Dashboard en Tiempo Real

```python
# dashboard.py
from zonajobs_scraper_final import ZonaJobsScraperFinal
import pandas as pd
import time

def mostrar_dashboard():
    """Muestra stats en tiempo real"""

    scraper = ZonaJobsScraperFinal()

    print("Iniciando dashboard...")
    print("Presiona Ctrl+C para detener\n")

    while True:
        # Limpiar pantalla (Windows)
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

        # Scrapear primera página (rápido)
        ofertas = scraper.scrapear_todo(max_paginas=1, max_resultados=22)

        # Stats
        df = pd.DataFrame(ofertas)

        print("=" * 60)
        print(f"ZONAJOBS DASHBOARD - {time.strftime('%H:%M:%S')}")
        print("=" * 60)
        print(f"\nÚltimas {len(ofertas)} ofertas:")

        print("\nModalidades:")
        print(df['modalidad_trabajo'].value_counts())

        print("\nTop 5 Empresas:")
        print(df['empresa'].value_counts().head())

        print("\n(Actualiza cada 60s - Ctrl+C para salir)")

        # Esperar 60 segundos
        time.sleep(60)

if __name__ == "__main__":
    try:
        mostrar_dashboard()
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard detenido")
```

---

## Tips y Mejores Prácticas

### 1. Rate Limiting

```python
# Para scraping intensivo, aumentar delay
scraper = ZonaJobsScraperFinal(delay_between_requests=3.0)

# Para pruebas rápidas
scraper = ZonaJobsScraperFinal(delay_between_requests=1.5)
```

### 2. Manejo de Errores

```python
try:
    ofertas = scraper.scrapear_todo(max_resultados=100)
except Exception as e:
    print(f"Error: {e}")
    # Guardar lo que se pudo scrapear
    if scraper.ofertas_parciales:
        scraper.save_to_json(scraper.ofertas_parciales, "ofertas_parciales.json")
```

### 3. Logging

```python
import logging

logging.basicConfig(
    filename='scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

scraper = ZonaJobsScraperFinal()
ofertas = scraper.scrapear_todo(max_resultados=100)

logging.info(f"Scrapeadas {len(ofertas)} ofertas")
```

### 4. Deduplicación

```python
# Eliminar duplicados por ID
ofertas_unicas = {o['id_oferta']: o for o in ofertas}.values()
ofertas_unicas = list(ofertas_unicas)

print(f"Originales: {len(ofertas)}")
print(f"Únicas: {len(ofertas_unicas)}")
```

---

## Próximos Pasos

1. **Experimenta** con estos ejemplos
2. **Adapta** a tus necesidades específicas
3. **Comparte** tus resultados y mejoras
4. **Respeta** los términos de servicio y rate limits

---

**Happy Scraping! 🚀**
