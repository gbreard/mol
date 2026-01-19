# MOL-31: Configuración de AWS S3

> **Fecha:** 2025-12-05
> **Issue:** [MOL-31](https://linear.app/molar/issue/MOL-31)

---

## 1. Crear Bucket S3 (AWS Console)

### Paso 1: Acceder a S3
1. Ir a [AWS Console](https://console.aws.amazon.com/)
2. Buscar "S3" en la barra de búsqueda
3. Click en "S3" para abrir el servicio

### Paso 2: Crear el bucket
1. Click en **"Create bucket"**
2. Configurar:

| Campo | Valor |
|-------|-------|
| Bucket name | `mol-validation-data` |
| AWS Region | `us-east-1` (N. Virginia) o `sa-east-1` (São Paulo) |

### Paso 3: Configuración de privacidad (IMPORTANTE)

En la sección **"Block Public Access settings for this bucket"**:

```
[x] Block all public access
    [x] Block public access to buckets and objects granted through new ACLs
    [x] Block public access to buckets and objects granted through any ACLs
    [x] Block public access to buckets and objects granted through new public bucket policies
    [x] Block public and cross-account access to buckets through any public bucket policies
```

**Marcar TODAS las casillas** (mantener el bucket privado).

### Paso 4: Versionado (opcional pero recomendado)
- Bucket Versioning: **Enable**
- Esto permite recuperar versiones anteriores de `validations.json` si hay errores

### Paso 5: Encriptación
- Server-side encryption: **Enable**
- Encryption type: **Amazon S3-managed keys (SSE-S3)**

### Paso 6: Crear
- Click en **"Create bucket"**

---

## 2. Crear Estructura de Carpetas

Después de crear el bucket, crear la estructura:

1. Click en el bucket `mol-validation-data`
2. Click en **"Create folder"**
3. Crear las siguientes carpetas:

```
mol-validation-data/
├── snapshots/
├── gold_set/
│   └── history/
└── config/
```

**Pasos:**
1. Create folder: `snapshots` → Create
2. Create folder: `gold_set` → Create
3. Entrar a `gold_set/`, Create folder: `history` → Create
4. Volver atrás, Create folder: `config` → Create

---

## 3. Crear Usuario IAM: mol-s3-writer (Local)

### Paso 1: Acceder a IAM
1. Ir a [IAM Console](https://console.aws.amazon.com/iam/)
2. Click en **"Users"** en el menú lateral
3. Click en **"Create user"**

### Paso 2: Configurar usuario
| Campo | Valor |
|-------|-------|
| User name | `mol-s3-writer` |
| Access type | Programmatic access (crear Access Key después) |

### Paso 3: Crear política personalizada
1. Click en **"Policies"** en el menú lateral
2. Click en **"Create policy"**
3. Seleccionar pestaña **"JSON"**
4. Pegar la siguiente política:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::mol-validation-data"
    },
    {
      "Sid": "WriteSnapshots",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::mol-validation-data/snapshots/*",
        "arn:aws:s3:::mol-validation-data/config/*"
      ]
    },
    {
      "Sid": "ReadGoldSet",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::mol-validation-data/gold_set/*"
    }
  ]
}
```

5. Click en **"Next"**
6. Nombre: `mol-s3-writer-policy`
7. Descripción: `Permite escribir snapshots y leer gold_set para MOL`
8. Click en **"Create policy"**

### Paso 4: Asignar política al usuario
1. Volver a **"Users"** → Click en `mol-s3-writer`
2. Pestaña **"Permissions"** → **"Add permissions"** → **"Attach policies directly"**
3. Buscar `mol-s3-writer-policy`
4. Seleccionar y click en **"Add permissions"**

### Paso 5: Crear Access Key
1. En el usuario `mol-s3-writer`, pestaña **"Security credentials"**
2. Sección **"Access keys"** → **"Create access key"**
3. Seleccionar **"Application running outside AWS"**
4. Click en **"Create access key"**
5. **GUARDAR** el Access Key ID y Secret Access Key (solo se muestran una vez)

---

## 4. Crear Usuario IAM: mol-s3-reader (Vercel)

### Paso 1: Crear usuario
1. IAM → Users → Create user
2. User name: `mol-s3-reader`

### Paso 2: Crear política personalizada

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::mol-validation-data"
    },
    {
      "Sid": "ReadAll",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::mol-validation-data/*"
    },
    {
      "Sid": "WriteGoldSet",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::mol-validation-data/gold_set/*"
    }
  ]
}
```

3. Nombre: `mol-s3-reader-policy`
4. Descripción: `Permite leer todos los archivos y escribir validaciones en gold_set`

### Paso 3: Asignar y crear Access Key
- Mismo proceso que mol-s3-writer
- Guardar credenciales para configurar en Vercel

---

## 5. Resumen de Permisos

| Usuario | snapshots/ | gold_set/ | config/ |
|---------|------------|-----------|---------|
| mol-s3-writer | Read/Write/Delete | Read | Read/Write |
| mol-s3-reader | Read | Read/Write | Read |

**Lógica:**
- **writer** (local): Sube snapshots, lee gold_set para sync
- **reader** (Vercel): Lee todo, escribe validaciones en gold_set

---

## 6. Configuración Local

### Variables de entorno

Crear archivo `.env` o `config/aws_credentials.json`:

**Opción A: .env (recomendado)**
```bash
# AWS S3 - MOL Validation
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET=mol-validation-data
```

**Opción B: config/aws_credentials.json**
```json
{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "...",
  "region": "us-east-1",
  "bucket": "mol-validation-data"
}
```

### Agregar a .gitignore
```
# AWS Credentials
config/aws_credentials.json
.env
```

---

## 7. Configuración Vercel

En el dashboard de Vercel del proyecto:

1. Settings → Environment Variables
2. Agregar:

| Key | Value | Environment |
|-----|-------|-------------|
| `AWS_ACCESS_KEY_ID` | (del mol-s3-reader) | Production, Preview |
| `AWS_SECRET_ACCESS_KEY` | (del mol-s3-reader) | Production, Preview |
| `AWS_REGION` | `us-east-1` | Production, Preview |
| `S3_BUCKET` | `mol-validation-data` | Production, Preview |

---

## 8. Verificación

### Test desde AWS CLI (opcional)
```bash
# Configurar perfil
aws configure --profile mol-writer
# Ingresar Access Key, Secret, Region

# Listar bucket
aws s3 ls s3://mol-validation-data/ --profile mol-writer

# Subir archivo de prueba
echo '{"test": true}' > test.json
aws s3 cp test.json s3://mol-validation-data/config/test.json --profile mol-writer

# Verificar
aws s3 ls s3://mol-validation-data/config/ --profile mol-writer

# Limpiar
aws s3 rm s3://mol-validation-data/config/test.json --profile mol-writer
```

### Test desde Python
```bash
python scripts/test_s3_connection.py
```

---

## 9. Checklist Final

- [ ] Bucket `mol-validation-data` creado
- [ ] Block Public Access habilitado
- [ ] Carpetas `snapshots/`, `gold_set/`, `config/` creadas
- [ ] Usuario `mol-s3-writer` con política asignada
- [ ] Usuario `mol-s3-reader` con política asignada
- [ ] Access Keys generadas y guardadas
- [ ] Credenciales locales configuradas
- [ ] Credenciales en Vercel configuradas (cuando se cree el proyecto)
- [ ] Test de conexión exitoso

---

> **Documento creado:** 2025-12-05
> **Issue:** MOL-31
