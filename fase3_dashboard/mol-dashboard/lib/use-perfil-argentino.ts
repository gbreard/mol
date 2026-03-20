'use client';

import { useState, useEffect } from 'react';

/**
 * Skill del perfil consolidado argentino.
 * Incluye source para distinguir ESCO puro de emergentes argentinas.
 */
export interface SkillConsolidada {
  label: string;
  label_normalized: string;
  uri?: string;
  source: 'esco_common' | 'argentina_approved';
  L1?: string;
  L2?: string;
  percentage_when_approved?: number;
}

/**
 * Perfil consolidado de una ocupación en el ESCO Argentino.
 */
export interface OcupacionConsolidada {
  label: string;
  isco: string;
  skills_consolidadas: SkillConsolidada[];
  total_skills: number;
  skills_from_esco: number;
  skills_from_argentina: number;
  cobertura_esco_essential?: number;
}

/**
 * Snapshot completo de la versión activa del perfil argentino.
 * Keyed por esco_occupation_uri.
 */
export interface PerfilArgentinoSnapshot {
  [occupationUri: string]: OcupacionConsolidada;
}

export interface PerfilArgentinoState {
  snapshot: PerfilArgentinoSnapshot | null;
  version: string | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook que carga la versión activa del perfil consolidado argentino.
 * Si no hay versión activa, retorna null y el matching usa ESCO puro como fallback.
 */
export function usePerfilArgentino(): PerfilArgentinoState {
  const [state, setState] = useState<PerfilArgentinoState>({
    snapshot: null,
    version: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadPerfilActivo() {
      try {
        const res = await fetch('/api/perfil-argentino-versiones');
        if (!res.ok) {
          // Si no hay API o falla, fallback a ESCO puro silenciosamente
          if (!cancelled) {
            setState({ snapshot: null, version: null, isLoading: false, error: null });
          }
          return;
        }

        const data = await res.json();
        const activa = data.activa;

        if (!activa || !activa.snapshot) {
          // No hay versión activa — fallback a ESCO puro
          if (!cancelled) {
            setState({ snapshot: null, version: null, isLoading: false, error: null });
          }
          return;
        }

        // Parsear snapshot (puede venir como string o como objeto)
        const snapshot = typeof activa.snapshot === 'string'
          ? JSON.parse(activa.snapshot)
          : activa.snapshot;

        if (!cancelled) {
          setState({
            snapshot,
            version: activa.version,
            isLoading: false,
            error: null,
          });
        }
      } catch {
        // Error de red — fallback silencioso a ESCO puro
        if (!cancelled) {
          setState({ snapshot: null, version: null, isLoading: false, error: null });
        }
      }
    }

    loadPerfilActivo();
    return () => { cancelled = true; };
  }, []);

  return state;
}

/**
 * Dado un occupation URI, retorna las skills del perfil argentino si existe,
 * o null si no tiene perfil argentino (usar ESCO puro como fallback).
 */
export function getSkillsConsolidadas(
  snapshot: PerfilArgentinoSnapshot | null,
  occupationUri: string
): SkillConsolidada[] | null {
  if (!snapshot) return null;
  const perfil = snapshot[occupationUri];
  if (!perfil || !perfil.skills_consolidadas || perfil.skills_consolidadas.length === 0) {
    return null;
  }
  return perfil.skills_consolidadas;
}
