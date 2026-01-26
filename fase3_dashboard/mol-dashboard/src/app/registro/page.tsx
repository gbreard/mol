'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/browser'

interface Invitacion {
  id: string
  email: string
  rol: string
  organizacion_id: string
  organizacion?: {
    nombre: string
  }
}

function RegistroForm() {
  const [nombre, setNombre] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [invitacion, setInvitacion] = useState<Invitacion | null>(null)

  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const verificarToken = async () => {
      if (!token) {
        setError('Token de invitacion no proporcionado')
        setLoading(false)
        return
      }

      const { data, error } = await supabase
        .from('invitaciones')
        .select('id, email, rol, organizacion_id, organizacion:organizaciones(nombre)')
        .eq('token', token)
        .eq('usado', false)
        .gt('expires_at', new Date().toISOString())
        .single()

      if (error || !data) {
        setError('Invitacion invalida o expirada')
      } else {
        setInvitacion(data as unknown as Invitacion)
      }
      setLoading(false)
    }

    verificarToken()
  }, [token, supabase])

  const handleRegistro = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    // Validaciones
    if (password !== confirmPassword) {
      setError('Las passwords no coinciden')
      setSubmitting(false)
      return
    }

    if (password.length < 6) {
      setError('La password debe tener al menos 6 caracteres')
      setSubmitting(false)
      return
    }

    if (!invitacion) {
      setError('Invitacion no valida')
      setSubmitting(false)
      return
    }

    try {
      // 1. Crear usuario en Auth
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: invitacion.email,
        password,
      })

      if (authError) {
        if (authError.message.includes('already registered')) {
          setError('Este email ya tiene una cuenta. Intenta iniciar sesion.')
        } else {
          setError(authError.message)
        }
        setSubmitting(false)
        return
      }

      if (!authData.user) {
        setError('Error creando usuario')
        setSubmitting(false)
        return
      }

      // 2. Crear perfil en usuarios
      const { error: perfilError } = await supabase
        .from('usuarios')
        .insert({
          auth_id: authData.user.id,
          email: invitacion.email,
          nombre,
          rol: invitacion.rol,
          organizacion_id: invitacion.organizacion_id,
        })

      if (perfilError) {
        console.error('Error creando perfil:', perfilError)
        // Continuar de todas formas - el trigger puede haberlo creado
      }

      // 3. Marcar invitacion como usada
      await supabase
        .from('invitaciones')
        .update({
          usado: true,
          usado_at: new Date().toISOString()
        })
        .eq('id', invitacion.id)

      // 4. Redirigir al dashboard
      router.push('/')
      router.refresh()
    } catch (err) {
      setError('Error inesperado al crear cuenta')
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500">Verificando invitacion...</div>
      </div>
    )
  }

  if (error && !invitacion) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Invitacion no valida</h2>
          <p className="text-gray-500 mb-6">{error}</p>
          <a
            href="/login"
            className="inline-block py-2 px-4 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
          >
            Ir al login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-blue-600 rounded-lg mx-auto mb-4 flex items-center justify-center">
            <span className="text-white text-2xl font-bold">M</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Crear cuenta</h1>
          {invitacion?.organizacion && (
            <p className="text-gray-500 mt-2 text-sm">
              Has sido invitado a <span className="font-medium">{invitacion.organizacion.nombre}</span>
            </p>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleRegistro} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={invitacion?.email || ''}
              disabled
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo
            </label>
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="Tu nombre"
              required
              disabled={submitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="Minimo 6 caracteres"
              minLength={6}
              required
              disabled={submitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirmar password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="Repetir password"
              minLength={6}
              required
              disabled={submitting}
            />
          </div>

          <div className="py-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Rol asignado:</span>
              <span className="font-medium text-gray-900 capitalize">{invitacion?.rol}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-gray-500">
          Ya tienes cuenta?{' '}
          <a href="/login" className="text-blue-600 hover:text-blue-700">
            Iniciar sesion
          </a>
        </p>
      </div>
    </div>
  )
}

export default function RegistroPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500">Cargando...</div>
      </div>
    }>
      <RegistroForm />
    </Suspense>
  )
}
