"use client";

import { useState } from "react";
import { Clock, User, ChevronDown, ChevronUp } from "lucide-react";

interface ChangelogEntry {
  timestamp: string;
  user: string;
  version: number;
  action: string;
}

interface ConfigChangelogProps {
  changelog: ChangelogEntry[];
  version: number;
  updatedBy: string | null;
  updatedAt: string | null;
  source: string;
}

export function ConfigChangelog({ changelog, version, updatedBy, updatedAt, source }: ConfigChangelogProps) {
  const [expanded, setExpanded] = useState(false);

  if (source === "local" || !changelog || changelog.length === 0) {
    return (
      <div className="text-xs text-gray-400 bg-gray-50 rounded-lg px-4 py-2">
        Sin historial de cambios (fuente: JSON local)
      </div>
    );
  }

  const sorted = [...changelog].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  const shown = expanded ? sorted : sorted.slice(0, 3);

  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2 text-sm text-gray-700">
          <Clock className="w-4 h-4 text-gray-400" />
          <span className="font-medium">Historial de cambios</span>
          <span className="text-xs text-gray-400">
            v{version} — {changelog.length} ediciones
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {(expanded || shown.length > 0) && (
        <div className="border-t border-gray-200">
          {shown.map((entry, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 px-4 py-2 text-xs ${
                i === 0 ? "bg-blue-50/50" : ""
              } ${i < shown.length - 1 ? "border-b border-gray-100" : ""}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                <div
                  className={`w-2 h-2 rounded-full ${
                    i === 0 ? "bg-blue-500" : "bg-gray-300"
                  }`}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-gray-400">v{entry.version}</span>
                  <span className="text-gray-700">{entry.action}</span>
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-gray-400">
                  <User className="w-3 h-3" />
                  <span>{entry.user}</span>
                  <span>—</span>
                  <span>{formatTimestamp(entry.timestamp)}</span>
                </div>
              </div>
            </div>
          ))}

          {!expanded && sorted.length > 3 && (
            <button
              onClick={() => setExpanded(true)}
              className="w-full px-4 py-1.5 text-xs text-blue-600 hover:bg-blue-50 border-t border-gray-100"
            >
              Ver {sorted.length - 3} cambios anteriores
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleDateString("es-AR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}
