'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import OEOnboarding from '@/components/OEOnboarding'
import ImportPreview, { type ImportRow, type ImportSummary } from '@/components/ImportPreview'
import ImportResult, { type ImportStats } from '@/components/ImportResult'

type Step = 'bienvenida' | 'preview' | 'resultado'

// Mock data para demo — en producción viene de POST /api/import-pool
const MOCK_PREVIEW_ROWS: ImportRow[] = [
  { nombre: 'Juan Pérez', dni: '30123456', ocupacion: 'Albañil', skills: 'Soldadura' },
  { nombre: 'María López', dni: '31456789', ocupacion: 'Cajera', skills: null },
  { nombre: 'Pedro García', dni: '32789012', ocupacion: 'Electricista', skills: 'Electricidad' },
  { nombre: null, dni: null, ocupacion: 'Costurera', skills: 'Costura, patronaje' },
]

const MOCK_SUMMARY: ImportSummary = {
  total: 150,
  con_ocupacion: 120,
  con_skills: 45,
  sin_datos: 30,
  sin_nombre: 3,
}

const MOCK_STATS: ImportStats = {
  total_importados: 147,
  con_skills_derivadas: 89,
  con_skills_declaradas: 45,
  sin_skills: 13,
}

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('bienvenida')
  const [loading, setLoading] = useState(false)

  const handleUploadPersonas = async (_file: File) => {
    // TODO: POST /api/import-pool con el archivo
    // Por ahora usa mock data
    setStep('preview')
  }

  const handleConfirm = async () => {
    setLoading(true)
    try {
      // TODO: POST /api/import-pool/confirm
      await new Promise((r) => setTimeout(r, 800)) // simula latencia
      setStep('resultado')
    } finally {
      setLoading(false)
    }
  }

  if (step === 'preview') {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <nav className="mb-6 text-sm text-gray-500">
          <span className="text-gray-400">Importar personas</span>
          <span className="mx-2">›</span>
          <span className="font-medium text-gray-800">Preview</span>
        </nav>
        <ImportPreview
          rows={MOCK_PREVIEW_ROWS}
          summary={MOCK_SUMMARY}
          loading={loading}
          onConfirm={handleConfirm}
          onCancel={() => setStep('bienvenida')}
        />
      </div>
    )
  }

  if (step === 'resultado') {
    return (
      <ImportResult
        stats={MOCK_STATS}
        onIrPanel={() => router.push('/oficina-empleo/perfil')}
        onImportarVacantes={() => setStep('bienvenida')}
        onImportarCursos={() => setStep('bienvenida')}
      />
    )
  }

  return (
    <OEOnboarding
      nombreOE="OE Municipal Avellaneda"
      nombreUsuario="María"
      onUploadPersonas={handleUploadPersonas}
      onAtenderManual={() => router.push('/oficina-empleo/perfil')}
    />
  )
}
