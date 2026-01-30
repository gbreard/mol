export interface DashboardFilters {
  territorio: string;
  provincia: string;
  localidad: string;
  fechaDesde: Date | null;
  fechaHasta: Date | null;
  permanencia: string[];
  searchOcupacion: string;
  ocupacionesSeleccionadas: string[];
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
