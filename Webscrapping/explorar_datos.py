import pandas as pd

df = pd.read_excel('ofertas_consolidadas.xlsx', sheet_name='BASE')

print('=== PROVINCIAS ===')
print(df['ubicacion.provincia'].value_counts().head(15))
print(f"\nTotal registros con provincia: {df['ubicacion.provincia'].notna().sum()}")
print(f"Total registros sin provincia: {df['ubicacion.provincia'].isna().sum()}")

print('\n=== CIUDADES ===')
print(df['ubicacion.ciudad'].value_counts().head(15))

print('\n=== MODALIDAD ===')
cols_mod = [c for c in df.columns if 'modalidad' in c.lower()]
print(f'Columnas con modalidad: {cols_mod}')
if cols_mod:
    for col in cols_mod:
        print(f"\n{col}:")
        print(df[col].value_counts())

print('\n=== TODAS LAS COLUMNAS ===')
print(f"Total: {len(df.columns)} columnas")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")
