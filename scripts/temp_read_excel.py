import pandas as pd

file_path = 'D:/OEDE/Webscrapping/docs/gold_set_completo_20260105_1224_verificación.xlsx'

# Skills del Excel para ID 1118027834
df_skills = pd.read_excel(file_path, sheet_name='Skills_Detalle')
skills_id = df_skills[df_skills['ID_Oferta'] == 1118027834]

print('=== SKILLS EN EXCEL PARA ID 1118027834 ===')
print(f'Total skills: {len(skills_id)}')
print()
print(f"{'Skill':<50} {'Score':<8} {'L1':<6} {'Digital':<8} {'Origen':<10}")
print('-' * 90)
for _, row in skills_id.iterrows():
    skill = str(row.get('Skill', '?'))[:48]
    score = row.get('Score', '?')
    l1 = row.get('L1', '?')
    digital = row.get('Es_Digital', '?')
    origen = row.get('Origen', '?')
    print(f'{skill:<50} {score:<8} {l1:<6} {digital:<8} {origen:<10}')

# NLP+Matching del Excel
print('\n\n=== NLP+MATCHING EN EXCEL PARA ID 1118027834 ===')
df_nlp = pd.read_excel(file_path, sheet_name='Ofertas_NLP_Matching')
row_nlp = df_nlp[df_nlp['ID'] == 1118027834].iloc[0]
campos_clave = ['Titulo_Limpio', 'Sector', 'Area_Funcional', 'Seniority', 'Modalidad',
                'ISCO_Code', 'ESCO_Label', 'Match_Score', 'Match_Method']
for campo in campos_clave:
    if campo in row_nlp.index:
        print(f'{campo}: {row_nlp[campo]}')
