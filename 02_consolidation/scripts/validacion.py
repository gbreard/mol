"""
Validación de datos contra el schema unificado
"""

import pandas as pd
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ValidadorSchema:
    """Valida datos contra el schema unificado"""

    def __init__(self, schema_path: Path = None):
        if schema_path is None:
            project_root = Path(__file__).parent.parent.parent
            schema_path = project_root / "shared" / "schemas" / "schema_unificado.json"

        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)

    def validar_dataframe(self, df: pd.DataFrame, strict=False) -> dict:
        """
        Valida DataFrame completo

        Returns:
            dict con resultados de validación
        """
        logger.info("Validando datos contra schema...")

        resultados = {
            'valido': True,
            'errores': [],
            'warnings': [],
            'estadisticas': {}
        }

        # Validar campos requeridos
        campos_requeridos = [
            '_metadata.source',
            '_metadata.source_id',
            'informacion_basica.titulo',
            'informacion_basica.empresa',
            '_metadata.url_oferta',
            '_metadata.fecha_extraccion'
        ]

        for campo in campos_requeridos:
            if campo not in df.columns:
                resultados['errores'].append(f"Campo requerido faltante: {campo}")
                resultados['valido'] = False
            else:
                # Verificar valores nulos
                nulos = df[campo].isna().sum()
                if nulos > 0:
                    msg = f"Campo {campo} tiene {nulos} valores nulos"
                    if strict:
                        resultados['errores'].append(msg)
                        resultados['valido'] = False
                    else:
                        resultados['warnings'].append(msg)

        # Estadísticas
        resultados['estadisticas'] = {
            'total_ofertas': len(df),
            'campos_totales': len(df.columns),
            'errores': len(resultados['errores']),
            'warnings': len(resultados['warnings'])
        }

        if resultados['valido']:
            logger.info("✓ Validación exitosa")
        else:
            logger.error(f"✗ Validación falló con {len(resultados['errores'])} errores")

        return resultados


def validar_schema(df: pd.DataFrame, strict=False):
    """Función helper para validar DataFrame"""
    validador = ValidadorSchema()
    return validador.validar_dataframe(df, strict=strict)


if __name__ == "__main__":
    print("Módulo de validación - importar desde consolidar_fuentes.py")
