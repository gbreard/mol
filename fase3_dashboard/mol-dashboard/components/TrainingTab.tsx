'use client'

import { useState, useEffect } from 'react'
import TrainingByGap, { type GapGroup } from './TrainingByGap'
import TransitionPreference from './TransitionPreference'
import TransitionDemand, { type DemandOccupation } from './TransitionDemand'

interface Props {
  profileId: string
}

type Tab = 'cursos' | 'transicion_a' | 'transicion_b'

interface TrainingSuggestions {
  by_gap: GapGroup[]
  transition_demand: DemandOccupation[]
}

export default function TrainingTab({ profileId }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('cursos')
  const [data, setData] = useState<TrainingSuggestions | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/training-suggestions?profile_id=${profileId}`)
        if (res.ok) setData(await res.json())
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [profileId])

  const tabs: { key: Tab; label: string }[] = [
    { key: 'cursos', label: 'Cursos por brecha' },
    { key: 'transicion_a', label: 'Transición: elegir destino' },
    { key: 'transicion_b', label: 'Transición: por demanda' },
  ]

  return (
    <div className="space-y-4">
      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            aria-selected={activeTab === t.key}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === t.key
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Source note */}
      <p className="text-xs text-gray-400">
        Fuente: Portal de Capacitación CABA | 2,255 cursos
      </p>

      {loading && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      )}

      {!loading && (
        <>
          {activeTab === 'cursos' && (
            <TrainingByGap byGap={data?.by_gap ?? []} />
          )}
          {activeTab === 'transicion_a' && (
            <TransitionPreference profileId={profileId} />
          )}
          {activeTab === 'transicion_b' && (
            <TransitionDemand occupations={data?.transition_demand ?? []} />
          )}
        </>
      )}
    </div>
  )
}
