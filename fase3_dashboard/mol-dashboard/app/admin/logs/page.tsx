"use client";

import { useState, useEffect } from "react";
import {
  FileText,
  Search,
  Filter,
  RefreshCw,
  User,
  Clock,
  Activity,
  Loader2,
  ChevronDown
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface LogEntry {
  id: string;
  usuario_id: string;
  organizacion_id: string | null;
  accion: string;
  recurso: string;
  recurso_id: string | null;
  detalle: any;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

interface EventoUso {
  id: string;
  usuario_id: string;
  evento: string;
  categoria: string;
  metadata: any;
  created_at: string;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [eventos, setEventos] = useState<EventoUso[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'audit' | 'eventos'>('audit');
  const [searchTerm, setSearchTerm] = useState("");
  const [filterAccion, setFilterAccion] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      if (!supabase) {
        console.warn('Supabase no configurado');
        setLoading(false);
        return;
      }

      // Audit logs
      const { data: auditData } = await supabase
        .from('audit_log')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100);

      if (auditData) {
        setLogs(auditData);
      }

      // Eventos de uso
      const { data: eventosData } = await supabase
        .from('eventos_uso')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100);

      if (eventosData) {
        setEventos(eventosData);
      }

    } catch (error) {
      console.error('Error cargando logs:', error);
    } finally {
      setLoading(false);
    }
  }

  const getAccionColor = (accion: string) => {
    const colors: Record<string, string> = {
      'login': 'bg-green-100 text-green-800',
      'logout': 'bg-gray-100 text-gray-800',
      'create': 'bg-blue-100 text-blue-800',
      'update': 'bg-amber-100 text-amber-800',
      'delete': 'bg-red-100 text-red-800',
      'view': 'bg-purple-100 text-purple-800',
      'export': 'bg-cyan-100 text-cyan-800',
    };
    return colors[accion.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  const getCategoriaColor = (categoria: string) => {
    const colors: Record<string, string> = {
      'navigation': 'bg-blue-100 text-blue-800',
      'filter': 'bg-purple-100 text-purple-800',
      'export': 'bg-green-100 text-green-800',
      'search': 'bg-amber-100 text-amber-800',
    };
    return colors[categoria?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  const filteredLogs = logs.filter(log =>
    log.accion.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.recurso.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (filterAccion ? log.accion.toLowerCase() === filterAccion.toLowerCase() : true)
  );

  const filteredEventos = eventos.filter(ev =>
    ev.evento.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ev.categoria.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Logs de Auditoría</h1>
          <p className="text-gray-500 mt-1">Registro de actividad del sistema</p>
        </div>
        <button
          onClick={() => { setLoading(true); loadData(); }}
          className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          Actualizar
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'audit'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Audit Log ({logs.length})
        </button>
        <button
          onClick={() => setActiveTab('eventos')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'eventos'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Eventos de Uso ({eventos.length})
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Buscar en logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        {activeTab === 'audit' && (
          <select
            value={filterAccion}
            onChange={(e) => setFilterAccion(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          >
            <option value="">Todas las acciones</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="view">View</option>
            <option value="export">Export</option>
          </select>
        )}
      </div>

      {/* Tabla Audit Log */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Fecha/Hora</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Acción</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Recurso</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Detalle</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-gray-500">
                    No hay logs de auditoría registrados
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAccionColor(log.accion)}`}>
                        {log.accion}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {log.recurso}
                      {log.recurso_id && <span className="text-gray-400 ml-1">#{log.recurso_id}</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {typeof log.detalle === 'object' ? JSON.stringify(log.detalle) : log.detalle || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 font-mono">
                      {log.ip_address || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tabla Eventos de Uso */}
      {activeTab === 'eventos' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Fecha/Hora</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Evento</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Categoría</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-900">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredEventos.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-gray-500">
                    No hay eventos de uso registrados
                  </td>
                </tr>
              ) : (
                filteredEventos.map((ev) => (
                  <tr key={ev.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(ev.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      {ev.evento}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoriaColor(ev.categoria)}`}>
                        {ev.categoria}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {typeof ev.metadata === 'object' ? JSON.stringify(ev.metadata) : ev.metadata || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
