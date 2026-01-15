# -*- coding: utf-8 -*-
"""Test directo del postprocessor para inferencia de area_funcional."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))

from nlp_postprocessor import NLPPostprocessor

pp = NLPPostprocessor(verbose=True)

# Test case: Tecnico Electromecanico
data = {
    'titulo_limpio': 'Tecnico Electromecanico - Zona San Vicente',
    'area_funcional': None
}
descripcion = 'Buscamos tecnico electromecanico para mantenimiento de equipos industriales.'

print("INPUT:")
print(f"  titulo_limpio: {data['titulo_limpio']}")
print(f"  area_funcional: {data['area_funcional']}")
print(f"  descripcion: {descripcion[:80]}...")
print()

result = pp.postprocess(data, descripcion)

print("\nRESULTADO:")
print(f"  area_funcional: {result.get('area_funcional')}")
