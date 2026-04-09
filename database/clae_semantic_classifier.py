#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLAESemanticClassifier v2.1 — Clasificador de sector económico CLAE
=====================================================================

Reconstruido desde .pyc + diagnóstico (E3.1 del SPEC Motor de Conocimiento).

Clasifica ofertas de empleo por código CLAE (6 dígitos) usando cascada jerárquica:
  Paso 0: id_area portal → portal_area_to_clae.json (match directo)
  Paso 1: sector_empresa → sección CLAE (letra A-S) via sector_canonico.json
  Paso 2: Dentro de la sección: BGE-M3 cosine search → código 6 dígitos

Reutiliza el modelo BGE-M3 del SkillsImplicitExtractor (no carga un segundo modelo).

Uso:
    from clae_semantic_classifier import CLAESemanticClassifier
    classifier = CLAESemanticClassifier(verbose=True)
    result = classifier.classify("Tecnología", "desarrollador python")
    # {'clae_code': '620100', 'clae_grupo': '620', 'clae_seccion': 'J',
    #  'clae_nombre': '...', 'clae_score': 0.52, 'clae_metodo': 'semantico_seccion'}
"""

import json
import sys
import numpy as np
from pathlib import Path
from typing import Optional, Dict

# Configuración centralizada (E1.1)
sys.path.insert(0, str(Path(__file__).parent.parent / "config"))
try:
    from embedding_config import EMBEDDING_MODEL, EMBEDDING_REVISION
except ImportError:
    EMBEDDING_MODEL = "BAAI/bge-m3"
    EMBEDDING_REVISION = None


class CLAESemanticClassifier:
    """Clasifica sector/empresa a código CLAE 6 dígitos con embudo jerárquico."""

    VERSION = "2.1.0"
    DEFAULT_THRESHOLD = 0.52
    DEFAULT_TOP_K = 3

    # Cache a nivel de clase (compartido entre instancias)
    _model = None
    _clae_embeddings = None
    _clae_metadata = None
    _section_indices = None
    _initialized = False

    def __init__(
        self,
        threshold: float = None,
        top_k: int = None,
        verbose: bool = False
    ):
        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self.top_k = top_k or self.DEFAULT_TOP_K
        self.verbose = verbose

        base_path = Path(__file__).parent
        self.embeddings_path = base_path / "embeddings" / "clae_actividades_embeddings.npy"
        self.metadata_path = base_path / "embeddings" / "clae_actividades_metadata.json"
        self.canonico_path = base_path.parent / "config" / "sector_canonico.json"
        self.portal_map_path = base_path.parent / "config" / "portal_area_to_clae.json"

        self._sector_to_seccion = {}
        self._sector_to_default_code = {}
        self._portal_area_map = {}

        self._initialize()

    def _initialize(self):
        """Carga embeddings, metadata, índice por sección y mapeos."""
        # Reutilizar modelo BGE-M3 del SkillsImplicitExtractor si ya está cargado
        if CLAESemanticClassifier._model is None:
            try:
                from skills_implicit_extractor import SkillsImplicitExtractor
                if SkillsImplicitExtractor._model is not None:
                    CLAESemanticClassifier._model = SkillsImplicitExtractor._model
                    if self.verbose:
                        print("[CLAE] Reutilizando modelo BGE-M3 de SkillsImplicitExtractor")
            except ImportError:
                pass

        if CLAESemanticClassifier._model is None:
            if self.verbose:
                print("[CLAE] Cargando modelo BGE-M3...")
            from sentence_transformers import SentenceTransformer
            if EMBEDDING_REVISION:
                CLAESemanticClassifier._model = SentenceTransformer(
                    EMBEDDING_MODEL, revision=EMBEDDING_REVISION
                )
            else:
                CLAESemanticClassifier._model = SentenceTransformer(EMBEDDING_MODEL)

        self.model = CLAESemanticClassifier._model

        # Cargar embeddings y metadata (cache de clase)
        if CLAESemanticClassifier._clae_embeddings is None:
            if self.embeddings_path.exists() and self.metadata_path.exists():
                if self.verbose:
                    print(f"[CLAE] Cargando embeddings desde {self.embeddings_path}")
                CLAESemanticClassifier._clae_embeddings = np.load(str(self.embeddings_path))
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    CLAESemanticClassifier._clae_metadata = json.load(f)

                # Construir índice por sección
                CLAESemanticClassifier._section_indices = {}
                for i, meta in enumerate(CLAESemanticClassifier._clae_metadata):
                    sec = meta.get('seccion', '')
                    if sec not in CLAESemanticClassifier._section_indices:
                        CLAESemanticClassifier._section_indices[sec] = []
                    CLAESemanticClassifier._section_indices[sec].append(i)

                if self.verbose:
                    total = CLAESemanticClassifier._clae_embeddings.shape[0]
                    secs = len(CLAESemanticClassifier._section_indices)
                    print(f"[CLAE] {total} actividades en {secs} secciones cargadas")
            else:
                if self.verbose:
                    print(f"[CLAE] WARNING: Embeddings no encontrados en {self.embeddings_path}")
                CLAESemanticClassifier._clae_embeddings = np.array([])
                CLAESemanticClassifier._clae_metadata = []
                CLAESemanticClassifier._section_indices = {}

        self.embeddings = CLAESemanticClassifier._clae_embeddings
        self.metadata = CLAESemanticClassifier._clae_metadata
        self.section_indices = CLAESemanticClassifier._section_indices

        # Cargar mapeos
        self._load_sector_map()
        self._load_portal_map()

    def _load_sector_map(self):
        """Carga mapa sector canónico -> sección CLAE desde sector_canonico.json."""
        if not self.canonico_path.exists():
            return
        with open(self.canonico_path, 'r', encoding='utf-8') as f:
            canonico = json.load(f)
        for nombre, info in canonico.get('sectores', {}).items():
            sec = info.get('clae_seccion', '')
            default = info.get('clae_code_default', '')
            if sec:
                self._sector_to_seccion[nombre.lower()] = sec
                self._sector_to_default_code[sec] = default

    def _load_portal_map(self):
        """Carga mapeo id_area portal -> CLAE desde portal_area_to_clae.json."""
        if not self.portal_map_path.exists():
            return
        with open(self.portal_map_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Navent = Bumeran + ZonaJobs (mismos IDs)
        self._portal_area_map = data.get('navent', {})

    def classify(
        self,
        sector_empresa: str,
        titulo: str,
        descripcion: str = "",
        id_area_portal: str = None
    ) -> Optional[Dict]:
        """
        Clasificación jerárquica por embudo.

        Cascada:
          0. id_area_portal -> portal_area_to_clae.json (match directo)
          1. sector_empresa canónico -> sección CLAE (siempre)
          2. Semántico DENTRO de la sección -> 6 dígitos (si score > threshold)
          3. Si no supera threshold -> código default de la sección

        Returns:
            dict con clae_code, clae_grupo, clae_seccion, clae_nombre, clae_score,
            clae_metodo ('portal_directo' | 'semantico_seccion' | 'default_seccion' | None)
        """
        if not len(self.embeddings):
            return None

        # === PASO 0: Match por id_area del portal ===
        if id_area_portal and str(id_area_portal) in self._portal_area_map:
            mapping = self._portal_area_map[str(id_area_portal)]
            seccion = mapping['clae_seccion']
            default_code = mapping['clae_code_default']
            # Buscar nombre del default_code en metadata
            nombre = ""
            for m in self.metadata:
                if m.get('code') == default_code:
                    nombre = m.get('nombre', '')
                    break
            return {
                'clae_code': default_code,
                'clae_grupo': default_code[:3],
                'clae_seccion': seccion,
                'clae_nombre': nombre,
                'clae_score': 1.0,
                'clae_metodo': 'portal_directo'
            }

        # === PASO 1: sector_empresa -> sección CLAE ===
        sector = (sector_empresa or "").strip()
        seccion = self._sector_to_seccion.get(sector.lower())
        default_code = self._sector_to_default_code.get(seccion, "") if seccion else ""

        if not seccion or sector.lower() == "otro":
            # Fallback: intentar inferir sección desde título (búsqueda global)
            if titulo and titulo.strip():
                fallback_result = self._semantic_search_global(titulo.strip())
                if fallback_result:
                    return fallback_result

            if self.verbose:
                print(f"[CLAE] Sector '{sector}' no tiene sección mapeada")
            return None

        # === PASO 2: dentro de la sección -> código 6 dígitos ===
        indices_seccion = self.section_indices.get(seccion, [])
        if not indices_seccion:
            if self.verbose:
                print(f"[CLAE] Sección '{seccion}' sin actividades en embeddings")
            return self._build_default_result(seccion, default_code)

        # Construir query: sector + titulo (truncado)
        desc_snippet = (descripcion or "")[:500]
        parts = [p for p in [sector, titulo, desc_snippet] if p and p.strip()]
        query = " ".join(parts)

        # Encode y buscar dentro de la sección
        query_emb = self.model.encode(query, normalize_embeddings=True)
        indices_arr = np.array(indices_seccion)
        section_embeddings = self.embeddings[indices_arr]
        similarities = np.dot(section_embeddings, query_emb)

        # Top-K dentro de la sección
        k = min(self.top_k, len(indices_seccion))
        top_local = np.argsort(similarities)[-k:][::-1]

        if self.verbose:
            print(f"[CLAE] Sección {seccion} ({len(indices_seccion)} actividades) | Query: '{query[:60]}...'")
            for i, li in enumerate(top_local[:3]):
                gi = indices_seccion[li]
                meta = self.metadata[gi]
                score = float(similarities[li])
                print(f"  Top {i+1}: {meta['code']} {meta['nombre'][:50]} (score={score:.3f})")

        # Mejor candidato
        best_local_idx = top_local[0]
        best_score = float(similarities[best_local_idx])
        best_global_idx = indices_seccion[best_local_idx]
        meta = self.metadata[best_global_idx]

        if best_score >= self.threshold:
            if self.verbose:
                print(f"[CLAE] → {meta['code']} {meta['nombre'][:50]}) [semantico_seccion]")
            return {
                'clae_code': meta['code'],
                'clae_grupo': meta.get('grupo', meta['code'][:3]),
                'clae_seccion': meta.get('seccion', seccion),
                'clae_nombre': meta.get('nombre', ''),
                'clae_score': round(best_score, 4),
                'clae_metodo': 'semantico_seccion'
            }
        else:
            if self.verbose:
                print(f"[CLAE] Score {best_score:.3f} → default sección {seccion}")
            return self._build_default_result(seccion, default_code)

    def _semantic_search_global(self, titulo: str) -> Optional[Dict]:
        """
        Fallback: buscar en TODO el corpus CLAE sin filtrar por sección.
        Se usa cuando sector_empresa = "Otro" o no tiene mapeo.
        """
        query_emb = self.model.encode(titulo, normalize_embeddings=True)
        similarities = np.dot(self.embeddings, query_emb)

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= self.threshold:
            meta = self.metadata[best_idx]
            if self.verbose:
                print(f"[CLAE] Fallback global: '{titulo[:40]}' → {meta['code']} (score={best_score:.3f})")
            return {
                'clae_code': meta['code'],
                'clae_grupo': meta.get('grupo', meta['code'][:3]),
                'clae_seccion': meta.get('seccion', ''),
                'clae_nombre': meta.get('nombre', ''),
                'clae_score': round(best_score, 4),
                'clae_metodo': 'semantico_global'
            }

        if self.verbose:
            print(f"[CLAE] Fallback global: '{titulo[:40]}' → score {best_score:.3f} < threshold")
        return None

    def _build_default_result(self, seccion: str, default_code: str) -> Dict:
        """Construye resultado con el código default de la sección."""
        nombre = ""
        grupo = default_code[:3] if default_code else ""
        for m in self.metadata:
            if m.get('code') == default_code:
                nombre = m.get('nombre', '')
                grupo = m.get('grupo', default_code[:3])
                break
        return {
            'clae_code': default_code,
            'clae_grupo': grupo,
            'clae_seccion': seccion,
            'clae_nombre': nombre,
            'clae_score': 0.0,
            'clae_metodo': 'default_seccion'
        }
