#!/usr/bin/env python3
"""
MOL-31: Test de conexión a S3

Verifica que las credenciales están configuradas correctamente
y que se puede leer/escribir en el bucket.

Uso:
    python scripts/test_s3_connection.py
    python scripts/test_s3_connection.py --write  # También prueba escritura
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def load_credentials():
    """Cargar credenciales desde archivo o variables de entorno."""

    # Opción 1: Variables de entorno
    if os.environ.get('AWS_ACCESS_KEY_ID'):
        return {
            'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
            'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
            'region': os.environ.get('AWS_REGION', 'us-east-1'),
            'bucket': os.environ.get('S3_BUCKET', 'mol-validation-data')
        }

    # Opción 2: Archivo de configuración
    config_file = ROOT_DIR / 'config' / 'aws_credentials.json'
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)

    # No encontrado
    return None


def test_connection(write_test=False):
    """Ejecutar tests de conexión a S3."""

    print("=" * 60)
    print("MOL-31: Test de Conexión S3")
    print("=" * 60)
    print()

    # 1. Cargar credenciales
    print("[1/5] Cargando credenciales...")
    credentials = load_credentials()

    if not credentials:
        print("  [ERROR] No se encontraron credenciales.")
        print("  Opciones:")
        print("    - Crear config/aws_credentials.json (copiar de .example)")
        print("    - Configurar variables de entorno AWS_ACCESS_KEY_ID, etc.")
        return False

    print(f"  [OK] Credenciales cargadas")
    print(f"       Region: {credentials['region']}")
    print(f"       Bucket: {credentials['bucket']}")
    print(f"       Access Key: {credentials['aws_access_key_id'][:8]}...")
    print()

    # 2. Verificar boto3
    print("[2/5] Verificando boto3...")
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        print(f"  [OK] boto3 version {boto3.__version__}")
    except ImportError:
        print("  [ERROR] boto3 no está instalado.")
        print("  Ejecutar: pip install boto3")
        return False
    print()

    # 3. Crear cliente S3
    print("[3/5] Conectando a S3...")
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=credentials['aws_access_key_id'],
            aws_secret_access_key=credentials['aws_secret_access_key'],
            region_name=credentials['region']
        )
        print("  [OK] Cliente S3 creado")
    except Exception as e:
        print(f"  [ERROR] No se pudo crear cliente: {e}")
        return False
    print()

    # 4. Listar contenido del bucket
    print("[4/5] Listando contenido del bucket...")
    bucket = credentials['bucket']
    try:
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=10)

        if 'Contents' in response:
            print(f"  [OK] Bucket accesible. Objetos encontrados:")
            for obj in response['Contents'][:5]:
                size_kb = obj['Size'] / 1024
                print(f"       - {obj['Key']} ({size_kb:.1f} KB)")
            if response['KeyCount'] > 5:
                print(f"       ... y {response['KeyCount'] - 5} más")
        else:
            print("  [OK] Bucket accesible (vacío)")

        # Verificar carpetas esperadas
        prefixes = ['snapshots/', 'gold_set/', 'config/']
        print()
        print("  Verificando estructura de carpetas:")
        for prefix in prefixes:
            try:
                check = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
                exists = 'Contents' in check or 'CommonPrefixes' in check
                status = "[OK]" if exists else "[WARN] No existe"
                print(f"       {prefix} {status}")
            except:
                print(f"       {prefix} [ERROR]")

    except NoCredentialsError:
        print("  [ERROR] Credenciales inválidas")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print("  [ERROR] Acceso denegado. Verificar política IAM.")
        elif error_code == 'NoSuchBucket':
            print(f"  [ERROR] Bucket '{bucket}' no existe.")
        else:
            print(f"  [ERROR] {error_code}: {e.response['Error']['Message']}")
        return False
    print()

    # 5. Test de escritura (opcional)
    if write_test:
        print("[5/5] Probando escritura...")
        test_key = 'config/_test_connection.json'
        test_data = {
            'test': True,
            'timestamp': datetime.now().isoformat(),
            'source': 'test_s3_connection.py'
        }

        try:
            # Escribir
            s3.put_object(
                Bucket=bucket,
                Key=test_key,
                Body=json.dumps(test_data),
                ContentType='application/json'
            )
            print(f"  [OK] Archivo escrito: {test_key}")

            # Leer
            response = s3.get_object(Bucket=bucket, Key=test_key)
            content = json.loads(response['Body'].read().decode('utf-8'))
            print(f"  [OK] Archivo leído correctamente")

            # Eliminar
            s3.delete_object(Bucket=bucket, Key=test_key)
            print(f"  [OK] Archivo eliminado")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                print("  [ERROR] Sin permiso de escritura. Verificar política IAM.")
            else:
                print(f"  [ERROR] {error_code}: {e.response['Error']['Message']}")
            return False
    else:
        print("[5/5] Test de escritura omitido (usar --write para incluir)")

    print()
    print("=" * 60)
    print("RESULTADO: [OK] Conexión exitosa")
    print("=" * 60)
    return True


def main():
    """Punto de entrada."""
    write_test = '--write' in sys.argv

    success = test_connection(write_test=write_test)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
