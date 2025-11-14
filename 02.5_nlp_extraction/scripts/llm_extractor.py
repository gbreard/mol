# -*- coding: utf-8 -*-
"""
LLM Extractor - FASE 3 (v4.0)
==============================

Extractor NLP usando Llama 3 local via Ollama para refinamiento de campos vacíos.
Arquitectura híbrida: Regex v3.7 (base rápida) + LLM (refinamiento preciso)

Modelo: llama3:latest (4.7 GB)
Optimizado para: Español
"""

import json
import requests
from typing import Dict, Optional, List, Any
from datetime import datetime


class LLMExtractor:
    """
    Extractor NLP usando Llama 3 local via Ollama

    Procesa solo campos vacíos para optimizar tiempo y recursos.
    """

    def __init__(
        self,
        model: str = "llama3:latest",
        api_url: str = "http://localhost:11434/api/generate",
        timeout: int = 30
    ):
        """
        Inicializa el extractor LLM

        Args:
            model: Nombre del modelo Ollama (default: llama3:latest)
            api_url: URL de la API de Ollama
            timeout: Timeout en segundos para cada request
        """
        self.model = model
        self.api_url = api_url
        self.timeout = timeout
        self.version = "v4.0.0"

    def _call_llm(self, prompt: str, temperature: float = 0.1) -> Optional[str]:
        """
        Llama al LLM via Ollama API

        Args:
            prompt: Prompt a enviar
            temperature: Temperature para sampling (0.1 = más determinístico)

        Returns:
            Respuesta del LLM o None si error
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 200,  # Máximo tokens de respuesta
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
                print(f"[ERROR] LLM API: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("[ERROR] LLM timeout")
            return None
        except Exception as e:
            print(f"[ERROR] LLM call: {e}")
            return None

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Parsea respuesta JSON del LLM

        Args:
            response: String con JSON

        Returns:
            Dict parseado o None si error
        """
        try:
            # Intentar parsear directamente
            return json.loads(response)
        except json.JSONDecodeError:
            # Intentar extraer JSON de la respuesta
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            return None

    # ========================================================================
    # PROMPTS OPTIMIZADOS EN ESPAÑOL
    # ========================================================================

    def extract_experiencia(self, titulo: str, descripcion: str) -> Dict:
        """
        Extrae años de experiencia requeridos

        Returns:
            {
                'experiencia_min_anios': int o None,
                'experiencia_max_anios': int o None,
                'confidence': float
            }
        """
        prompt = f"""Analiza esta oferta laboral y extrae los años de experiencia requeridos.

TÍTULO: {titulo}

DESCRIPCIÓN:
{descripcion[:800]}

INSTRUCCIONES:
- Si menciona "X años", "X+ años", "mínimo X años" → experiencia_min_anios = X
- Si menciona "entre X y Y años" → experiencia_min_anios = X, experiencia_max_anios = Y
- Si solo dice "experiencia", "con experiencia", "experiencia previa" → experiencia_min_anios = 1
- Si NO menciona experiencia → ambos = null

RESPONDE SOLO CON JSON (sin texto adicional):
{{"experiencia_min_anios": <numero o null>, "experiencia_max_anios": <numero o null>}}"""

        response = self._call_llm(prompt, temperature=0.1)
        if not response:
            return {'experiencia_min_anios': None, 'experiencia_max_anios': None, 'confidence': 0.0}

        parsed = self._parse_json_response(response)
        if parsed:
            return {
                'experiencia_min_anios': parsed.get('experiencia_min_anios'),
                'experiencia_max_anios': parsed.get('experiencia_max_anios'),
                'confidence': 0.8
            }
        else:
            return {'experiencia_min_anios': None, 'experiencia_max_anios': None, 'confidence': 0.0}

    def extract_educacion(self, titulo: str, descripcion: str) -> Dict:
        """
        Extrae nivel educativo requerido

        Returns:
            {
                'nivel_educativo': str o None,
                'estado_educativo': str o None,
                'confidence': float
            }
        """
        prompt = f"""Analiza esta oferta laboral y extrae el nivel educativo requerido.

TÍTULO: {titulo}

DESCRIPCIÓN:
{descripcion[:800]}

NIVELES VÁLIDOS:
- "secundario": Bachiller, secundaria, educación media
- "terciario": Técnico, tecnicatura, carrera corta
- "universitario": Licenciatura, ingeniería, grado universitario
- "posgrado": Maestría, doctorado, especialización

ESTADOS VÁLIDOS:
- "completo": Título obtenido, graduado
- "en_curso": Estudiando, cursando
- "incompleto": Incompleto, trunco

INSTRUCCIONES:
- Identifica el nivel educativo más alto mencionado
- Si dice "excluyente", "requisito", "indispensable" → estado = "completo"
- Si NO menciona requisitos educativos → ambos = null

RESPONDE SOLO CON JSON:
{{"nivel_educativo": "<nivel o null>", "estado_educativo": "<estado o null>"}}"""

        response = self._call_llm(prompt, temperature=0.1)
        if not response:
            return {'nivel_educativo': None, 'estado_educativo': None, 'confidence': 0.0}

        parsed = self._parse_json_response(response)
        if parsed:
            return {
                'nivel_educativo': parsed.get('nivel_educativo'),
                'estado_educativo': parsed.get('estado_educativo'),
                'confidence': 0.8
            }
        else:
            return {'nivel_educativo': None, 'estado_educativo': None, 'confidence': 0.0}

    def extract_skills_tecnicas(self, titulo: str, descripcion: str) -> Dict:
        """
        Extrae skills técnicas mencionadas

        Returns:
            {
                'skills_tecnicas_list': List[str] o None,
                'confidence': float
            }
        """
        prompt = f"""Analiza esta oferta laboral y extrae las skills técnicas requeridas.

TÍTULO: {titulo}

DESCRIPCIÓN:
{descripcion[:800]}

SKILLS TÉCNICAS son:
- Lenguajes de programación: Python, Java, JavaScript, C++, etc.
- Frameworks: Django, React, Angular, Spring, etc.
- Bases de datos: MySQL, PostgreSQL, MongoDB, SQL Server, etc.
- Herramientas: Git, Docker, AWS, Excel avanzado, SAP, etc.
- Software específico: AutoCAD, Photoshop, Office, etc.

NO incluyas:
- Soft skills (trabajo en equipo, proactividad, etc.)
- Idiomas (inglés, portugués, etc.)

INSTRUCCIONES:
- Lista SOLO las skills técnicas explícitamente mencionadas
- Máximo 10 skills
- Si NO hay skills técnicas → null

RESPONDE SOLO CON JSON:
{{"skills_tecnicas": ["skill1", "skill2", ...]}} o {{"skills_tecnicas": null}}"""

        response = self._call_llm(prompt, temperature=0.2)
        if not response:
            return {'skills_tecnicas_list': None, 'confidence': 0.0}

        parsed = self._parse_json_response(response)
        if parsed and parsed.get('skills_tecnicas'):
            skills = parsed['skills_tecnicas']
            # Convertir a JSON string para DB
            return {
                'skills_tecnicas_list': skills if isinstance(skills, list) else None,
                'confidence': 0.7
            }
        else:
            return {'skills_tecnicas_list': None, 'confidence': 0.0}

    def extract_soft_skills(self, titulo: str, descripcion: str) -> Dict:
        """
        Extrae soft skills mencionadas

        Returns:
            {
                'soft_skills_list': List[str] o None,
                'confidence': float
            }
        """
        prompt = f"""Analiza esta oferta laboral y extrae las soft skills (habilidades blandas) requeridas.

TÍTULO: {titulo}

DESCRIPCIÓN:
{descripcion[:800]}

SOFT SKILLS son habilidades personales como:
- Trabajo en equipo, liderazgo, comunicación
- Proactividad, responsabilidad, compromiso
- Organización, planificación, autonomía
- Resolución de problemas, pensamiento crítico
- Adaptabilidad, flexibilidad, iniciativa
- Atención al detalle, orientación a resultados

NO incluyas:
- Skills técnicas (Python, Excel, etc.)
- Idiomas
- Requisitos de educación o experiencia

INSTRUCCIONES:
- Lista SOLO soft skills explícitamente mencionadas
- Máximo 8 skills
- Si NO hay soft skills → null

RESPONDE SOLO CON JSON:
{{"soft_skills": ["skill1", "skill2", ...]}} o {{"soft_skills": null}}"""

        response = self._call_llm(prompt, temperature=0.2)
        if not response:
            return {'soft_skills_list': None, 'confidence': 0.0}

        parsed = self._parse_json_response(response)
        if parsed and parsed.get('soft_skills'):
            skills = parsed['soft_skills']
            return {
                'soft_skills_list': skills if isinstance(skills, list) else None,
                'confidence': 0.7
            }
        else:
            return {'soft_skills_list': None, 'confidence': 0.0}

    # ========================================================================
    # MÉTODO PRINCIPAL: REFINAR CAMPOS VACÍOS
    # ========================================================================

    def refine_empty_fields(
        self,
        titulo: str,
        descripcion: str,
        current_result: Dict,
        campos_a_refinar: Optional[List[str]] = None
    ) -> Dict:
        """
        Refina solo los campos vacíos usando LLM

        Args:
            titulo: Título del puesto
            descripcion: Descripción completa
            current_result: Resultado actual de regex v3.7
            campos_a_refinar: Lista de campos a refinar (None = todos los vacíos)

        Returns:
            Dict con campos refinados
        """
        resultado = current_result.copy()

        # Si no se especifican campos, refinar todos los vacíos
        if campos_a_refinar is None:
            campos_a_refinar = []
            if not resultado.get('experiencia_min_anios'):
                campos_a_refinar.append('experiencia')
            if not resultado.get('nivel_educativo'):
                campos_a_refinar.append('educacion')
            if not resultado.get('skills_tecnicas_list'):
                campos_a_refinar.append('skills_tecnicas')
            if not resultado.get('soft_skills_list'):
                campos_a_refinar.append('soft_skills')

        # Refinar cada campo
        for campo in campos_a_refinar:
            if campo == 'experiencia':
                exp_result = self.extract_experiencia(titulo, descripcion)
                if exp_result['confidence'] > 0.5:
                    resultado['experiencia_min_anios'] = exp_result['experiencia_min_anios']
                    resultado['experiencia_max_anios'] = exp_result['experiencia_max_anios']

            elif campo == 'educacion':
                edu_result = self.extract_educacion(titulo, descripcion)
                if edu_result['confidence'] > 0.5:
                    resultado['nivel_educativo'] = edu_result['nivel_educativo']
                    resultado['estado_educativo'] = edu_result['estado_educativo']

            elif campo == 'skills_tecnicas':
                skills_result = self.extract_skills_tecnicas(titulo, descripcion)
                if skills_result['confidence'] > 0.5:
                    resultado['skills_tecnicas_list'] = skills_result['skills_tecnicas_list']

            elif campo == 'soft_skills':
                soft_result = self.extract_soft_skills(titulo, descripcion)
                if soft_result['confidence'] > 0.5:
                    resultado['soft_skills_list'] = soft_result['soft_skills_list']

        # Actualizar versión a v4.0
        resultado['nlp_version'] = self.version

        return resultado


# ============================================================================
# FUNCIONES HELPER
# ============================================================================

def test_llm_connection(model: str = "llama3:latest") -> bool:
    """
    Prueba conexión con Ollama

    Returns:
        True si conecta correctamente
    """
    try:
        extractor = LLMExtractor(model=model)
        response = extractor._call_llm("Test: responde solo 'OK'", temperature=0.1)
        return response is not None
    except Exception as e:
        print(f"[ERROR] Conexión fallida: {e}")
        return False


def refinar_oferta(
    titulo: str,
    descripcion: str,
    resultado_regex: Dict,
    model: str = "llama3:latest"
) -> Dict:
    """
    Función helper para refinar una oferta

    Args:
        titulo: Título del puesto
        descripcion: Descripción completa
        resultado_regex: Resultado de regex v3.7
        model: Modelo LLM a usar

    Returns:
        Dict con campos refinados
    """
    extractor = LLMExtractor(model=model)
    return extractor.refine_empty_fields(titulo, descripcion, resultado_regex)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LLM EXTRACTOR v4.0 - Test")
    print("=" * 70)

    # 1. Test de conexión
    print("\n1. Probando conexion con Ollama...")
    if test_llm_connection():
        print("   [OK] Conexion exitosa")
    else:
        print("   [ERROR] No se puede conectar a Ollama")
        print("   Asegurate de que Ollama este corriendo: ollama serve")
        exit(1)

    # 2. Test de extracción
    print("\n2. Probando extracción...")

    descripcion_test = """
    Buscamos Desarrollador Python Senior para empresa de tecnología.

    Requisitos:
    - 5 años de experiencia en desarrollo de software
    - Título universitario en Ingeniería en Sistemas (excluyente)
    - Conocimientos sólidos en Python, Django, PostgreSQL
    - Experiencia con Git, Docker, AWS

    Se valorará:
    - Proactividad y trabajo en equipo
    - Capacidad de liderazgo
    - Inglés avanzado
    """

    # Simular resultado de regex vacío
    resultado_regex = {
        'experiencia_min_anios': None,
        'experiencia_max_anios': None,
        'nivel_educativo': None,
        'estado_educativo': None,
        'skills_tecnicas_list': None,
        'soft_skills_list': None,
        'nlp_version': 'v3.7.0'
    }

    extractor = LLMExtractor()
    print("\n   Extrayendo con LLM...")
    resultado = extractor.refine_empty_fields(
        "Desarrollador Python Senior",
        descripcion_test,
        resultado_regex
    )

    print("\n3. RESULTADOS:")
    print("=" * 70)
    print(f"   Experiencia: {resultado['experiencia_min_anios']} años")
    print(f"   Educación: {resultado['nivel_educativo']} ({resultado['estado_educativo']})")
    print(f"   Skills técnicas: {resultado['skills_tecnicas_list']}")
    print(f"   Soft skills: {resultado['soft_skills_list']}")
    print(f"   Version: {resultado['nlp_version']}")
    print("=" * 70)
    print("\n[OK] Test completado")
