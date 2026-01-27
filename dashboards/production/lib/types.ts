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
