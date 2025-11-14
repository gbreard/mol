# Instalación de PostgreSQL - Guía Rápida

## Opción 1: Instalador Oficial (Recomendado)

### 1. Descargar PostgreSQL

Descarga PostgreSQL 14+ desde:
https://www.postgresql.org/download/windows/

O usa el instalador directo de EDB:
https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

**Versión recomendada**: PostgreSQL 14.x o 15.x

### 2. Instalar

1. Ejecutar el instalador descargado
2. Seguir el asistente con estas configuraciones:

   - **Componentes**: Marcar todos (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
   - **Directorio**: Por defecto está bien (C:\Program Files\PostgreSQL\15\)
   - **Directorio de datos**: Por defecto está bien
   - **Password del superusuario (postgres)**: Elegir una contraseña fuerte y **ANOTARLA**
   - **Puerto**: 5432 (por defecto)
   - **Locale**: Spanish_Argentina.1252 o Default locale

3. Completar la instalación

### 3. Verificar Instalación

Abre una nueva consola (CMD o PowerShell) y verifica:

```bash
# Verificar que PostgreSQL esté en PATH
where psql

# Debería mostrar algo como:
# C:\Program Files\PostgreSQL\15\bin\psql.exe
```

### 4. Agregar PostgreSQL al PATH (si no está)

Si `where psql` no encuentra nada:

1. Abrir "Variables de entorno del sistema"
2. Editar la variable PATH
3. Agregar: `C:\Program Files\PostgreSQL\15\bin`
4. Aplicar y reiniciar la consola

### 5. Crear Base de Datos

Opción A - Usando pgAdmin (GUI):

1. Abrir pgAdmin 4
2. Conectar al servidor local (password que elegiste)
3. Click derecho en "Databases" -> Create -> Database
4. Nombre: `bumeran_scraping`
5. Owner: `postgres`
6. Save

Opción B - Usando línea de comandos:

```bash
# Conectar a PostgreSQL
psql -U postgres

# Crear la base de datos
CREATE DATABASE bumeran_scraping;

# Salir
\q
```

### 6. Ejecutar el Script de Schema

```bash
# Desde la consola, en el directorio del proyecto
cd D:\OEDE\Webscrapping

# Ejecutar el script SQL
psql -U postgres -d bumeran_scraping -f database/create_database.sql

# Si pide password, usar la que configuraste en la instalación
```

### 7. Configurar Variables de Entorno

Crear archivo `.env` en el root del proyecto:

```bash
# Copiar el template
copy .env.example .env

# Editar .env con tus credenciales
```

Contenido del `.env`:

```bash
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bumeran_scraping
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_AQUI  # ← Cambiar por tu password
```

---

## Opción 2: Docker (Alternativa Rápida)

Si tienes Docker instalado:

```bash
# Levantar PostgreSQL en contenedor
docker run --name postgres-bumeran -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=bumeran_scraping -p 5432:5432 -d postgres:15

# Ejecutar el schema
docker exec -i postgres-bumeran psql -U postgres -d bumeran_scraping < database/create_database.sql
```

Variables de entorno para Docker:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bumeran_scraping
DB_USER=postgres
DB_PASSWORD=mysecretpassword
```

---

## Verificación Final

Una vez instalado, verifica la conexión:

```python
# Test rápido de conexión
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); print('Conexión exitosa!') if db.connect() else print('Error de conexión')"
```

---

## Troubleshooting

### Error: "psql no se reconoce como comando"

- Reiniciar la consola después de agregar PostgreSQL al PATH
- Verificar que la ruta en PATH sea correcta

### Error: "Connection refused"

- Verificar que el servicio PostgreSQL esté corriendo
- Windows: Buscar "Services" -> "postgresql-x64-15" -> Start

### Error: "password authentication failed"

- Verificar que el password en `.env` sea correcto
- Intentar resetear el password del usuario postgres

---

## Próximo Paso

Una vez PostgreSQL instalado y configurado:

```bash
# Testear la integración completa
python run_scheduler.py --test
```

Esto ejecutará un scraping de prueba y guardará todo en PostgreSQL.
