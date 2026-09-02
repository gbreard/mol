// Lógica de alertas del monitor de scraping — por cadencia, no umbral fijo.
// Los umbrales viven en config/scraping/portal_cadencia.json y llegan al
// frontend dentro de scraping_live_stats.portales[*] (inyectados por
// sync_scraping_stats.py). Estas funciones son puras y testeables.

export interface PortalLive {
  portal: string;
  total: number;
  ultimo_scraping: string;            // ISO o 'YYYY-MM-DD' (MAX(scrapeado_en) local)
  ultimos_7d: number;
  hoy: number;                        // inserciones netas últimas 24h
  origen?: "vps" | "local";
  cadencia?: "diaria" | "bisemanal" | "goteo";
  umbral_horas?: number;              // horas sin datos que disparan alerta
  cero_corridas?: number;             // N días seguidos en 0 (portales de goteo)
}

export interface HistoryDay {
  fecha: string;                      // 'YYYY-MM-DD'
  por_portal: Record<string, number>;
}

export type Nivel = "ok" | "warn" | "error";
export type TipoAlerta = "atrasado" | "corrio_cero" | "goteo_cero";

export interface PortalEval {
  portal: string;
  nivel: Nivel;
  horas_sin: number;
  tipo: TipoAlerta | null;
  mensaje: string | null;
}

const DEFAULT_UMBRAL = 96;
const HORA_CORTE_DIARIA = 12;         // pasada esta hora local, un diario ya debería tener datos de hoy

export function horasSin(ultimo: string | null | undefined, nowMs: number): number {
  if (!ultimo) return Infinity;
  const t = new Date(ultimo).getTime();
  if (isNaN(t)) return Infinity;
  return Math.max(0, (nowMs - t) / 3_600_000);
}

// Nivel por atraso: ok si hay datos frescos (< umbral); warn hasta 2×umbral;
// error a partir de 2×umbral (claramente roto).
export function nivelAtraso(hs: number, umbral: number): Nivel {
  if (hs < umbral) return "ok";
  if (hs < umbral * 2) return "warn";
  return "error";
}

// Días recientes consecutivos con 0 ofertas para el portal (goteo).
export function corridasEnCero(portal: string, history: HistoryDay[], n: number): number {
  const dias = [...history].sort((a, b) => (a.fecha < b.fecha ? 1 : -1)); // desc
  let count = 0;
  for (const d of dias.slice(0, n)) {
    if ((d.por_portal?.[portal] || 0) === 0) count++;
    else break;
  }
  return count;
}

export function evaluarPortal(
  p: PortalLive,
  history: HistoryDay[],
  nowMs: number,
  horaCorte: number = HORA_CORTE_DIARIA,
): PortalEval {
  const umbral = p.umbral_horas ?? DEFAULT_UMBRAL;
  const hs = horasSin(p.ultimo_scraping, nowMs);
  const horaActual = new Date(nowMs).getHours();

  // 1) Roto de verdad: atraso >= 2×umbral → error, gana sobre todo.
  if (hs >= umbral * 2) {
    return { portal: p.portal, nivel: "error", horas_sin: hs, tipo: "atrasado",
      mensaje: `sin datos hace ${Math.round(hs)}h (umbral ${umbral}h)` };
  }

  // 2) Goteo: N corridas seguidas en cero (aunque el atraso aún no llegue al umbral).
  if (p.cero_corridas && corridasEnCero(p.portal, history, p.cero_corridas) >= p.cero_corridas) {
    return { portal: p.portal, nivel: "warn", horas_sin: hs, tipo: "goteo_cero",
      mensaje: `${p.cero_corridas} corridas seguidas sin ofertas nuevas` };
  }

  // 3) Corrió pero trajo cero (diarios): portal vivo, esperado hoy, 0 en 24h.
  if (p.cadencia === "diaria" && p.hoy === 0 && p.total > 0 && horaActual >= horaCorte && hs < umbral * 2) {
    return { portal: p.portal, nivel: "warn", horas_sin: hs, tipo: "corrio_cero",
      mensaje: `se esperaba corrida hoy y trajo 0 ofertas nuevas` };
  }

  // 4) Atraso simple entre umbral y 2×umbral.
  if (hs >= umbral) {
    return { portal: p.portal, nivel: "warn", horas_sin: hs, tipo: "atrasado",
      mensaje: `sin datos hace ${Math.round(hs)}h (umbral ${umbral}h)` };
  }

  return { portal: p.portal, nivel: "ok", horas_sin: hs, tipo: null, mensaje: null };
}
