# -*- coding: utf-8 -*-
"""
03_match_semantico.py - PASO 3: Match Semántico por Título
============================================================

Busca ocupaciones ESCO similares al título usando embeddings BGE-M3.
Complementa el match por skills (paso 2) con similitud semántica.

Input: JSON del paso 1 (01_skills_extraidas_*.json) - usa titulo_limpio
Output: JSON con ocupaciones candidatas por similitud semántica.

Uso:
    python 03_match_semantico.py --input exports/matching_optimization/01_skills_extraidas_*.json
    python 03_match_semantico.py --input ... --top_n 5     # Top 5 candidatos
    python 03_match_semantico.py --input ... --verbose     # Modo debug
"""

import sys
import json
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer

# Agregar database/ al path
BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "database"))


class SemanticMatcher:
    """Match semántico de títulos con ocupaciones ESCO."""

    MODEL_NAME = "BAAI/bge-m3"
    _model = None  # Cache a nivel de clase

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._load_model()
        self._load_occupation_embeddings()

    def _load_model(self):
        """Carga modelo BGE-M3 (con cache)."""
        if SemanticMatcher._model is None:
            if self.verbose:
                print(f"Cargando modelo {self.MODEL_NAME}...")
            SemanticMatcher._model = SentenceTransformer(self.MODEL_NAME)
        self.model = SemanticMatcher._model

    def _load_occupation_embeddings(self):
        """Carga embeddings pre-calculados de ocupaciones ESCO."""
        emb_path = BASE_DIR / "database" / "embeddings" / "esco_occupations_embeddings.npy"
        meta_path = BASE_DIR / "database" / "embeddings" / "esco_occupations_metadata.json"

        if emb_path.exists() and meta_path.exists():
            self.occ_embeddings = np.load(str(emb_path))
            with open(meta_path, 'r', encoding='utf-8') as f:
                self.occ_metadata = json.load(f)
            if self.verbose:
                print(f"Cargados {len(self.occ_metadata)} embeddings de ocupaciones")
        else:
            raise FileNotFoundError(f"No se encontraron embeddings en {emb_path}")

    def match(self, titulo: str, top_n: int = 10) -> list:
        """Busca ocupaciones similares al título."""
        if not titulo:
            return []

        # Generar embedding del título
        titulo_emb = self.model.encode(titulo, normalize_embeddings=True)

        # Calcular similitud coseno
        similarities = np.dot(self.occ_embeddings, titulo_emb)

        # Top N
        top_indices = np.argsort(similarities)[::-1][:top_n]

        candidatos = []
        for idx in top_indices:
            meta = self.occ_metadata[idx]
            candidatos.append({
                'occupation_uri': meta.get('uri', ''),
                'esco_label': meta.get('preferredLabel', ''),
                'isco_code': meta.get('isco_code', ''),
                'score': float(similarities[idx]),
                'metodo': 'semantic_bge_m3'
            })

        return candidatos


def cargar_datos(input_path: str) -> list:
    """Carga datos del paso 1."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_semantico(datos: list, top_n: int = 10, verbose: bool = False) -> list:
    """Busca ocupaciones por similitud semántica del título."""
    matcher = SemanticMatcher(verbose=verbose)

    resultados = []
    total = len(datos)

    for i, oferta in enumerate(datos):
        id_oferta = oferta['id_oferta']
        titulo = oferta.get('titulo_limpio', '')

        if verbose:
            print(f"\n[{i+1}/{total}] {id_oferta}: {titulo[:50]}...")

        try:
            candidatos = matcher.match(titulo, top_n=top_n)

            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'area_funcional': oferta.get('area_funcional'),
                'nivel_seniority': oferta.get('nivel_seniority'),
                'candidatos_count': len(candidatos),
                'candidatos': candidatos,
                'mejor_candidato': candidatos[0] if candidatos else None
            }

            if verbose and candidatos:
                print(f"   -> {len(candidatos)} ocupaciones candidatas")
                for c in candidatos[:3]:
                    print(f"      - {c.get('esco_label', '?')} (ISCO {c.get('isco_code', '?')}) score={c.get('score', 0):.3f}")

        except Exception as e:
            resultado = {
                'id_oferta': id_oferta,
                'titulo_limpio': titulo,
                'error': str(e),
                'candidatos_count': 0,
                'candidatos': []
            }
            if verbose:
                print(f"   -> ERROR: {e}")

        resultados.append(resultado)

        # Progreso cada 10
        if not verbose and (i + 1) % 10 == 0:
            print(f"Procesadas {i+1}/{total} ofertas...")

    return resultados


def guardar_resultados(resultados: list, output_path: Path):
    """Guarda resultados en JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en: {output_path}")


def imprimir_resumen(resultados: list):
    """Imprime resumen del matching semántico."""
    total = len(resultados)
    con_candidatos = sum(1 for r in resultados if r.get('candidatos_count', 0) > 0)
    errores = sum(1 for r in resultados if 'error' in r)

    print("\n" + "=" * 60)
    print("RESUMEN MATCH SEMÁNTICO")
    print("=" * 60)
    print(f"Total ofertas procesadas: {total}")
    print(f"Ofertas con candidatos: {con_candidatos} ({100*con_candidatos/total:.1f}%)")
    print(f"Errores: {errores}")

    # Score promedio del mejor candidato
    scores = [r['mejor_candidato']['score'] for r in resultados if r.get('mejor_candidato')]
    if scores:
        print(f"Score promedio (mejor candidato): {np.mean(scores):.3f}")
        print(f"Score mínimo: {np.min(scores):.3f}")
        print(f"Score máximo: {np.max(scores):.3f}")
    print("=" * 60)

    # Distribución de códigos ISCO
    print("\nDistribución por código ISCO (primer dígito):")
    isco_dist = {}
    for r in resultados:
        mejor = r.get('mejor_candidato')
        if mejor:
            isco = mejor.get('isco_code', '?')
            if isco and len(isco) >= 1:
                grupo = isco[0]
                isco_dist[grupo] = isco_dist.get(grupo, 0) + 1

    for grupo in sorted(isco_dist.keys()):
        count = isco_dist[grupo]
        print(f"  ISCO {grupo}xxx: {count} ofertas")

    # Ejemplos de matches de bajo score
    bajo_score = [r for r in resultados if r.get('mejor_candidato') and r['mejor_candidato']['score'] < 0.5]
    if bajo_score:
        print(f"\nOfertas con score bajo (<0.5): {len(bajo_score)}")
        for r in bajo_score[:5]:
            mejor = r['mejor_candidato']
            print(f"  {r['id_oferta']}: {r.get('titulo_limpio', '')[:40]}...")
            print(f"     -> {mejor.get('esco_label', '?')} (score={mejor.get('score', 0):.3f})")


def main():
    parser = argparse.ArgumentParser(description='Match semántico por título')
    parser.add_argument('--input', '-i', type=str, required=True, help='JSON del paso 1')
    parser.add_argument('--top_n', type=int, default=10, help='Top N candidatos (default: 10)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo debug')
    parser.add_argument('--output', '-o', type=str, default=None, help='Archivo de salida')
    args = parser.parse_args()

    print("=" * 60)
    print("PASO 3: MATCH SEMÁNTICO (Gold Set 100)")
    print("=" * 60)
    print(f"Input: {args.input}")
    print(f"Top N candidatos: {args.top_n}")

    # Cargar datos
    print("\nCargando datos...")
    datos = cargar_datos(args.input)
    print(f"Ofertas cargadas: {len(datos)}")

    # Match semántico
    print("\nBuscando ocupaciones por similitud semántica...")
    resultados = match_semantico(
        datos,
        top_n=args.top_n,
        verbose=args.verbose
    )

    # Guardar
    output_dir = BASE_DIR / "exports" / "matching_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"03_match_semantico_{timestamp}.json"

    guardar_resultados(resultados, output_path)

    # Resumen
    imprimir_resumen(resultados)

    print(f"\n[OK] Siguiente paso: python 04_combinar_scores.py --skills <paso2.json> --semantico {output_path}")


if __name__ == "__main__":
    main()
