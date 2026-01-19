#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skills Implicit Extractor v2.0 - Extrae skills ESCO desde título y tareas
============================================================================

VERSION: 2.0.0
FECHA: 2026-01-04
MODELO: BGE-M3 (BAAI/bge-m3)

OBJETIVO:
Extraer skills ESCO implícitas a partir del TÍTULO y las tareas de una oferta.
Basado en la metodología del Excel Gold Set pestaña 17_Skills_Completas_ESCO.

CAMBIO v2.0:
- Ahora usa título_limpio + tareas_explicitas (antes solo tareas)
- Nuevo método extract_skills() para el pipeline v3

FLUJO:
1. Recibe titulo_limpio + tareas_explicitas
2. Para cada texto, genera embedding con BGE-M3
3. Busca skills ESCO más similares (cosine similarity)
4. Retorna skills con score > umbral, indicando origen (titulo/tarea)

Uso:
    from skills_implicit_extractor import SkillsImplicitExtractor

    extractor = SkillsImplicitExtractor()

    # v2.0 - Nuevo método con título + tareas
    skills = extractor.extract_skills(
        titulo_limpio="Responsable de Depósito",
        tareas_explicitas="Control de inventarios; Gestión de equipo"
    )
    # [
    #     {"skill_esco": "gestionar inventario", "score": 0.83, "origen": "tarea"},
    #     {"skill_esco": "liderar equipos", "score": 0.75, "origen": "titulo"},
    #     ...
    # ]
"""

import json
import numpy as np
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer

# Categorización jerárquica L1/L2 para dashboards
# v2.0: Usa datos ESCO directos del RDF (sin hardcoding)
from skill_categorizer import get_categorizer


class SkillsImplicitExtractor:
    """
    Extrae skills ESCO implícitas desde tareas usando embeddings BGE-M3.

    Usa cache a nivel de clase para evitar recargar modelo y embeddings.
    """

    VERSION = "2.2.0"  # v2.2: Ponderación skills genéricas vs específicas

    # Configuración por defecto
    DEFAULT_MODEL = "BAAI/bge-m3"
    DEFAULT_THRESHOLD = 0.60  # Umbral de similitud mínima (v2.2: subido de 0.55)
    DEFAULT_TOP_K = 3  # Top K skills por tarea

    # Cache a nivel de clase
    _model = None
    _skills_embeddings = None
    _skills_metadata = None
    _skills_weights_config = None  # v2.2: Config de pesos
    _initialized = False

    def __init__(
        self,
        embeddings_path: str = None,
        metadata_path: str = None,
        db_path: str = None,
        threshold: float = None,
        top_k: int = None,
        verbose: bool = False
    ):
        """
        Inicializa el extractor.

        Args:
            embeddings_path: Path a embeddings .npy (default: database/embeddings/esco_skills_embeddings.npy)
            metadata_path: Path a metadata .json (default: database/embeddings/esco_skills_metadata.json)
            db_path: Path a BD (para regenerar embeddings si no existen)
            threshold: Umbral de similitud mínima (default: 0.55)
            top_k: Número máximo de skills por tarea (default: 3)
            verbose: Mostrar mensajes de debug
        """
        base_path = Path(__file__).parent

        self.embeddings_path = Path(embeddings_path) if embeddings_path else base_path / "embeddings" / "esco_skills_embeddings_full.npy"
        self.metadata_path = Path(metadata_path) if metadata_path else base_path / "embeddings" / "esco_skills_metadata_full.json"
        self.db_path = Path(db_path) if db_path else base_path / "bumeran_scraping.db"

        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self.top_k = top_k or self.DEFAULT_TOP_K
        self.verbose = verbose

        # Inicializar (usa cache de clase)
        self._initialize()

    def _initialize(self):
        """Carga modelo y embeddings (usa cache si ya están cargados)."""
        # Cargar modelo (una sola vez)
        if SkillsImplicitExtractor._model is None:
            if self.verbose:
                print(f"[SKILLS] Cargando modelo {self.DEFAULT_MODEL}...")
            SkillsImplicitExtractor._model = SentenceTransformer(self.DEFAULT_MODEL)

        self.model = SkillsImplicitExtractor._model

        # Cargar embeddings y metadata
        if SkillsImplicitExtractor._skills_embeddings is None:
            if self.embeddings_path.exists() and self.metadata_path.exists():
                if self.verbose:
                    print(f"[SKILLS] Cargando embeddings desde {self.embeddings_path}...")
                SkillsImplicitExtractor._skills_embeddings = np.load(str(self.embeddings_path))
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    SkillsImplicitExtractor._skills_metadata = json.load(f)
            else:
                if self.verbose:
                    print(f"[SKILLS] Embeddings no encontrados, se requiere generación previa")
                SkillsImplicitExtractor._skills_embeddings = np.array([])
                SkillsImplicitExtractor._skills_metadata = []

        self.embeddings = SkillsImplicitExtractor._skills_embeddings
        self.metadata = SkillsImplicitExtractor._skills_metadata

        # v2.2: Cargar config de pesos para skills genéricas
        if SkillsImplicitExtractor._skills_weights_config is None:
            weights_path = Path(__file__).parent.parent / "config" / "skills_weights.json"
            if weights_path.exists():
                with open(weights_path, 'r', encoding='utf-8') as f:
                    SkillsImplicitExtractor._skills_weights_config = json.load(f)
                if self.verbose:
                    print(f"[SKILLS] Config pesos cargado: {len(SkillsImplicitExtractor._skills_weights_config.get('skills_genericas', {}).get('lista', []))} skills genéricas")
            else:
                SkillsImplicitExtractor._skills_weights_config = {}

        self.weights_config = SkillsImplicitExtractor._skills_weights_config

        SkillsImplicitExtractor._initialized = True

        if self.verbose:
            print(f"[SKILLS] Inicializado: {len(self.metadata)} skills, umbral={self.threshold}")

    def extract_from_tasks(
        self,
        tareas_explicitas: str,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        Extrae skills ESCO implícitas desde las tareas de una oferta.

        Args:
            tareas_explicitas: String con tareas separadas por punto y coma
            top_k: Override del número máximo de skills por tarea
            threshold: Override del umbral de similitud

        Returns:
            Lista de dicts con: tarea, skill_esco, skill_uri, score, origen
        """
        if not tareas_explicitas or not self.embeddings.size:
            return []

        top_k = top_k or self.top_k
        threshold = threshold or self.threshold

        # Separar tareas
        tareas = [t.strip() for t in tareas_explicitas.split(';') if t.strip()]

        if not tareas:
            return []

        skills_implicitas = []
        skills_vistas = set()  # Para evitar duplicados

        for tarea in tareas:
            # Generar embedding de la tarea
            tarea_emb = self.model.encode(tarea, normalize_embeddings=True)

            # Calcular similitud coseno con todas las skills
            similarities = np.dot(self.embeddings, tarea_emb)

            # Obtener top K indices ordenados por similitud
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            for idx in top_indices:
                score = float(similarities[idx])

                if score < threshold:
                    continue

                skill_meta = self.metadata[idx]
                skill_label = skill_meta.get('label', skill_meta.get('preferred_label_es', ''))

                # Evitar duplicados
                if skill_label.lower() in skills_vistas:
                    continue

                skills_vistas.add(skill_label.lower())

                skills_implicitas.append({
                    "tarea": tarea[:100],  # Truncar para BD
                    "skill_esco": skill_label,
                    "skill_uri": skill_meta.get('uri', skill_meta.get('skill_uri', '')),
                    "score": round(score, 4),
                    "origen": "IMPLICITA"
                })

                if self.verbose:
                    print(f"[SKILLS] '{tarea[:50]}...' -> '{skill_label}' (score={score:.3f})")

        return skills_implicitas

    def _get_skill_weight(
        self,
        skill_label: str,
        sector_empresa: str = None,
        nivel_seniority: str = None,
        area_funcional: str = None
    ) -> float:
        """
        v2.2: Calcula el peso de una skill según si es genérica o específica.

        Skills genéricas (trabajo en equipo, comunicación, etc.) tienen peso reducido.
        Skills contextuales dependen del sector/seniority/área.

        Returns:
            Peso entre 0.0 y 1.0
        """
        if not self.weights_config:
            return 1.0

        skill_lower = skill_label.lower().strip()

        # 1. Verificar si es skill genérica
        skills_genericas = self.weights_config.get("skills_genericas", {})
        lista_genericas = [s.lower() for s in skills_genericas.get("lista", [])]
        peso_generico = skills_genericas.get("peso", 0.5)

        if skill_lower in lista_genericas:
            return peso_generico

        # 2. Verificar reglas contextuales
        for regla in self.weights_config.get("skills_contextuales", {}).get("reglas", []):
            skill_regla = regla.get("skill", "").lower()
            if skill_lower == skill_regla or skill_regla in skill_lower:
                # Verificar condición sector
                if "si_sector_es" in regla and sector_empresa:
                    if sector_empresa in regla["si_sector_es"]:
                        return regla.get("entonces_peso", 1.0)
                    else:
                        return regla.get("sino_peso", 0.5)

                # Verificar condición seniority
                if "si_seniority_es" in regla and nivel_seniority:
                    if nivel_seniority.lower() in [s.lower() for s in regla["si_seniority_es"]]:
                        return regla.get("entonces_peso", 1.0)
                    else:
                        return regla.get("sino_peso", 0.5)

                # Verificar condición área
                if "si_area_es" in regla and area_funcional:
                    if area_funcional in regla["si_area_es"]:
                        return regla.get("entonces_peso", 1.0)
                    else:
                        return regla.get("sino_peso", 0.5)

        # Por defecto, peso 1.0 (skill específica)
        return 1.0

    def extract_skills(
        self,
        titulo_limpio: str,
        tareas_explicitas: str = None,
        skills_nlp: List[str] = None,
        soft_skills_nlp: List[str] = None,
        sector_empresa: str = None,
        nivel_seniority: str = None,
        area_funcional: str = None,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        v2.2: Extrae skills ESCO con ponderación de skills genéricas.

        El título aporta contexto general del rol.
        Las tareas aportan detalle específico.
        Las skills_nlp y soft_skills_nlp (si existen) enriquecen con lo que el LLM detectó.

        v2.1 (2026-01-14): Agregado skills_nlp para usar skills_tecnicas_list del NLP.
        v2.2 (2026-01-14): Agregado ponderación de skills genéricas vs específicas.
                          Skills como "trabajo en equipo" tienen peso 0.5x.
                          Agregado soft_skills_nlp para usar soft_skills_list del NLP.

        Args:
            titulo_limpio: Título limpio de la oferta (requerido)
            tareas_explicitas: String con tareas separadas por ; (opcional)
            skills_nlp: Lista de skills técnicas extraídas por NLP (skills_tecnicas_list)
            soft_skills_nlp: Lista de soft skills extraídas por NLP (soft_skills_list)
            sector_empresa: Sector de la empresa (para ponderación contextual)
            nivel_seniority: Nivel de seniority (para ponderación contextual)
            area_funcional: Área funcional (para ponderación contextual)
            top_k: Override del número máximo de skills por texto
            threshold: Override del umbral de similitud

        Returns:
            Lista de dicts con: skill_esco, skill_uri, score, score_ponderado, peso, origen
        """
        if not self.embeddings.size:
            return []

        top_k = top_k or self.top_k
        threshold = threshold or self.threshold

        # Preparar textos a procesar
        textos = []

        # 1. Título siempre presente (si existe)
        if titulo_limpio and titulo_limpio.strip():
            textos.append(("titulo", titulo_limpio.strip()))

        # 2. Tareas si existen
        if tareas_explicitas:
            for tarea in tareas_explicitas.split(';'):
                tarea = tarea.strip()
                if tarea:
                    textos.append(("tarea", tarea))

        # 3. Skills NLP (v2.1): usar skills extraídas por LLM como contexto adicional
        # Esto es CRÍTICO cuando tareas_explicitas es NULL pero el LLM detectó skills
        if skills_nlp:
            for skill in skills_nlp:
                skill = skill.strip() if isinstance(skill, str) else str(skill)
                if skill and skill.lower() not in ['null', 'none', '']:
                    textos.append(("skills_nlp", skill))

        # 4. Soft Skills NLP (v2.2): usar soft skills extraídas por LLM
        # Las soft skills ayudan a identificar mejor roles de gestión/liderazgo
        if soft_skills_nlp:
            for skill in soft_skills_nlp:
                skill = skill.strip() if isinstance(skill, str) else str(skill)
                if skill and skill.lower() not in ['null', 'none', '']:
                    textos.append(("soft_skills_nlp", skill))

        if not textos:
            return []

        skills_extraidas = []
        skills_vistas = set()  # Para evitar duplicados

        for origen, texto in textos:
            # Generar embedding del texto
            texto_emb = self.model.encode(texto, normalize_embeddings=True)

            # Calcular similitud coseno con todas las skills
            similarities = np.dot(self.embeddings, texto_emb)

            # Obtener top K indices ordenados por similitud
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            for idx in top_indices:
                score = float(similarities[idx])

                if score < threshold:
                    continue

                skill_meta = self.metadata[idx]
                skill_label = skill_meta.get('label', skill_meta.get('preferred_label_es', ''))
                skill_uri = skill_meta.get('uri', skill_meta.get('skill_uri', ''))

                # Evitar duplicados (mantener el de mayor score)
                skill_key = skill_label.lower()
                if skill_key in skills_vistas:
                    continue

                skills_vistas.add(skill_key)

                # v2.2: Calcular peso según si es skill genérica o específica
                peso = self._get_skill_weight(
                    skill_label,
                    sector_empresa=sector_empresa,
                    nivel_seniority=nivel_seniority,
                    area_funcional=area_funcional
                )
                score_ponderado = score * peso

                skills_extraidas.append({
                    "skill_esco": skill_label,
                    "skill_uri": skill_uri,
                    "score": round(score, 4),
                    "score_ponderado": round(score_ponderado, 4),  # v2.2
                    "peso": peso,  # v2.2
                    "origen": origen,  # "titulo" o "tarea"
                    "texto_fuente": texto[:100]  # Truncar para debugging
                })

                if self.verbose:
                    peso_tag = " [GEN]" if peso < 1.0 else ""
                    print(f"[SKILLS] [{origen}] '{texto[:40]}...' -> '{skill_label}' (score={score:.3f}, peso={peso}){peso_tag}")

        # v2.2: Ordenar por score_ponderado descendente (skills genéricas bajan en el ranking)
        skills_extraidas.sort(key=lambda x: x['score_ponderado'], reverse=True)

        # Agregar categorías L1/L2 para dashboards
        try:
            categorizer = get_categorizer()
            for skill in skills_extraidas:
                categoria = categorizer.categorize(
                    skill_uri=skill.get("skill_uri", ""),
                    skill_label=skill.get("skill_esco", "")
                )
                skill.update(categoria)
        except Exception as e:
            if self.verbose:
                print(f"[WARN] Error en categorización: {e}")

        return skills_extraidas

    def get_skills_for_offer(
        self,
        skills_declaradas: List[str],
        tareas_explicitas: str,
        merge: bool = True
    ) -> Tuple[List[str], List[Dict]]:
        """
        Combina skills declaradas con skills implícitas extraídas de tareas.

        Args:
            skills_declaradas: Lista de skills ya declaradas en la oferta
            tareas_explicitas: String con tareas separadas por ;
            merge: Si True, retorna lista unificada; si False, retorna separadas

        Returns:
            (skills_all, skills_implicitas_detalle)
        """
        # Normalizar skills declaradas
        declaradas_norm = {s.lower().strip() for s in skills_declaradas if s}

        # Extraer implícitas
        implicitas = self.extract_from_tasks(tareas_explicitas)

        # Filtrar implícitas que ya están declaradas
        implicitas_nuevas = [
            s for s in implicitas
            if s['skill_esco'].lower() not in declaradas_norm
        ]

        if merge:
            # Retornar lista unificada
            all_skills = list(skills_declaradas) + [s['skill_esco'] for s in implicitas_nuevas]
            return all_skills, implicitas_nuevas
        else:
            return skills_declaradas, implicitas_nuevas

    @classmethod
    def clear_cache(cls):
        """Limpia el cache (útil para tests)."""
        cls._model = None
        cls._skills_embeddings = None
        cls._skills_metadata = None
        cls._initialized = False

    def is_ready(self) -> bool:
        """Verifica si el extractor está listo (tiene embeddings cargados)."""
        return self.embeddings.size > 0 and len(self.metadata) > 0


def generate_skills_embeddings(
    db_path: str = None,
    output_dir: str = None,
    model_name: str = "BAAI/bge-m3",
    batch_size: int = 32,
    verbose: bool = True
) -> Tuple[int, str]:
    """
    Genera embeddings para todas las skills ESCO de la BD.

    Args:
        db_path: Path a la BD SQLite
        output_dir: Directorio de salida para embeddings
        model_name: Nombre del modelo de embeddings
        batch_size: Tamaño del batch para encoding
        verbose: Mostrar progreso

    Returns:
        (num_skills, output_path)
    """
    base_path = Path(__file__).parent
    db_path = Path(db_path) if db_path else base_path / "bumeran_scraping.db"
    output_dir = Path(output_dir) if output_dir else base_path / "embeddings"

    output_dir.mkdir(exist_ok=True)

    if verbose:
        print(f"[GEN] Generando embeddings para skills ESCO...")
        print(f"[GEN] BD: {db_path}")
        print(f"[GEN] Modelo: {model_name}")

    # Cargar skills de la BD
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute('''
        SELECT skill_uri, preferred_label_es, description_es
        FROM esco_skills
        WHERE preferred_label_es IS NOT NULL
        ORDER BY skill_uri
    ''')

    skills = []
    texts = []

    for row in cur:
        uri, label, description = row
        if label:
            skills.append({
                'uri': uri,
                'label': label,
                'description': description or ''
            })
            # Usar label + descripción para embedding más rico
            text = label
            if description:
                text = f"{label}: {description[:200]}"
            texts.append(text)

    conn.close()

    if verbose:
        print(f"[GEN] Skills a procesar: {len(skills)}")

    if not skills:
        print("[GEN] ERROR: No se encontraron skills en la BD")
        return 0, ""

    # Cargar modelo
    if verbose:
        print(f"[GEN] Cargando modelo...")
    model = SentenceTransformer(model_name)

    # Generar embeddings en batches
    if verbose:
        print(f"[GEN] Generando embeddings (batch_size={batch_size})...")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=verbose,
        normalize_embeddings=True
    )

    # Guardar
    embeddings_path = output_dir / "esco_skills_embeddings_full.npy"
    metadata_path = output_dir / "esco_skills_metadata_full.json"

    np.save(str(embeddings_path), embeddings)
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"[GEN] Embeddings guardados: {embeddings_path}")
        print(f"[GEN] Metadata guardados: {metadata_path}")
        print(f"[GEN] Shape: {embeddings.shape}")

    return len(skills), str(embeddings_path)


def main():
    """CLI para testing y generación de embeddings."""
    import argparse

    parser = argparse.ArgumentParser(description="Skills Implicit Extractor v1.0")
    parser.add_argument("--generate", action="store_true", help="Generar embeddings para todas las skills")
    parser.add_argument("--test", action="store_true", help="Ejecutar test con tareas de ejemplo")
    parser.add_argument("--tareas", type=str, help="Tareas a procesar (separadas por ;)")
    parser.add_argument("--threshold", type=float, default=0.55, help="Umbral de similitud")
    parser.add_argument("--top-k", type=int, default=3, help="Top K skills por tarea")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.generate:
        print("=" * 60)
        print("GENERACION DE EMBEDDINGS ESCO SKILLS")
        print("=" * 60)
        num_skills, path = generate_skills_embeddings(verbose=True)
        print(f"\nCompletado: {num_skills} skills procesadas")
        return

    if args.test or args.tareas:
        print("=" * 60)
        print("TEST: Skills Implicit Extractor")
        print("=" * 60)

        extractor = SkillsImplicitExtractor(
            threshold=args.threshold,
            top_k=args.top_k,
            verbose=args.verbose
        )

        if not extractor.is_ready():
            print("\n[ERROR] Embeddings no disponibles. Ejecutar primero:")
            print("  python skills_implicit_extractor.py --generate")
            return

        tareas = args.tareas or "Organización integral del depósito; Control de inventarios; Atención al cliente"

        print(f"\nTareas: {tareas}")
        print(f"Umbral: {args.threshold}")
        print(f"Top K: {args.top_k}")
        print()

        skills = extractor.extract_from_tasks(tareas)

        print(f"Skills implícitas encontradas: {len(skills)}")
        for i, skill in enumerate(skills, 1):
            print(f"\n{i}. {skill['skill_esco']}")
            print(f"   Tarea: {skill['tarea']}")
            print(f"   Score: {skill['score']}")
            print(f"   URI: {skill['skill_uri'][:50]}...")


if __name__ == "__main__":
    main()
