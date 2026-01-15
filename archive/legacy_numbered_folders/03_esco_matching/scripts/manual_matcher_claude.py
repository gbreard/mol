# -*- coding: utf-8 -*-
"""
Matching Manual Inteligente por Claude
========================================

Claude hace matching manual de ofertas con ESCO usando razonamiento contextual.
Documenta patrones para futuros matchings automatizados.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import unicodedata
import re

# Rutas
OFERTAS_PATH = r"D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\ofertas_esco_isco_llm_20251027_191809.csv"
ESCO_PATH = r"D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json"
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\03_esco_matching\data")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class TextNormalizer:
    """Normalizador de texto"""

    @staticmethod
    def normalize(text):
        if pd.isna(text) or not text:
            return ""
        text = text.lower().strip()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class ManualMatcher:
    """Matcher manual inteligente"""

    def __init__(self):
        self.ofertas = []
        self.esco_data = {}
        self.esco_list = []
        self.resultados = []
        self.patrones = []

        self._load_data()

    def _load_data(self):
        """Carga datos"""
        print("=" * 100)
        print("MATCHING MANUAL INTELIGENTE - CLAUDE")
        print("=" * 100)

        # Cargar ofertas
        print(f"\n[1/2] Cargando ofertas...")
        df = pd.read_csv(OFERTAS_PATH, encoding='utf-8', low_memory=False)
        self.ofertas = df.to_dict('records')
        print(f"  OK: {len(self.ofertas)} ofertas cargadas")

        # Cargar ESCO
        print(f"\n[2/2] Cargando ESCO...")
        with open(ESCO_PATH, 'r', encoding='utf-8') as f:
            self.esco_data = json.load(f)

        # Convertir a lista para búsqueda
        self.esco_list = [
            {
                'esco_id': k,
                'label_es': v.get('label_es', ''),
                'label_en': v.get('label_en', ''),
                'isco_code': v.get('codigo_isco_4d', v.get('codigo_isco', '')),
                'alt_labels': v.get('alt_labels_es', []),
                'uri': v.get('uri', '')
            }
            for k, v in self.esco_data.items()
        ]

        print(f"  OK: {len(self.esco_list)} ocupaciones ESCO")

    def search_esco(self, keywords, isco_prefix=None):
        """
        Busca en ESCO por keywords

        Args:
            keywords: lista de palabras clave
            isco_prefix: filtrar por prefijo ISCO (ej: "5" para servicios)

        Returns:
            lista de matches ordenados por relevancia
        """
        keywords_norm = [TextNormalizer.normalize(k) for k in keywords if k]
        matches = []

        for ocu in self.esco_list:
            label_norm = TextNormalizer.normalize(ocu['label_es'])
            alt_labels_norm = ' '.join([TextNormalizer.normalize(a) for a in ocu.get('alt_labels', [])])
            texto_completo = f"{label_norm} {alt_labels_norm}"

            # Filtrar por ISCO si se especifica
            if isco_prefix and not str(ocu['isco_code']).startswith(str(isco_prefix)):
                continue

            # Calcular score simple
            score = 0
            for kw in keywords_norm:
                if kw in texto_completo:
                    score += 1

            if score > 0:
                matches.append({
                    'esco_id': ocu['esco_id'],
                    'label': ocu['label_es'],
                    'isco_code': ocu['isco_code'],
                    'alt_labels': ocu['alt_labels'][:3],
                    'score': score
                })

        # Ordenar por score
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:20]

    def get_isco_level(self, titulo_norm):
        """
        Determina nivel ISCO (1 dígito) basado en título

        Returns:
            str con nivel ISCO sugerido
        """
        # Directores/Gerentes (1)
        if any(w in titulo_norm for w in ['director', 'gerente', 'jefe', 'responsable', 'coordinador']):
            return '1'

        # Profesionales (2)
        if any(w in titulo_norm for w in ['analista', 'ingeniero', 'especialista', 'asesor', 'consultor', 'arquitecto']):
            return '2'

        # Técnicos (3)
        if any(w in titulo_norm for w in ['tecnico', 'asistente', 'auxiliar administrativo']):
            return '3'

        # Administrativos (4)
        if any(w in titulo_norm for w in ['administrativo', 'secretaria', 'recepcionista']):
            return '4'

        # Servicios/Ventas (5)
        if any(w in titulo_norm for w in ['vendedor', 'promotor', 'cajero', 'mozo', 'camarero', 'cocinero']):
            return '5'

        # Agropecuarios (6) - poco común
        if any(w in titulo_norm for w in ['agricola', 'ganadero', 'forestal', 'pesca']):
            return '6'

        # Oficios (7)
        if any(w in titulo_norm for w in ['soldador', 'mecanico', 'electricista', 'carpintero', 'plomero', 'oficial']):
            return '7'

        # Operadores (8)
        if any(w in titulo_norm for w in ['operador', 'operario', 'conductor', 'chofer', 'maquinista']):
            return '8'

        # Elementales (9)
        if any(w in titulo_norm for w in ['limpieza', 'peones', 'ayudante', 'repositor']):
            return '9'

        return None

    def save_progress(self):
        """Guarda progreso actual"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Guardar resultados
        output_path = OUTPUT_DIR / f"manual_matching_claude_{timestamp}.json"

        data = {
            'timestamp': timestamp,
            'total_ofertas': len(self.ofertas),
            'procesadas': len(self.resultados),
            'resultados': self.resultados,
            'patrones': self.patrones
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n[GUARDADO] {output_path}")
        print(f"Progreso: {len(self.resultados)}/{len(self.ofertas)}")

        return output_path

    def export_to_csv(self):
        """Exporta resultados a CSV para comparación"""
        if not self.resultados:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Crear DataFrame con resultados
        df_results = pd.DataFrame([
            {
                'titulo': r['titulo'],
                'descripcion': r.get('descripcion', ''),
                'claude_esco_id': r['claude_match']['esco_id'],
                'claude_esco_label': r['claude_match']['label'],
                'claude_isco_code': r['claude_match']['isco_code'],
                'claude_confidence': r['claude_match']['confidence'],
                'claude_reasoning': r['claude_match']['reasoning'],
                'claude_pattern': r['claude_match'].get('pattern', ''),
                'fuzzy_esco_label': r['fuzzy_original']['label'],
                'fuzzy_isco_code': r['fuzzy_original']['isco_code'],
                'fuzzy_score': r['fuzzy_original']['score'],
                'fuzzy_confidence': r['fuzzy_original']['confidence'],
                'match_coincide': r['claude_match']['isco_code'] == r['fuzzy_original']['isco_code']
            }
            for r in self.resultados
        ])

        output_path = OUTPUT_DIR / f"manual_matching_comparison_{timestamp}.csv"
        df_results.to_csv(output_path, index=False, encoding='utf-8')

        print(f"[EXPORTADO CSV] {output_path}")
        return output_path


def main():
    """Función principal"""
    matcher = ManualMatcher()

    print("\n" + "=" * 100)
    print("SISTEMA DE MATCHING MANUAL LISTO")
    print("=" * 100)
    print("\nEste script proporciona herramientas para matching manual.")
    print("Claude procesara las ofertas usando razonamiento contextual.\n")

    # Ejemplo de uso
    print("Ejemplo de busqueda en ESCO:")
    print("-" * 100)

    # Buscar "promotor de ventas"
    results = matcher.search_esco(['promotor', 'ventas'], isco_prefix='5')
    print(f"\nBusqueda: 'promotor ventas' (ISCO 5xxx)")
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r['label']} (ISCO: {r['isco_code']}) [score: {r['score']}]")
        if r['alt_labels']:
            print(f"   Alt: {', '.join(r['alt_labels'][:2])}")

    print("\n" + "=" * 100)
    print("FRAMEWORK LISTO - Esperando procesamiento por Claude")
    print("=" * 100)


if __name__ == "__main__":
    main()
