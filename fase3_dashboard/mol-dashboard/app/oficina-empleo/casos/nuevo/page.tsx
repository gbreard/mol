'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, ArrowRight, User, QrCode } from 'lucide-react'

export default function NuevoCasoPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    nombre: '', apellido: '', dni: '', telefono: '', email: '',
    provincia: 'CABA', barrio: '', edad: '',
  })
  const [error, setError] = useState('')

  const set = (key: string, val: string) => {
    setForm((f) => ({ ...f, [key]: val }))
    setError('')
  }

  const handleContinuar = () => {
    if (!form.nombre.trim() || !form.apellido.trim()) {
      setError('Completá nombre y apellido.')
      return
    }
    if (!form.dni.trim()) {
      setError('Ingresá el DNI.')
      return
    }
    // En producción: POST /api/casos → { persona_id, caso_id }
    // Mock: redirige al perfil S1 con nombre pre-cargado
    router.push(`/mi-futuro-laboral/perfil`)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-8">

        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Volver
        </button>

        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900">Nuevo caso</h1>
          <p className="text-gray-500 text-sm mt-1">
            Cargá los datos de la persona. Después completarán el perfil de competencias juntos.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">

          {/* Nombre */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Nombre *</label>
              <input
                type="text"
                value={form.nombre}
                onChange={(e) => set('nombre', e.target.value)}
                placeholder="María"
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Apellido *</label>
              <input
                type="text"
                value={form.apellido}
                onChange={(e) => set('apellido', e.target.value)}
                placeholder="González"
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />
            </div>
          </div>

          {/* DNI + Edad */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">DNI *</label>
              <input
                type="text"
                value={form.dni}
                onChange={(e) => set('dni', e.target.value)}
                placeholder="28.450.123"
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Edad</label>
              <input
                type="number"
                value={form.edad}
                onChange={(e) => set('edad', e.target.value)}
                placeholder="34"
                min={16} max={100}
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />
            </div>
          </div>

          {/* Contacto */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">Teléfono</label>
            <input
              type="tel"
              value={form.telefono}
              onChange={(e) => set('telefono', e.target.value)}
              placeholder="+54 11 4523-9876"
              className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
              placeholder="mgonzalez@email.com"
              className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
            />
          </div>

          {/* Ubicación */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Provincia</label>
              <select
                value={form.provincia}
                onChange={(e) => set('provincia', e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
              >
                <option>CABA</option>
                <option>Buenos Aires</option>
                <option>Córdoba</option>
                <option>Santa Fe</option>
                <option>Mendoza</option>
                <option>Otra</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Barrio / Localidad</label>
              <input
                type="text"
                value={form.barrio}
                onChange={(e) => set('barrio', e.target.value)}
                placeholder="Flores"
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />
            </div>
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}

          <button
            onClick={handleContinuar}
            className="w-full inline-flex items-center justify-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-3 rounded-xl hover:bg-teal-700 transition-colors"
          >
            Continuar al perfil de competencias
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Opción QR */}
        <div className="mt-4 flex items-start gap-3 bg-teal-50 border border-teal-200 rounded-xl p-4">
          <QrCode className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-teal-800">¿La persona tiene un teléfono?</p>
            <p className="text-xs text-teal-700 mt-0.5">
              Podés enviarle el link de Mi Futuro Laboral para que complete su perfil desde el teléfono.
              El técnico ve los resultados automáticamente.
            </p>
            <button className="mt-2 text-xs text-teal-600 font-medium hover:underline">
              Enviar link →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
