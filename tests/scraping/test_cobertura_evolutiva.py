"""
Test rápido de la función de cobertura evolutiva
Verifica que los datos históricos se cargan correctamente
"""

from dashboard import data_loaders as dl

print("="*70)
print("TEST: Carga de Cobertura Temporal Evolutiva")
print("="*70)
print()

# Cargar datos históricos completos
df = dl.cargar_cobertura_temporal_completa(dias=30)

print(f"Total de registros históricos: {len(df)}")
print()

if not df.empty:
    print("Columnas disponibles:")
    for col in df.columns:
        print(f"  - {col}")
    print()

    print("Datos históricos (últimas 5 filas):")
    print(df.tail(5).to_string())
    print()

    print("RESUMEN:")
    print(f"  Fecha más antigua: {df['fecha'].min()}")
    print(f"  Fecha más reciente: {df['fecha'].max()}")
    print(f"  Total API promedio: {df['total_api'].mean():.0f}")
    print(f"  Total scrapeado promedio: {df['total_scrapeado'].mean():.0f}")
    print(f"  Cobertura promedio: {df['cobertura_pct'].mean():.2f}%")
    print(f"  Gap promedio: {df['gap'].mean():.0f}")
else:
    print("⚠️ No se encontraron datos históricos")

print()
print("="*70)
