# Validación de esquema de matching_rules_business.json (FRENTE H, P0.a.3, 2026-08-06).
# El matcher v3 evalúa un set FIJO de claves; una clave desconocida se ignora EN
# SILENCIO (una regla puede disparar más ancho que su diseño — caso R4: sus guardas
# nlp_seniority_es/nlp_tiene_gente_cargo no se evalúan). Este test:
#   1. FALLA si una regla NUEVA (fuera de la lista legacy conocida) usa claves que
#      el matcher no implementa — que el drift no entre más en silencio.
#   2. Documenta el inventario legacy congelado (las 6 reglas pre-v3 conocidas).
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Claves de condición implementadas en match_ofertas_v3 (rama bypass, v3.5.9)
CONDICION_IMPLEMENTADAS = {
    'titulo_contiene_alguno', 'titulo_contiene_alguno_2', 'titulo_contiene_todos',
    'titulo_o_tareas_contiene_alguno', 'titulo_original_contiene_alguno',
    'skills_contiene_alguno', 'area_funcional_es', 'sector_es',
    'sector_empresa_es_alguno', 'titulo_no_contiene_alguno', 'sector_no_es',
    'area_funcional_no_es',
    # implementadas parcialmente / con semántica propia
    'titulo_contiene', 'titulo_no_contiene', 'tareas_contiene_alguno',
    'area_funcional_es_alguno',
}
ACCION_IMPLEMENTADAS = {'forzar_isco', 'esco_label', 'esco_code'}

# Reglas legacy pre-v3 con claves fuera del set (documentadas, congeladas):
# R4/R6/R7/R9 = priorización (rama aparte), R10/R11 = activa:false.
# NO agregar reglas nuevas acá: una regla nueva con clave desconocida debe FALLAR.
LEGACY_CONGELADAS = {'R4_nivel_gerencial', 'R6_sector_gastronomia', 'R7_sector_educacion',
                     'R9_tareas_logisticas', 'R10_electricista_industrial', 'R11_titulo_compuesto'}

# Reglas con guardas NLP escritas pero JAMAS aplicadas por el matcher (disparan mas
# ancho que su diseño). Pendiente Eje 4: implementar la guarda o revalidar con Cyn.
# NO se retiran las claves (retirarlas bendeciria el comportamiento ancho en silencio).
GUARDAS_NO_APLICADAS = {'R94_jefe_sucursal_financiera', 'R95_tech_lead_ia_ml'}


def _reglas():
    d = json.load(open(REPO / 'config' / 'matching_rules_business.json'))['reglas_forzar_isco']
    return {k: v for k, v in d.items()
            if isinstance(v, dict) and not k.startswith('_') and k != 'descripcion'}


def test_condiciones_solo_claves_implementadas():
    problemas = []
    for rid, r in _reglas().items():
        if rid in LEGACY_CONGELADAS or rid in GUARDAS_NO_APLICADAS:
            continue
        desconocidas = set(r.get('condicion', {})) - CONDICION_IMPLEMENTADAS
        if desconocidas:
            problemas.append(f'{rid}: condicion con claves NO implementadas {sorted(desconocidas)}')
    assert not problemas, 'Claves de condicion que el matcher ignoraria EN SILENCIO:\n' + '\n'.join(problemas)


def test_acciones_solo_claves_implementadas():
    problemas = []
    for rid, r in _reglas().items():
        if rid in LEGACY_CONGELADAS or rid in GUARDAS_NO_APLICADAS:
            continue
        desconocidas = set(r.get('accion', {})) - ACCION_IMPLEMENTADAS
        if desconocidas:
            problemas.append(f'{rid}: accion con claves NO implementadas {sorted(desconocidas)}')
    assert not problemas, 'Claves de accion que el matcher ignoraria EN SILENCIO:\n' + '\n'.join(problemas)


def test_targets_resuelven_en_catalogo():
    cat = {o['esco_code'] for o in json.load(open(REPO / 'database' / 'embeddings' / 'esco_occupations_metadata.json')) if o.get('esco_code')}
    labels = {o['esco_label'] for o in json.load(open(REPO / 'database' / 'embeddings' / 'esco_occupations_metadata.json'))}
    problemas = []
    for rid, r in _reglas().items():
        if rid in LEGACY_CONGELADAS or rid in GUARDAS_NO_APLICADAS:
            continue
        acc = r.get('accion', {})
        ec, el = acc.get('esco_code'), acc.get('esco_label')
        if ec and str(ec) not in cat:
            problemas.append(f'{rid}: esco_code {ec} no existe en catalogo')
        elif not ec and el and el not in labels:
            problemas.append(f'{rid}: esco_label no resuelve exacto: {el!r}')
        elif not ec and not el:
            problemas.append(f'{rid}: sin target (ni esco_code ni esco_label)')
    assert not problemas, 'Targets muertos:\n' + '\n'.join(problemas)
