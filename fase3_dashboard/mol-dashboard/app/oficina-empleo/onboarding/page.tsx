'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import OEOnboarding from '@/components/OEOnboarding'
import ImportPreview, { type ImportRow, type ImportSummary } from '@/components/ImportPreview'
import ImportResult, { type ImportStats } from '@/components/ImportResult'

type Step = 'bienvenida' | 'preview' | 'resultado'

interface PreviewData {
  rows: ImportRow[]
  summary: ImportSummary
}

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('bienvenida')
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<PreviewData | null>(null)
  const [stats, setStats] = useState<ImportStats | null>(null)

  const handleUploadPersonas = async (file: File) => {
    setLoading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/import-pool', { method: 'POST', body: form })
      if (res.ok) {
        const data = await res.json()
        setPreview({ rows: data.rows, summary: data.summary })
        setStep('preview')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/import-pool/confirm', { method: 'POST' })
      if (res.ok) {
        setStats(await res.json())
        setStep('resultado')
      }
    } finally {
      setLoading(false)
    }
  }

  if (step === 'preview' && preview) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <nav className="mb-6 text-sm text-gray-500">
          <span className="text-gray-400">Importar personas</span>
          <span className="mx-2">›</span>
          <span className="font-medium text-gray-800">Preview</span>
        </nav>
        <ImportPreview
          rows={preview.rows}
          summary={preview.summary}
          loading={loading}
          onConfirm={handleConfirm}
          onCancel={() => setStep('bienvenida')}
        />
      </div>
    )
  }

  if (step === 'resultado' && stats) {
    return (
      <ImportResult
        stats={stats}
        onIrPanel={() => router.push('/oficina-empleo/perfil')}
        onImportarVacantes={() => setStep('bienvenida')}
        onImportarCursos={() => setStep('bienvenida')}
      />
    )
  }

  return (
    <OEOnboarding
      nombreOE="OE Municipal"
      onUploadPersonas={handleUploadPersonas}
      onAtenderManual={() => router.push('/oficina-empleo/perfil')}
    />
  )
}
