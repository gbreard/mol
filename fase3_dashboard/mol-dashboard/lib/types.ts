export interface DashboardFilters {
  territorio: string;
  provincia: string;
  localidad: string[];
  fechaDesde: Date | null;
  fechaHasta: Date | null;
  permanencia: string[];
  searchOcupacion: string;
  ocupacionesSeleccionadas: string[];
  // Filtros de Requerimientos (Issue #5)
  nivelEducativo: string[];
  experiencia: string;
  seniority: string[];
  modalidad: string[];
  jornada: string;
  skillsDigitales: boolean;
}

// ========== ISSUES/FEEDBACK SYSTEM ==========

export type IssueType = 'error_isco' | 'error_nlp' | 'error_skill' | 'sugerencia' | 'bug' | 'otro';
export type IssueEstado = 'pendiente' | 'en_progreso' | 'resuelto' | 'descartado';
export type IssuePrioridad = 'baja' | 'media' | 'alta' | 'critica';

export interface Issue {
  id: string;
  titulo: string;
  descripcion?: string;
  tipo: IssueType;
  estado: IssueEstado;
  prioridad: IssuePrioridad;
  id_oferta?: string;
  autor_id: string;
  autor_email: string;
  autor_nombre?: string;  // Nombre completo del autor
  created_at: string;
  updated_at: string;
  resuelto_at?: string;
  resuelto_por?: string;
  // Campos de tracking (workflow)
  agrupado_con?: string[];      // IDs de issues similares
  solucion_aplicada?: string;   // Descripción de la solución
  config_modificada?: string;   // Archivo de config modificado
  ofertas_afectadas?: number;   // Cantidad de ofertas corregidas
  sprint?: string;              // Sprint/iteración asignada
}

export interface IssueStats {
  pendientes: number;
  en_progreso: number;
  resueltos: number;
}

// Labels para UI
export const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
  error_isco: 'Error ISCO',
  error_nlp: 'Error NLP',
  error_skill: 'Error Skill',
  sugerencia: 'Sugerencia',
  bug: 'Bug',
  otro: 'Otro'
};

export const ISSUE_ESTADO_LABELS: Record<IssueEstado, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En progreso',
  resuelto: 'Resuelto',
  descartado: 'Descartado'
};

export const ISSUE_PRIORIDAD_LABELS: Record<IssuePrioridad, string> = {
  baja: 'Baja',
  media: 'Media',
  alta: 'Alta',
  critica: 'Critica'
};

// ========== SKILLS INTELLIGENCE DASHBOARD ==========

export interface SkillItem {
  id: string;
  label: string;
  L1: string;
  L2: string;
  description?: string;
}

export interface SimilarOccupation {
  id: string;
  label: string;
  isco: string;
  jaccard: number;
  shared: number;
}

export interface OccupationDetail {
  label: string;
  isco: string;
  skills: {
    essential: SkillItem[];
    optional: SkillItem[];
  };
  knowledge: {
    essential: SkillItem[];
    optional: SkillItem[];
  };
  similar: SimilarOccupation[];
  counts: {
    skills_essential: number;
    skills_optional: number;
    knowledge_essential: number;
    knowledge_optional: number;
    total_skills: number;
    total_knowledge: number;
    similar: number;
  };
}

export interface OccupationFullDetailIndex {
  [occupationId: string]: OccupationDetail;
}

export interface SearchableSkill {
  id: string;
  label: string;
  type: 'skill' | 'knowledge';
  L1: string;
  L2: string;
  essential: number;  // count of occupations
  optional: number;   // count of occupations
  total: number;
  description?: string;
}

export interface SkillsSearchableIndex {
  skills: SearchableSkill[];
  stats: {
    total: number;
    skills: number;
    knowledge: number;
    with_occupations: number;
    without_occupations: number;
  };
}

// ========== PERFIL ARGENTINA (MOL vs ESCO) ==========

export interface MOLSkillItem {
  label_original: string;
  label_normalized: string;
  frequency: number;
  percentage: number;
  is_esco_essential: boolean;
  is_esco_optional: boolean;
  is_emerging: boolean;
  esco_uri?: string;
  description?: string;
  L1?: string;
  L2?: string;
}

export interface OccupationMOLProfile {
  esco_uuid: string;
  esco_label: string;
  offer_count: number;
  mol_skills: MOLSkillItem[];
  comparison: {
    coverage_essential: number;
    coverage_total: number;
    common_count: number;
    common_optional_count: number;
    emerging_count: number;
    missing_count: number;
    esco_essential_count: number;
    esco_optional_count: number;
    mol_unique_count: number;
    common_labels: string[];
    common_optional_labels: string[];
    emerging_labels: string[];
    missing_labels: string[];
  };
}

export interface MOLSkillsProfileIndex {
  version: string;
  generated_at: string;
  stats: {
    total_offers: number;
    total_occupations_with_mol: number;
    avg_skills_per_offer: number;
  };
  occupations: { [esco_uuid: string]: OccupationMOLProfile };
}

// ========== PERFIL CONSOLIDADO ==========

export interface ConsolidatedSkill {
  label_normalized: string;
  label_original: string;
  source: 'esco_common' | 'mol_approved';
  frequency?: number;
  percentage?: number;
  esco_uri?: string;
  description?: string;
  L1?: string;
  L2?: string;
  approved_at?: string;
}

export interface ConsolidatedProfile {
  esco_uuid: string;
  esco_label: string;
  last_updated: string;
  consolidated_skills: ConsolidatedSkill[];
  stats: {
    total_consolidated: number;
    from_esco_common: number;
    from_mol_approved: number;
    pending_candidates: number;
  };
}

export interface ConsolidatedProfilesIndex {
  version: string;
  generated_at: string;
  profiles: { [esco_uuid: string]: ConsolidatedProfile };
}
