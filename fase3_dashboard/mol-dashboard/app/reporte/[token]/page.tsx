import { notFound } from 'next/navigation'
import CompatibilityReport, { type ReportData } from '@/components/CompatibilityReport'

interface Props {
  params: Promise<{ token: string }>
}

async function fetchReport(token: string): Promise<ReportData | null> {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
      ? process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : 'http://localhost:3000'
      : 'http://localhost:3000'

    const res = await fetch(`${baseUrl}/api/compatibility-report?token=${token}`, {
      cache: 'no-store',
    })
    if (res.status === 404) return null
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export default async function ReportePage({ params }: Props) {
  const { token } = await params
  const data = await fetchReport(token)

  if (!data) notFound()

  if (data.estado === 'expirado') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm">
          <div className="mb-4 text-4xl">⏱</div>
          <h1 className="mb-2 text-xl font-semibold text-gray-800">Reporte expirado</h1>
          <p className="text-gray-500">
            Este reporte ha expirado. Contacte al candidato para solicitar uno actualizado.
          </p>
        </div>
      </div>
    )
  }

  if (data.estado === 'revocado') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
        <div className="max-w-md rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm">
          <div className="mb-4 text-4xl">🚫</div>
          <h1 className="mb-2 text-xl font-semibold text-gray-800">Reporte no disponible</h1>
          <p className="text-gray-500">Este reporte ya no está disponible.</p>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <CompatibilityReport data={data} />
    </main>
  )
}
