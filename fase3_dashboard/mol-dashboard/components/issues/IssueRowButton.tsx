"use client";

import { useIssues } from "@/contexts/IssueContext";
import { MessageSquarePlus } from "lucide-react";

interface IssueRowButtonProps {
  id_oferta: string;
  titulo: string;
  isco_code?: string;
}

export function IssueRowButton({ id_oferta, titulo, isco_code }: IssueRowButtonProps) {
  const { openDrawer } = useIssues();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click
    openDrawer({ id_oferta, titulo, isco_code });
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center justify-center w-7 h-7 rounded text-gray-400 hover:text-blue-600 hover:bg-blue-100 transition-colors"
      title="Crear issue sobre esta oferta"
    >
      <MessageSquarePlus className="w-4 h-4" />
    </button>
  );
}
