'use client'

import { useState, useEffect } from 'react'
import { Scale, BarChart3, Target, Loader2 } from 'lucide-react'
import dynamic from 'next/dynamic'

// Lazy load heavy components (occupation_full_detail.json = 45MB)
const OccupationDetail = dynamic(() => import('@/components/OccupationDetail'), { loading: () => <LoadingPlaceholder /> })
const OccupationCompare = dynamic(() => import('@/components/OccupationCompare'), { loading: () => <LoadingPlaceholder /> })

function LoadingPlaceholder() {
  return (
    <div className="flex items-center justify-center py-12 gap-2 text-gray-400">
      <Loader2 className="w-5 h-5 animate-spin" />
      <span className="text-sm">Cargando...</span>
    </div>
  )
}

type Tab = 'ocupaciones' | 'comparar'

export default function VipPoliticasPage() {
  const [activeTab, setActiveTab] = useState<Tab>('ocupaciones')
  const [occupationsData, setOccupationsData] = useState<any>(null)
  const [occupationsList, setOccupationsList] = useState<any[]>([])
  const [loadingData, setLoadingData] = useState(false)

  // Load occupation data lazily when skills section is first shown
  useEffect(() => {
    if (occupationsData) return
    setLoadingData(true)

    Promise.all([
      fetch('/data/occupation_full_detail.json').then(r => r.json()),
      fetch('/data/esco_occupations_metadata.json').then(r => r.json()),
    ]).then(([fullDetail, metadata]) => {
      setOccupationsData(fullDetail)
      setOccupationsList(
        (metadata || []).map((m: any) => ({
          id: m.uri?.split('/').pop() || '',
          uri: m.uri,
          label: m.label,
          isco_code: m.isco_code,
        }))
      )
    }).catch(() => {}).finally(() => setLoadingData(false))
  }, [occupationsData])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Scale className="w-5 h-5 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Políticas Laborales</h1>
          </div>
          <p className="text-sm text-gray-500">
            Inteligencia de mercado y análisis de ocupaciones para fundamentar políticas basadas en datos
          </p>
        </div>

        {/* Skills Intelligence */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="border-b px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-semibold text-gray-800">Skills Intelligence</h2>
            </div>
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
              <button
                onClick={() => setActiveTab('ocupaciones')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'ocupaciones' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Ocupaciones
              </button>
              <button
                onClick={() => setActiveTab('comparar')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'comparar' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Comparar
              </button>
            </div>
          </div>

          <div className="p-4 text-[13px]">
            {loadingData ? (
              <LoadingPlaceholder />
            ) : (
              <>
                {activeTab === 'ocupaciones' && occupationsData && (
                  <OccupationDetail
                    occupationsData={occupationsData}
                    occupationsList={occupationsList}
                  />
                )}
                {activeTab === 'comparar' && occupationsData && (
                  <OccupationCompare
                    occupationsData={occupationsData}
                    occupationsList={occupationsList}
                  />
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
