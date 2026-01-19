"""
Script para ejecutar el schema de usuarios en Supabase
"""
import sys

try:
    import psycopg2
except ImportError:
    print("Instalando psycopg2...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2

# Connection string
conn_string = "postgresql://postgres:kfAPRug.h85H.D9@db.uywzoyhjjofsvvsrrnek.supabase.co:5432/postgres"

print("Conectando a Supabase PostgreSQL...")

try:
    conn = psycopg2.connect(conn_string, connect_timeout=30)
    print("Conexion exitosa!")

    # Leer SQL
    with open("D:/OEDE/Webscrapping/fase3_dashboard/sql/001_usuarios_multitenant.sql", encoding="utf-8") as f:
        sql = f.read()

    print("Ejecutando SQL...")
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print("SQL ejecutado correctamente!")

    # Verificar tablas creadas
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('organizaciones', 'usuarios', 'busquedas_guardadas', 'intereses', 'alertas')
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    print(f"Tablas creadas: {[t[0] for t in tables]}")

    # Verificar org OEDE
    cur.execute("SELECT nombre, tipo FROM organizaciones LIMIT 1")
    org = cur.fetchone()
    if org:
        print(f"Organizacion inicial: {org[0]} ({org[1]})")

    cur.close()
    conn.close()
    print("Listo!")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
