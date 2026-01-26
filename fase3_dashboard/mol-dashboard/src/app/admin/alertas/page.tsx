'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/browser'

interface Alerta {
  id: string
  nombre: string
  tipo: string
  configuracion: Record<string, unknown>
  activa: boolean
  frecuencia: string
  ultima_ejecucion: string | null
  created_at: string
}

const tiposAlerta = [
  { value: 'nuevas_ofertas', label: 'Nuevas ofertas', description: 'Notifica cuando hay nuevas ofertas que coinciden con criterios' },
  { value: 'umbral_ocupacion', label: 'Umbral ocupacion', description: 'Notifica cuando una ocupacion supera un umbral de ofertas' },
  { value: 'keyword_match', label: 'Keyword match', description: 'Notifica cuando aparecen ofertas con palabras clave' },
]

export default function AdminAlertasPage() {
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [nombre, setNombre] = useState('')
  const [tipo, setTipo] = useState('nuevas_ofertas')
  const [frecuencia, setFrecuencia] = useState('diaria')
  const [submitting, setSubmitting] = useState(false)

  const supabase = createClient()

  useEffect(() => {
    cargarAlertas()
  }, [])

  const cargarAlertas = async () => {
    setLoading(true)

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    const { data: currentUser } = await supabase
      .from('usuarios')
      .select('organizacion_id')
      .eq('auth_id', user.id)
      .single()

    if (!currentUser) return

    const { data } = await supabase
      .from('alertas')
      .select('*')
      .eq('organizacion_id', currentUser.organizacion_id)
      .order('created_at', { ascending: false })

    setAlertas(data || [])
    setLoading(false)
  }

  const handleCrearAlerta = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    const { data: currentUser } = await supabase
      .from('usuarios')
      .select('id, organizacion_id')
      .eq('auth_id', user.id)
      .single()

    if (!currentUser) return

    const { error } = await supabase
      .from('alertas')
      .insert({
        nombre,
        tipo,
        frecuencia,
        configuracion: {},
        usuario_id: currentUser.id,
        organizacion_id: currentUser.organizacion_id,
      })

    if (!error) {
      setNombre('')
      setTipo('nuevas_ofertas')
      setFrecuencia('diaria')
      setShowForm(false)
      cargarAlertas()
    }

    setSubmitting(false)
  }

  const toggleAlerta = async (id: string, activa: boolean) => {
    await supabase
      .from('alertas')
      .update({ activa: !activa })
      .eq('id', id)

    cargarAlertas()
  }

  const eliminarAlerta = async (id: string) => {
    if (!confirm('Eliminar esta alerta?')) return

    await supabase
      .from('alertas')
      .delete()
      .eq('id', id)

    cargarAlertas()
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Nunca'
    return new Date(dateStr).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded mb-6"></div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="h-4 w-32 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Gestion de Alertas</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          {showForm ? 'Cancelar' : '+ Nueva Alerta'}
        </button>
      </div>

      {/* Formulario nueva alerta */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Nueva Alerta</h2>

          <form onSubmit={handleCrearAlerta} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre
              </label>
              <input
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
                placeholder="Ej: Ofertas de desarrollo"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de alerta
              </label>
              <select
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
              >
                {tiposAlerta.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {tiposAlerta.find(t => t.value === tipo)?.description}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frecuencia
              </label>
              <select
                value={frecuencia}
                onChange={(e) => setFrecuencia(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-sm"
              >
                <option value="inmediata">Inmediata</option>
                <option value="diaria">Diaria</option>
                <option value="semanal">Semanal</option>
              </select>
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Creando...' : 'Crear Alerta'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Lista de alertas */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Alertas ({alertas.length})
        </h2>

        {alertas.length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <p className="text-gray-500">No hay alertas configuradas</p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Crear primera alerta
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {alertas.map((alerta) => (
              <div
                key={alerta.id}
                className={`p-4 rounded-lg border ${
                  alerta.activa ? 'border-gray-200' : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className={`font-medium ${alerta.activa ? 'text-gray-900' : 'text-gray-500'}`}>
                        {alerta.nombre}
                      </h3>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        alerta.activa
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {alerta.activa ? 'Activa' : 'Pausada'}
                      </span>
                    </div>
                    <div className="mt-1 text-sm text-gray-500">
                      <span className="capitalize">{alerta.tipo.replace('_', ' ')}</span>
                      {' · '}
                      <span className="capitalize">{alerta.frecuencia}</span>
                      {' · '}
                      Ultima ejecucion: {formatDate(alerta.ultima_ejecucion)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleAlerta(alerta.id, alerta.activa)}
                      className={`px-3 py-1 text-xs rounded border ${
                        alerta.activa
                          ? 'border-yellow-300 text-yellow-700 hover:bg-yellow-50'
                          : 'border-green-300 text-green-700 hover:bg-green-50'
                      }`}
                    >
                      {alerta.activa ? 'Pausar' : 'Activar'}
                    </button>
                    <button
                      onClick={() => eliminarAlerta(alerta.id)}
                      className="px-3 py-1 text-xs rounded border border-red-300 text-red-700 hover:bg-red-50"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
