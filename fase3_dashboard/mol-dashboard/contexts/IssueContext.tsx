"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { Issue } from '@/lib/types';
import { getIssuesPendientes } from '@/lib/supabase';
import { usePathname } from 'next/navigation';

interface OfertaInfo {
  id_oferta: string;
  titulo: string;
  isco_code?: string;
}

interface IssueContextType {
  // Drawer state
  isOpen: boolean;
  openDrawer: (oferta?: OfertaInfo) => void;
  closeDrawer: () => void;

  // Selected oferta (for issue creation)
  selectedOferta: OfertaInfo | null;
  clearSelectedOferta: () => void;

  // Issues data
  pendingIssues: Issue[];
  pendingCount: number;
  refreshIssues: () => Promise<void>;

  // Form mode
  isCreating: boolean;
  setIsCreating: (val: boolean) => void;
}

const IssueContext = createContext<IssueContextType | undefined>(undefined);

export function IssueProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOferta, setSelectedOferta] = useState<OfertaInfo | null>(null);
  const [pendingIssues, setPendingIssues] = useState<Issue[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [loaded, setLoaded] = useState(false);
  // DEMO: en login, VIP y Oficina de Empleo los issues no se usan y la consulta da
  // timeout (57014): se cargan solo al abrir el panel de feedback.
  const pathname = usePathname() || '';
  const autoLoad = !['/login', '/vip', '/oficina-empleo'].some(p => pathname.startsWith(p));

  const refreshIssues = useCallback(async () => {
    try {
      const issues = await getIssuesPendientes();
      setPendingIssues(issues);
      setLoaded(true);
    } catch (error) {
      console.error('Error loading issues:', error);
    }
  }, []);

  // Load issues on mount
  useEffect(() => {
    if (autoLoad) refreshIssues();
  }, [refreshIssues, autoLoad]);

  const openDrawer = useCallback((oferta?: OfertaInfo) => {
    if (!loaded) refreshIssues();
    if (oferta) {
      setSelectedOferta(oferta);
      setIsCreating(true);
    }
    setIsOpen(true);
  }, [loaded, refreshIssues]);

  const closeDrawer = useCallback(() => {
    setIsOpen(false);
    setIsCreating(false);
  }, []);

  const clearSelectedOferta = useCallback(() => {
    setSelectedOferta(null);
  }, []);

  const value: IssueContextType = {
    isOpen,
    openDrawer,
    closeDrawer,
    selectedOferta,
    clearSelectedOferta,
    pendingIssues,
    pendingCount: pendingIssues.length,
    refreshIssues,
    isCreating,
    setIsCreating,
  };

  return (
    <IssueContext.Provider value={value}>
      {children}
    </IssueContext.Provider>
  );
}

export function useIssues() {
  const context = useContext(IssueContext);
  if (context === undefined) {
    throw new Error('useIssues must be used within an IssueProvider');
  }
  return context;
}
