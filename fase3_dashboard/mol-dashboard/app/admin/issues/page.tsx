"use client";

import { useState, useEffect } from "react";
import { getIssues, getIssuesStats, supabase } from "@/lib/supabase";
import { Issue, IssueStats, ISSUE_TYPE_LABELS, ISSUE_ESTADO_LABELS, ISSUE_PRIORIDAD_LABELS } from "@/lib/types";
import { IssueList, IssueBadge } from "@/components/issues";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Search, RefreshCw, AlertCircle, CheckCircle, Clock, Filter, FileText, Copy, Download } from "lucide-react";

export default function AdminIssuesPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [stats, setStats] = useState<IssueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [estadoFilter, setEstadoFilter] = useState<string>("all");
  const [tipoFilter, setTipoFilter] = useState<string>("all");
  const [prioridadFilter, setPrioridadFilter] = useState<string>("all");
  const [autorFilter, setAutorFilter] = useState<string>("all");
  const [autores, setAutores] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [incluirAuto, setIncluirAuto] = useState(false);
  // M-09b: Correcciones asociadas y reporte
  const [corrections, setCorrections] = useState<Record<string, any>>({});
  const [reportOpen, setReportOpen] = useState(false);
  const [reportText, setReportText] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const filters: Record<string, any> = {};
      if (estadoFilter !== "all") filters.estado = estadoFilter;
      if (tipoFilter !== "all") filters.tipo = tipoFilter;
      if (prioridadFilter !== "all") filters.prioridad = prioridadFilter;
      if (autorFilter !== "all") filters.autor_email = autorFilter;
      if (incluirAuto) filters.incluir_auto = true;

      const [issuesData, statsData] = await Promise.all([
        getIssues(Object.keys(filters).length > 0 ? filters : undefined),
        getIssuesStats()
      ]);

      setIssues(issuesData);
      setStats(statsData);

      // M-09b: Cargar correcciones para issues con id_oferta
      const ofertaIds = [...new Set(issuesData.map(i => i.id_oferta).filter(Boolean))];
      if (ofertaIds.length > 0 && supabase) {
        try {
          const { data: corrData } = await supabase
            .from('ofertas_dashboard')
            .select('id_oferta,validacion_correcciones,titulo,isco_code,isco_label')
            .in('id_oferta', ofertaIds.slice(0, 100));
          const corrMap: Record<string, any> = {};
          corrData?.forEach(r => {
            if (r.validacion_correcciones) corrMap[r.id_oferta] = { ...r.validacion_correcciones, _titulo: r.titulo, _isco: r.isco_code, _isco_label: r.isco_label };
          });
          setCorrections(corrMap);
        } catch {}
      }

      // Extract unique authors for filter (only on first load or when no autor filter)
      if (autores.length === 0 && issuesData.length > 0) {
        const emails = [...new Set(issuesData.map(i => i.autor_email).filter(Boolean))].sort();
        setAutores(emails);
      }
    } catch (err) {
      console.error("Error loading issues:", err);
      setError("Error al cargar los issues");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [estadoFilter, tipoFilter, prioridadFilter, autorFilter, incluirAuto]);

  // M-09b: Inferir tipo de corrección
  function inferCorrectionType(issueId: string, ofertaId?: string): string | null {
    if (!ofertaId) return null;
    const corr = corrections[ofertaId];
    if (!corr) return null;
    if (corr.ocupacion_corregida) return "Matching";
    if (corr.nlp_editado) return "NLP";
    if (corr.skills_editadas) return "Skills";
    const nota = (corr.nota || "").toLowerCase();
    if (nota.includes("sinónimo") || nota.includes("equivale") || nota.includes("diccionario") || nota.includes("repositor") || nota.includes("reponedor")) return "Sinónimos";
    if (nota.includes("ruido") || nota.includes("no es tarea") || nota.includes("fragmento")) return "Limpieza";
    if (nota.length > 50) return "Análisis";
    return null;
  }

  // M-09b: Generar reporte markdown para Claude Code
  function generateReport() {
    const pendientes = filteredIssues.filter(i => i.estado === "pendiente" && i.id_oferta);
    const sections: string[] = [];
    sections.push(`# Reporte de correcciones para procesamiento`);
    sections.push(`Generado: ${new Date().toISOString().slice(0, 10)} | Correcciones: ${pendientes.length}\n`);

    // Sección 1: Correcciones ISCO
    const iscoCorr = pendientes.filter(i => corrections[i.id_oferta]?.ocupacion_corregida);
    if (iscoCorr.length > 0) {
      sections.push(`## CORRECCIONES DE ISCO (para reglas de matching)\n`);
      iscoCorr.forEach(i => {
        const c = corrections[i.id_oferta];
        const oc = c.ocupacion_corregida;
        sections.push(`### Oferta: ${c._titulo || i.titulo} (ID: ${i.id_oferta})`);
        sections.push(`- ISCO sistema: ${c._isco} (${c._isco_label})`);
        sections.push(`- ISCO correcto: ${oc.isco_code} (${oc.esco_label})`);
        if (c.nota) sections.push(`- Nota: ${c.nota}`);
        sections.push(`- Issue: #${i.id.slice(0, 8)}\n`);
      });
    }

    // Sección 2: Notas con análisis
    const notasLargas = pendientes.filter(i => {
      const c = corrections[i.id_oferta];
      return c?.nota && c.nota.length > 50 && !c.ocupacion_corregida;
    });
    if (notasLargas.length > 0) {
      sections.push(`## NOTAS CON ANÁLISIS (para sinónimos / reglas NLP)\n`);
      notasLargas.forEach(i => {
        const c = corrections[i.id_oferta];
        const tipo = inferCorrectionType(i.id, i.id_oferta);
        sections.push(`### Oferta: ${c._titulo || i.titulo} (ID: ${i.id_oferta})`);
        sections.push(`- Tipo inferido: ${tipo || "General"}`);
        sections.push(`- Nota: ${c.nota}`);
        if (i.descripcion) sections.push(`- Descripción issue: ${i.descripcion.slice(0, 300)}`);
        sections.push(``);
      });
    }

    // Sección 3: Skills editadas
    const skillsCorr = pendientes.filter(i => corrections[i.id_oferta]?.skills_editadas);
    if (skillsCorr.length > 0) {
      sections.push(`## SKILLS EDITADAS (para Gold Set / training pairs)\n`);
      skillsCorr.forEach(i => {
        const c = corrections[i.id_oferta];
        sections.push(`### Oferta: ${c._titulo || i.titulo} (ID: ${i.id_oferta})`);
        const skills = c.skills_editadas || [];
        skills.forEach((s: any) => sections.push(`  - ${s.label} (${s.type})`));
        sections.push(``);
      });
    }

    // Sección 4: Instrucciones
    sections.push(`## INSTRUCCIONES PARA CLAUDE CODE\n`);
    sections.push(`Analizá las correcciones anteriores y para cada una proponé:`);
    sections.push(`1. Si es corrección de ISCO → ¿Requiere regla nueva en matching_rules_business.json?`);
    sections.push(`2. Si hay sinónimos propuestos → Propone entrada para sinonimos_argentinos_esco.json`);
    sections.push(`3. Si hay skills editadas → Propone agregar al Gold Set como caso validado`);
    sections.push(`4. Para cada propuesta incluí: justificación, casos cubiertos, linaje (issue_id, oferta)`);

    const report = sections.join("\n");
    setReportText(report);
    setReportOpen(true);
  }

  // Filter by search term
  const filteredIssues = issues.filter((issue) =>
    issue.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    issue.descripcion?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Issues & Feedback</h1>
          <p className="text-gray-600">Gestion de issues y sugerencias del equipo</p>
        </div>
        <Button variant="outline" size="sm" onClick={generateReport}
          className="flex items-center gap-2">
          <FileText className="w-4 h-4" /> Generar reporte para Claude Code
        </Button>
      </div>

      {/* M-09b: Modal de reporte */}
      {reportOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Reporte para Claude Code</h2>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => {
                  navigator.clipboard.writeText(reportText);
                }}>
                  <Copy className="w-4 h-4 mr-1" /> Copiar
                </Button>
                <Button variant="outline" size="sm" onClick={() => {
                  const blob = new Blob([reportText], { type: "text/markdown" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url; a.download = `reporte_correcciones_${new Date().toISOString().slice(0, 10)}.md`;
                  a.click(); URL.revokeObjectURL(url);
                }}>
                  <Download className="w-4 h-4 mr-1" /> Descargar .md
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setReportOpen(false)}>✕</Button>
              </div>
            </div>
            <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs font-mono whitespace-pre-wrap overflow-y-auto max-h-[60vh]">
              {reportText}
            </pre>
          </div>
        </div>
      )}

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
        <div className="grid grid-cols-5 gap-4">
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

          <Select value={autorFilter} onValueChange={setAutorFilter}>
            <SelectTrigger className="bg-gray-50">
              <SelectValue placeholder="Usuario" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los usuarios</SelectItem>
              {autores.map((email) => (
                <SelectItem key={email} value={email}>
                  {email.split("@")[0]}
                </SelectItem>
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
        <div className="mt-3 flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={incluirAuto}
              onChange={(e) => setIncluirAuto(e.target.checked)}
              className="rounded border-gray-300"
            />
            Incluir issues automáticos ({">"}99K)
          </label>
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
            {Object.keys(corrections).length > 0 && (
              <span className="ml-2 text-xs text-blue-500">
                ({Object.keys(corrections).length} con correcciones)
              </span>
            )}
          </div>
          <IssueList issues={filteredIssues.map(i => ({
            ...i,
            _correctionType: inferCorrectionType(i.id, i.id_oferta) || undefined,
          } as any))} showOfertaLink />
        </div>
      )}
    </div>
  );
}
