"use client";

import { useState } from "react";
import {
  Settings,
  Database,
  Cloud,
  Bell,
  Shield,
  Palette,
  Save,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  ExternalLink
} from "lucide-react";

interface ConfigSection {
  id: string;
  title: string;
  icon: any;
  description: string;
}

export default function ConfiguracionPage() {
  const [activeSection, setActiveSection] = useState('database');
  const [saved, setSaved] = useState(false);

  const sections: ConfigSection[] = [
    { id: 'database', title: 'Base de Datos', icon: Database, description: 'Configuración de conexiones' },
    { id: 'supabase', title: 'Supabase', icon: Cloud, description: 'Sincronización y API' },
    { id: 'scraping', title: 'Scraping', icon: RefreshCw, description: 'Fuentes y frecuencia' },
    { id: 'notificaciones', title: 'Notificaciones', icon: Bell, description: 'Alertas del sistema' },
    { id: 'seguridad', title: 'Seguridad', icon: Shield, description: 'Autenticación y permisos' },
    { id: 'apariencia', title: 'Apariencia', icon: Palette, description: 'Tema y personalización' },
  ];

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Configuración</h1>
          <p className="text-gray-500 mt-1">Ajustes del sistema MOL</p>
        </div>
        {saved && (
          <div className="flex items-center gap-2 text-green-600 bg-green-50 px-4 py-2 rounded-lg">
            <CheckCircle className="w-5 h-5" />
            Cambios guardados
          </div>
        )}
      </div>

      <div className="flex gap-6">
        {/* Sidebar de secciones */}
        <div className="w-64 flex-shrink-0">
          <nav className="space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                  activeSection === section.id
                    ? 'bg-purple-100 text-purple-700'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <section.icon className="w-5 h-5" />
                <div>
                  <p className="font-medium">{section.title}</p>
                  <p className="text-xs text-gray-500">{section.description}</p>
                </div>
              </button>
            ))}
          </nav>
        </div>

        {/* Contenido */}
        <div className="flex-1">
          {activeSection === 'database' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuración de Base de Datos</h2>

              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">SQLite Local</p>
                    <p className="text-sm text-gray-500">database/bumeran_scraping.db</p>
                  </div>
                  <span className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    Conectado
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ruta de la base de datos
                    </label>
                    <input
                      type="text"
                      defaultValue="database/bumeran_scraping.db"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      readOnly
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tamaño estimado
                    </label>
                    <input
                      type="text"
                      defaultValue="~150 MB"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      readOnly
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'supabase' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuración de Supabase</h2>

              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                  <div>
                    <p className="font-medium text-gray-900">Estado de conexión</p>
                    <p className="text-sm text-gray-500">uywzoyhjjofsvvsrrnek.supabase.co</p>
                  </div>
                  <span className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    Conectado
                  </span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    URL del proyecto
                  </label>
                  <input
                    type="text"
                    defaultValue={process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://...supabase.co'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                    readOnly
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Anon Key
                  </label>
                  <input
                    type="password"
                    defaultValue="••••••••••••••••••••"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                    readOnly
                  />
                </div>

                <a
                  href="https://supabase.com/dashboard/project/uywzoyhjjofsvvsrrnek"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700"
                >
                  Abrir Dashboard de Supabase
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          )}

          {activeSection === 'scraping' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuración de Scraping</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Fuentes activas
                  </label>
                  <div className="space-y-2">
                    {['Bumeran', 'ZonaJobs', 'Computrabajo', 'Indeed', 'LinkedIn'].map((source) => (
                      <label key={source} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          defaultChecked={['Bumeran', 'ZonaJobs', 'Computrabajo'].includes(source)}
                          className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                        />
                        <span className="text-gray-700">{source}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Frecuencia de scraping
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
                    <option value="daily">Diario</option>
                    <option value="twice">2 veces al día</option>
                    <option value="hourly">Cada hora</option>
                    <option value="manual">Manual</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Límite de ofertas por scraping
                  </label>
                  <input
                    type="number"
                    defaultValue={500}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </div>
          )}

          {activeSection === 'notificaciones' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuración de Notificaciones</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Alertas por email
                  </label>
                  <div className="space-y-2">
                    {[
                      { id: 'scraping_error', label: 'Errores de scraping' },
                      { id: 'new_offers', label: 'Nuevas ofertas procesadas' },
                      { id: 'validation_needed', label: 'Ofertas pendientes de validación' },
                      { id: 'sync_status', label: 'Estado de sincronización' },
                    ].map((notif) => (
                      <label key={notif.id} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          defaultChecked={notif.id === 'scraping_error'}
                          className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                        />
                        <span className="text-gray-700">{notif.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email para notificaciones
                  </label>
                  <input
                    type="email"
                    placeholder="admin@ejemplo.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </div>
          )}

          {activeSection === 'seguridad' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuración de Seguridad</h2>

              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                  <div>
                    <p className="font-medium text-gray-900">Autenticación</p>
                    <p className="text-sm text-gray-500">Supabase Auth (Email/Password)</p>
                  </div>
                  <span className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    Activo
                  </span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Opciones de seguridad
                  </label>
                  <div className="space-y-2">
                    {[
                      { id: 'mfa', label: 'Autenticación de dos factores (2FA)', enabled: false },
                      { id: 'session_timeout', label: 'Timeout de sesión (30 min)', enabled: true },
                      { id: 'ip_whitelist', label: 'Lista blanca de IPs', enabled: false },
                      { id: 'audit_log', label: 'Log de auditoría', enabled: true },
                    ].map((opt) => (
                      <label key={opt.id} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          defaultChecked={opt.enabled}
                          className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                        />
                        <span className="text-gray-700">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'apariencia' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configuración de Apariencia</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Tema
                  </label>
                  <div className="flex gap-4">
                    {['Claro', 'Oscuro', 'Sistema'].map((tema) => (
                      <label key={tema} className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="tema"
                          defaultChecked={tema === 'Claro'}
                          className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                        />
                        <span className="text-gray-700">{tema}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Color primario
                  </label>
                  <div className="flex gap-2">
                    {['#7c3aed', '#2563eb', '#059669', '#dc2626', '#ea580c'].map((color) => (
                      <button
                        key={color}
                        className="w-8 h-8 rounded-full border-2 border-white shadow-md"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre del dashboard
                  </label>
                  <input
                    type="text"
                    defaultValue="Monitor de Ofertas Laborales"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Botón guardar */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Save className="w-5 h-5" />
              Guardar cambios
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
