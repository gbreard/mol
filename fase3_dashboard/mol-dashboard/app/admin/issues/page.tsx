"use client";

import { useState, useEffect } from "react";
import { getIssues, getIssuesStats } from "@/lib/supabase";
import { Issue, IssueStats, ISSUE_TYPE_LABELS, ISSUE_ESTADO_LABELS, ISSUE_PRIORIDAD_LABELS } from "@/lib/types";
import { IssueList, IssueBadge } from "@/components/issues";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Search, RefreshCw, AlertCircle, CheckCircle, Clock, Filter } from "lucide-react";

export default function AdminIssuesPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [stats, setStats] = useState<IssueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [estadoFilter, setEstadoFilter] = useState<string>("all");
  const [tipoFilter, setTipoFilter] = useState<string>("all");
  const [prioridadFilter, setPrioridadFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const filters: Record<string, string> = {};
      if (estadoFilter !== "all") filters.estado = estadoFilter;
      if (tipoFilter !== "all") filters.tipo = tipoFilter;
      if (prioridadFilter !== "all") filters.prioridad = prioridadFilter;

      const [issuesData, statsData] = await Promise.all([
        getIssues(Object.keys(filters).length > 0 ? filters : undefined),
        getIssuesStats()
      ]);

      setIssues(issuesData);
      setStats(statsData);
    } catch (err) {
      console.error("Error loading issues:", err);
      setError("Error al cargar los issues");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [estadoFilter, tipoFilter, prioridadFilter]);

  // Filter by search term
  const filteredIssues = issues.filter((issue) =>
    issue.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    issue.descripcion?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Issues & Feedback</h1>
        <p className="text-gray-600">Gestion de issues y sugerencias del equipo</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-700">{stats.pendientes}</div>
                <div className="text-sm text-yellow-600">Pendientes</div>
              </div>
            </div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <AlertCircle className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-700">{stats.en_progreso}</div>
                <div className="text-sm text-blue-600">En progreso</div>
              </div>
            </div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-green-700">{stats.resueltos}</div>
                <div className="text-sm text-green-600">Resueltos</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-blue-600" />
          <h3 className="font-bold text-gray-900">Filtros</h3>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <Select value={estadoFilter} onValueChange={setEstadoFilter}>
            <SelectTrigger className="bg-gray-50">
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los estados</SelectItem>
              {Object.entries(ISSUE_ESTADO_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={tipoFilter} onValueChange={setTipoFilter}>
            <SelectTrigger className="bg-gray-50">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los tipos</SelectItem>
              {Object.entries(ISSUE_TYPE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={prioridadFilter} onValueChange={setPrioridadFilter}>
            <SelectTrigger className="bg-gray-50">
              <SelectValue placeholder="Prioridad" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas las prioridades</SelectItem>
              {Object.entries(ISSUE_PRIORIDAD_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Buscar..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-gray-50"
            />
          </div>
        </div>
      </div>

      {/* Refresh button */}
      <div className="flex justify-end mb-4">
        <Button
          variant="outline"
          size="sm"
          onClick={loadData}
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Cargando issues...</span>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600 font-medium">{error}</p>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="text-sm text-gray-500 mb-4">
            Mostrando {filteredIssues.length} issues
          </div>
          <IssueList issues={filteredIssues} showOfertaLink />
        </div>
      )}
    </div>
  );
}
