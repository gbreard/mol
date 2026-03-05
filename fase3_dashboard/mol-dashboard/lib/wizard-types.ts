// Types for the Validation Wizard (P-40 v2.0)

/** Occupation correction from the ESCO search tab */
export interface OcupacionCorregida {
  esco_uuid: string;
  esco_label: string;
  isco_code: string;
}

/** Edited NLP field — only fields that changed are included */
export interface NlpEditado {
  area_funcional?: string;
  nivel_seniority?: string;
  modalidad?: string;
  nivel_educativo?: string;
  experiencia_min_anios?: number;
  salario_min?: number;
  salario_max?: number;
  provincia?: string;
  localidad?: string;
  clae_seccion?: string;
  clae_grupo?: string;
  clae_code?: string;
}

/** CLAE nomenclador structure (loaded from JSON) */
export interface ClaeNomenclador {
  secciones: Record<string, { nombre: string; clae2: string }>;
  grupos: Record<string, { seccion: string; nombre: string; clae2: string }>;
  actividades: Record<string, { grupo: string; seccion: string; nombre: string }>;
}

/** A single edited task with optional associated skills */
export interface TareaEditada {
  texto: string;
  skills: SkillAsociada[];
}

/** A skill associated to a task (or standalone) */
export interface SkillAsociada {
  id: string;
  label: string;
  type: "skill" | "knowledge";
}

/** Aggregated corrections from all wizard tabs */
export interface WizardCorrecciones {
  ocupacion_corregida?: OcupacionCorregida;
  nlp_editado?: NlpEditado;
  tareas_editadas?: TareaEditada[];
  skills_editadas?: SkillAsociada[];
  nota?: string;
}

/** Trigger that opened the wizard — determines default tab */
export type WizardTrigger = "error" | "revisar" | "editar";
