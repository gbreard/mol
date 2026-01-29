"use client";

import { Issue } from "@/lib/types";
import { IssueBadge } from "./IssueBadge";
import { Button } from "@/components/ui/button";
import { Check, Clock, FileText } from "lucide-react";
import { updateIssue } from "@/lib/supabase";
import { useIssues } from "@/contexts/IssueContext";
import { useState } from "react";

interface IssueListProps {
  issues: Issue[];
  compact?: boolean;
  showOfertaLink?: boolean;
}

// Helper para tiempo relativo
function timeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "ahora";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  const weeks = Math.floor(days / 7);
  return `${weeks}sem`;
}

function IssueItem({ issue, compact, showOfertaLink }: { issue: Issue; compact?: boolean; showOfertaLink?: boolean }) {
  const { refreshIssues } = useIssues();
  const [loading, setLoading] = useState(false);

  const handleMarkResolved = async () => {
    setLoading(true);
    try {
      await updateIssue(issue.id, { estado: "resuelto" });
      await refreshIssues();
    } catch (error) {
      console.error("Error updating issue:", error);
    } finally {
      setLoading(false);
    }
  };

  if (compact) {
    return (
      <div className="flex items-start gap-3 py-3 px-2 hover:bg-gray-50 rounded-lg transition-colors group">
        <div
          className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
            issue.prioridad === "critica"
              ? "bg-red-500"
              : issue.prioridad === "alta"
              ? "bg-orange-500"
              : issue.prioridad === "media"
              ? "bg-blue-500"
              : "bg-gray-400"
          }`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-gray-900 truncate">{issue.titulo}</p>
            <span className="text-xs text-gray-500 flex-shrink-0">{timeAgo(issue.created_at)}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <IssueBadge variant="tipo" value={issue.tipo} size="sm" />
            {issue.id_oferta && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <FileText className="w-3 h-3" />
                #{issue.id_oferta.slice(-6)}
              </span>
            )}
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleMarkResolved}
          disabled={loading}
          className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0"
          title="Marcar como resuelto"
        >
          <Check className="w-4 h-4 text-green-600" />
        </Button>
      </div>
    );
  }

  // Full version
  return (
    <div className="border-b border-gray-100 py-4 last:border-0">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <IssueBadge variant="tipo" value={issue.tipo} />
            <IssueBadge variant="prioridad" value={issue.prioridad} />
            <IssueBadge variant="estado" value={issue.estado} />
          </div>
          <h4 className="font-medium text-gray-900 mb-1">{issue.titulo}</h4>
          {issue.descripcion && (
            <p className="text-sm text-gray-600 mb-2">{issue.descripcion}</p>
          )}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {timeAgo(issue.created_at)}
            </span>
            <span>{issue.autor_email}</span>
            {issue.id_oferta && showOfertaLink && (
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                Oferta #{issue.id_oferta}
              </span>
            )}
          </div>
        </div>
        {issue.estado !== "resuelto" && issue.estado !== "descartado" && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkResolved}
            disabled={loading}
            className="text-green-600 border-green-200 hover:bg-green-50"
          >
            <Check className="w-4 h-4 mr-1" />
            Resolver
          </Button>
        )}
      </div>
    </div>
  );
}

export function IssueList({ issues, compact = false, showOfertaLink = true }: IssueListProps) {
  if (issues.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-sm">No hay issues pendientes</p>
      </div>
    );
  }

  return (
    <div className={compact ? "divide-y divide-gray-100" : ""}>
      {issues.map((issue) => (
        <IssueItem
          key={issue.id}
          issue={issue}
          compact={compact}
          showOfertaLink={showOfertaLink}
        />
      ))}
    </div>
  );
}
