'use client'

import { useState, useEffect, useCallback } from 'react'
import type { SkillItem } from '@/components/SkillWithDefinition'

export type S1Proposito =
  | 'busco_trabajo'
  | 'cambiar_rubro'
  | 'saber_que_vale'
  | 'desde_oe'

export interface S1Store {
  nombre: string
  proposito: S1Proposito | null
  skills: SkillItem[]
  destino_uri: string | null
  destino_label: string | null
}

const KEY = 's1_perfil'

const DEFAULT: S1Store = {
  nombre: '',
  proposito: null,
  skills: [],
  destino_uri: null,
  destino_label: null,
}

function load(): S1Store {
  if (typeof window === 'undefined') return DEFAULT
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? { ...DEFAULT, ...JSON.parse(raw) } : DEFAULT
  } catch {
    return DEFAULT
  }
}

function save(store: S1Store) {
  if (typeof window === 'undefined') return
  sessionStorage.setItem(KEY, JSON.stringify(store))
}

export function useS1Store() {
  const [store, setStoreState] = useState<S1Store>(DEFAULT)

  useEffect(() => {
    setStoreState(load())
  }, [])

  const setStore = useCallback((partial: Partial<S1Store>) => {
    setStoreState((prev) => {
      const next = { ...prev, ...partial }
      save(next)
      return next
    })
  }, [])

  const addSkills = useCallback((incoming: SkillItem[]) => {
    setStoreState((prev) => {
      const uris = new Set(prev.skills.map((s) => s.uri))
      const nuevas = incoming.filter((s) => !uris.has(s.uri))
      const next = { ...prev, skills: [...prev.skills, ...nuevas] }
      save(next)
      return next
    })
  }, [])

  const updateSkill = useCallback((uri: string, patch: Partial<SkillItem>) => {
    setStoreState((prev) => {
      const next = {
        ...prev,
        skills: prev.skills.map((s) => (s.uri === uri ? { ...s, ...patch } : s)),
      }
      save(next)
      return next
    })
  }, [])

  const removeSkill = useCallback((uri: string) => {
    setStoreState((prev) => {
      const next = { ...prev, skills: prev.skills.filter((s) => s.uri !== uri) }
      save(next)
      return next
    })
  }, [])

  const reset = useCallback(() => {
    if (typeof window !== 'undefined') sessionStorage.removeItem(KEY)
    setStoreState(DEFAULT)
  }, [])

  const confirmed = store.skills.filter((s) => s.confidence === 'confirmed')

  return { store, setStore, addSkills, updateSkill, removeSkill, reset, confirmed }
}
