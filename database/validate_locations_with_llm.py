#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validación automática de ubicaciones ambiguas usando LLM
=========================================================

Valida las 50 ubicaciones ambiguas exportadas usando Ollama (llama3.1:8b)
para determinar si la normalización provincia/código/localidad es correcta.

Uso:
    python validate_locations_with_llm.py           # Procesar todas (50)
    python validate_locations_with_llm.py --limit 5  # Testing con 5

Requisitos:
    - Ollama corriendo: ollama serve
    - Modelo descargado: ollama pull llama3.1:8b
"""

import sqlite3
import csv
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import time


class LocationValidator:
    """
    Validador de ubicaciones geográficas usando LLM local
    """

    def __init__(
        self,
        db_path: str,
        csv_path: str,
        model: str = "llama3.1:8b",
        api_url: str = "http://localhost:11434/api/generate",
        timeout: int = 60
    ):
        self.db_path = db_path
        self.csv_path = csv_path
        self.model = model
        self.api_url = api_url
        self.timeout = timeout

        # Cargar tabla INDEC desde BD
        self.provincias_indec = self._load_provincias_indec()

    def _load_provincias_indec(self) -> Dict[str, Dict]:
        """Carga tabla de provincias INDEC desde BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo_provincia, nombre_oficial, nombre_comun, variantes
            FROM indec_provincias
            ORDER BY codigo_provincia
        """)

        provincias = {}
        for row in cursor.fetchall():
            codigo, nombre_oficial, nombre_comun, variantes_json = row
            variantes = json.loads(variantes_json) if variantes_json else []
            provincias[codigo] = {
                'nombre_oficial': nombre_oficial,
                'nombre_comun': nombre_comun,
                'variantes': variantes
            }

        conn.close()
        return provincias

    def _get_oferta_descripcion(self, id_oferta: int) -> Optional[str]:
        """
        Obtiene descripción de una oferta desde la BD

        Args:
            id_oferta: ID de la oferta

        Returns:
            Descripción de la oferta o None si no existe
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Intentar descripcion_utf8 primero, luego descripcion, luego titulo
        cursor.execute("""
            SELECT COALESCE(descripcion_utf8, descripcion, titulo) as texto
            FROM ofertas
            WHERE id_oferta = ?
        """, (id_oferta,))

        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]
        else:
            return None

    def _build_provincias_table_text(self) -> str:
        """Construye tabla de provincias para el prompt"""
        lines = ["CODIGOS INDEC DE PROVINCIAS ARGENTINAS (24 jurisdicciones):"]

        for codigo, data in sorted(self.provincias_indec.items()):
            nombre = data['nombre_comun']
            variantes = data['variantes']

            if variantes:
                var_text = f" ({', '.join(variantes[:3])})"
            else:
                var_text = ""

            lines.append(f"{codigo} - {nombre}{var_text}")

        # Agregar reglas críticas
        lines.extend([
            "",
            "REGLAS CRITICAS:",
            "- 'Capital Federal' = código 02 (CABA), NO código 06",
            "- 'Ciudad de Buenos Aires' = código 02 (CABA), NO código 06",
            "- 'CABA' = código 02, NO código 06",
            "- Barrios de CABA (Núñez, Palermo, Belgrano, Recoleta) = código 02",
            "- Municipios del GBA (Pilar, Vicente López, San Isidro, La Matanza) = código 06",
            "- 'Buenos Aires' ambiguo → analizar descripción de oferta"
        ])

        return "\n".join(lines)

    def _build_validation_prompt(
        self,
        ubicacion_original: str,
        provincia_actual: str,
        codigo_actual: str,
        localidad_actual: str,
        descripcion_oferta: str
    ) -> str:
        """Construye el prompt de validación"""

        tabla_provincias = self._build_provincias_table_text()

        # Limpiar descripción (manejar encoding issues y limitar tamaño)
        if descripcion_oferta:
            desc_clean = descripcion_oferta[:1500]  # Limitar a 1500 chars
            # Reemplazar caracteres problemáticos
            desc_clean = desc_clean.replace('\x00', '').replace('�', '')
        else:
            desc_clean = "[SIN DESCRIPCION DISPONIBLE]"

        prompt = f"""Eres un experto en geografía argentina. Valida si esta ubicación fue normalizada correctamente según códigos INDEC.

{tabla_provincias}

DATOS DE LA OFERTA:
- Ubicación original: "{ubicacion_original}"
- Provincia asignada: {provincia_actual}
- Código INDEC asignado: {codigo_actual}
- Localidad asignada: {localidad_actual}

DESCRIPCION DE LA OFERTA LABORAL:
{desc_clean}

INSTRUCCIONES:
1. Analiza la descripción buscando pistas geográficas (barrios, zonas, referencias a CABA/GBA)
2. Determina si la normalización actual es CORRECTA o INCORRECTA
3. Si es incorrecta, identifica provincia, código y localidad correctos según tabla INDEC

CASOS ESPECIALES:
- "Capital Federal, Buenos Aires" → Casi siempre es CABA (código 02), no provincia (06)
- "Buenos Aires, Buenos Aires" → Puede ser ciudad en provincia (06) o error que debería ser CABA (02)
- Localidades del GBA mencionando "Buenos Aires" → código 06 es correcto

RESPONDE EXCLUSIVAMENTE EN JSON (sin markdown ni texto adicional):
{{
  "es_correcta": true,
  "provincia_correcta": null,
  "codigo_correcto": null,
  "localidad_correcta": null,
  "razonamiento": "Explicación breve de tu decisión",
  "confianza": 0.85
}}

IMPORTANTE:
- Si es_correcta = true, entonces provincia_correcta, codigo_correcto y localidad_correcta deben ser null
- Si es_correcta = false, proporciona los valores correctos
- Responde SOLO con el JSON, sin markdown ni texto adicional
- confianza: 0.0 (muy inseguro) a 1.0 (muy seguro)"""

        return prompt

    def _call_llm(self, prompt: str, temperature: float = 0.1) -> Optional[str]:
        """Llama a Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 600,  # Aumentado para evitar cortes
                }
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"      [ERROR] API {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            print("      [ERROR] LLM timeout")
            return None
        except Exception as e:
            print(f"      [ERROR] LLM call: {e}")
            return None

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parsea respuesta JSON del LLM"""

        # Pre-procesamiento: agregar comillas a codigo_correcto si es número
        import re
        response = re.sub(r'"codigo_correcto":\s*(\d+)', r'"codigo_correcto": "\1"', response)

        try:
            # Intentar parsear directamente
            parsed = json.loads(response)
            # Convertir codigo_correcto a string con padding si es necesario
            if parsed.get('codigo_correcto') is not None:
                parsed['codigo_correcto'] = str(parsed['codigo_correcto']).zfill(2)
            return parsed
        except json.JSONDecodeError:
            # Intentar extraer JSON si está envuelto en markdown o texto
            try:
                # Buscar entre ```json ... ``` o { ... }
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    # Aplicar mismo pre-procesamiento
                    json_str = re.sub(r'"codigo_correcto":\s*(\d+)', r'"codigo_correcto": "\1"', json_str)
                    parsed = json.loads(json_str)
                    # Convertir codigo_correcto a string con padding
                    if parsed.get('codigo_correcto') is not None:
                        parsed['codigo_correcto'] = str(parsed['codigo_correcto']).zfill(2)
                    return parsed
            except Exception as e:
                print(f"      [DEBUG] Error parsing: {str(e)}")
                pass

            print(f"      [ERROR] No se pudo parsear JSON: {response[:300]}")
            return None

    def validate_ubicacion(
        self,
        ubicacion_original: str,
        provincia_actual: str,
        codigo_actual: str,
        localidad_actual: str,
        ejemplo_id_oferta: int
    ) -> Dict:
        """
        Valida una ubicación usando LLM

        Returns:
            Dict con resultado de validación
        """
        # 1. Obtener descripción de la oferta
        descripcion = self._get_oferta_descripcion(ejemplo_id_oferta)

        if not descripcion:
            return {
                'es_correcta': None,
                'provincia_correcta': None,
                'codigo_correcto': None,
                'localidad_correcta': None,
                'razonamiento': 'No se pudo obtener descripción de la oferta',
                'confianza': 0.0
            }

        # 2. Construir prompt
        prompt = self._build_validation_prompt(
            ubicacion_original,
            provincia_actual,
            codigo_actual,
            localidad_actual,
            descripcion
        )

        # 3. Llamar a LLM
        response = self._call_llm(prompt, temperature=0.1)

        if not response:
            return {
                'es_correcta': None,
                'provincia_correcta': None,
                'codigo_correcto': None,
                'localidad_correcta': None,
                'razonamiento': 'Error en llamada a LLM',
                'confianza': 0.0
            }

        # 4. Parsear respuesta
        parsed = self._parse_json_response(response)

        if not parsed:
            return {
                'es_correcta': None,
                'provincia_correcta': None,
                'codigo_correcto': None,
                'localidad_correcta': None,
                'razonamiento': 'Error parseando respuesta LLM',
                'confianza': 0.0
            }

        return parsed

    def process_csv(self, output_csv: Optional[str] = None, limit: Optional[int] = None):
        """
        Procesa el CSV de ubicaciones ambiguas y escribe resultados

        Args:
            output_csv: Ruta del CSV de salida (None = sobrescribe original)
            limit: Limitar a N ubicaciones para testing (None = todas)
        """
        print("=" * 80)
        print("VALIDACION AUTOMATICA DE UBICACIONES CON LLM")
        print("=" * 80)
        print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Modelo LLM: {self.model}")
        print(f"CSV entrada: {self.csv_path}")
        print(f"Limite: {limit if limit else 'TODAS (50)'}\n")

        # Leer CSV
        ubicaciones = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                ubicaciones.append(row)

        print(f"[OK] {len(ubicaciones)} ubicaciones cargadas\n")
        print("Procesando...")
        print("-" * 80)

        # Procesar cada ubicación
        start_time = time.time()
        resultados = []

        stats = {
            'correctas': 0,
            'incorrectas': 0,
            'errores': 0,
            'confianza_alta': 0,  # >= 0.8
            'confianza_media': 0,  # 0.6-0.79
            'confianza_baja': 0   # < 0.6
        }

        for i, ub in enumerate(ubicaciones, 1):
            print(f"\n[{i}/{len(ubicaciones)}] {ub['ubicacion_original']}")
            print(f"    Actual: {ub['provincia_normalizada_actual']} (cod {ub['codigo_provincia_actual']}) - {ub['localidad_normalizada_actual']}")

            try:
                # Validar con LLM
                resultado = self.validate_ubicacion(
                    ubicacion_original=ub['ubicacion_original'],
                    provincia_actual=ub['provincia_normalizada_actual'],
                    codigo_actual=ub['codigo_provincia_actual'],
                    localidad_actual=ub['localidad_normalizada_actual'],
                    ejemplo_id_oferta=int(ub['ejemplo_id_oferta'])
                )

                # Estadísticas de confianza
                conf = resultado.get('confianza', 0.0)
                if conf >= 0.8:
                    stats['confianza_alta'] += 1
                elif conf >= 0.6:
                    stats['confianza_media'] += 1
                else:
                    stats['confianza_baja'] += 1

                # Actualizar fila con resultados
                if resultado.get('es_correcta'):
                    ub['provincia_normalizada_CORRECTA'] = ''
                    ub['codigo_provincia_CORRECTO'] = ''
                    ub['localidad_normalizada_CORRECTA'] = ''
                    stats['correctas'] += 1
                elif resultado.get('es_correcta') is False:
                    ub['provincia_normalizada_CORRECTA'] = resultado.get('provincia_correcta') or ''
                    ub['codigo_provincia_CORRECTO'] = resultado.get('codigo_correcto') or ''
                    ub['localidad_normalizada_CORRECTA'] = resultado.get('localidad_correcta') or ''
                    stats['incorrectas'] += 1
                else:
                    # Error o no determinado
                    ub['provincia_normalizada_CORRECTA'] = ''
                    ub['codigo_provincia_CORRECTO'] = ''
                    ub['localidad_normalizada_CORRECTA'] = ''
                    stats['errores'] += 1

                ub['comentarios'] = f"{resultado.get('razonamiento', '')} (conf: {conf:.2f})"

                # Mostrar resultado
                if resultado.get('es_correcta'):
                    print(f"    Resultado: CORRECTA [OK]")
                elif resultado.get('es_correcta') is False:
                    print(f"    Resultado: INCORRECTA [X]")
                    print(f"    Sugerencia: {resultado.get('provincia_correcta')} (cod {resultado.get('codigo_correcto')}) - {resultado.get('localidad_correcta')}")
                else:
                    print(f"    Resultado: ERROR/NO_DETERMINADO [?]")

                print(f"    Razonamiento: {resultado.get('razonamiento', 'N/A')[:100]}")
                print(f"    Confianza: {conf:.2f}")

                resultados.append(ub)

                # Pequeño delay para no saturar
                time.sleep(0.5)

            except Exception as e:
                print(f"    [ERROR] {str(e)}")
                ub['comentarios'] = f"ERROR: {str(e)}"
                ub['provincia_normalizada_CORRECTA'] = ''
                ub['codigo_provincia_CORRECTO'] = ''
                ub['localidad_normalizada_CORRECTA'] = ''
                stats['errores'] += 1
                resultados.append(ub)

        # Escribir CSV de salida
        output_path = output_csv or self.csv_path

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(resultados[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(resultados)

        # Estadísticas finales
        elapsed = time.time() - start_time
        avg_time = elapsed / len(ubicaciones) if len(ubicaciones) > 0 else 0

        print("\n" + "=" * 80)
        print("RESUMEN DE VALIDACION")
        print("=" * 80)

        print(f"\nUbicaciones procesadas: {len(resultados)}")
        print(f"  - Correctas: {stats['correctas']}")
        print(f"  - Incorrectas: {stats['incorrectas']}")
        print(f"  - Errores: {stats['errores']}")

        print(f"\nDistribución de confianza:")
        print(f"  - Alta (>=0.8): {stats['confianza_alta']}")
        print(f"  - Media (0.6-0.79): {stats['confianza_media']}")
        print(f"  - Baja (<0.6): {stats['confianza_baja']}")

        print(f"\nTiempo total: {elapsed:.1f} segundos ({elapsed/60:.1f} minutos)")
        print(f"Tiempo promedio por ubicación: {avg_time:.1f} segundos")
        print(f"\nResultados guardados en: {output_path}")

        # Próximos pasos
        print("\n" + "=" * 80)
        print("PROXIMOS PASOS")
        print("=" * 80)

        if stats['incorrectas'] > 0:
            print(f"\n1. Revisar las {stats['incorrectas']} ubicaciones marcadas como incorrectas")
            print(f"2. Especialmente revisar las {stats['confianza_baja'] + stats['confianza_media']} con confianza < 0.8")
            print(f"3. Ajustar manualmente en el CSV si es necesario")
            print(f"4. Ejecutar: python apply_location_corrections.py")
        else:
            print("\n[OK] Todas las ubicaciones fueron validadas como correctas")
            print("No es necesario ejecutar apply_location_corrections.py")
            print("\nContinuar con TAREA 2: Testing extendido NLP v6.0")

        print("\n" + "=" * 80)
        print("VALIDACION COMPLETADA")
        print("=" * 80)


def test_connection(model: str = "llama3.1:8b") -> bool:
    """Prueba conexión con Ollama"""
    try:
        print("Probando conexión con Ollama...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": "Test: responde solo 'OK'",
                "stream": False,
                "options": {"num_predict": 10}
            },
            timeout=10
        )

        if response.status_code == 200:
            print("[OK] Conexión exitosa\n")
            return True
        else:
            print(f"[ERROR] Status code: {response.status_code}\n")
            return False

    except Exception as e:
        print(f"[ERROR] Conexión fallida: {e}\n")
        return False


def main():
    """Ejecuta validación automática"""

    # Parsear argumentos
    parser = argparse.ArgumentParser(
        description="Validación automática de ubicaciones con LLM"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limitar a N ubicaciones para testing (default: todas)'
    )
    args = parser.parse_args()

    # Paths
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    csv_path = Path(__file__).parent / "ubicaciones_ambiguas_validacion.csv"

    # Validar archivos
    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada: {db_path}")
        return

    if not csv_path.exists():
        print(f"ERROR: CSV no encontrado: {csv_path}")
        print("\nPRIMERO ejecuta: python export_ambiguous_locations.py")
        return

    # Test de conexión
    if not test_connection():
        print("\nERROR: No se puede conectar a Ollama")
        print("\nPasos para resolver:")
        print("1. Asegurate de que Ollama esté corriendo: ollama serve")
        print("2. Verifica que el modelo esté descargado: ollama pull llama3.1:8b")
        print("3. Prueba manualmente: ollama run llama3.1:8b")
        return

    # Crear validador
    validator = LocationValidator(
        db_path=str(db_path),
        csv_path=str(csv_path),
        model="llama3.1:8b",
        timeout=60
    )

    # Procesar CSV
    validator.process_csv(
        output_csv=None,  # Sobrescribe CSV original
        limit=args.limit
    )


if __name__ == "__main__":
    main()
