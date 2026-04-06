'use client'

import { useState, useCallback, useMemo } from 'react'

export interface SelectedSkill {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  L1?: string
  L2?: string
  source: 'ocupacion' | 'busqueda' | 'texto' | 'estructurado'
  category?: 'idioma' | 'herramienta' | 'software'
  essential_for_occupation?: boolean
  market_frequency?: number
  description?: string
}

export interface SelectedOccupation {
  id: string
  label: string
  isco_code: string
}

export interface SkillCaptureState {
  nombre: string
  dni: string
  ocupaciones: SelectedOccupation[]
  skills: SelectedSkill[]
}

export function useSkillCapture(initial?: Partial<SkillCaptureState>) {
  const [nombre, setNombre] = useState(initial?.nombre || '')
  const [dni, setDni] = useState(initial?.dni || '')
  const [ocupaciones, setOcupaciones] = useState<SelectedOccupation[]>(initial?.ocupaciones || [])
  const [skills, setSkills] = useState<SelectedSkill[]>(initial?.skills || [])

  const skillUris = useMemo(() => new Set(skills.map(s => s.uri)), [skills])

  const addSkill = useCallback((skill: SelectedSkill) => {
    setSkills(prev => {
      const key = skill.uri || skill.label.toLowerCase()
      if (prev.some(s => (s.uri || s.label.toLowerCase()) === key)) return prev
      return [...prev, skill]
    })
  }, [])

  const addSkills = useCallback((newSkills: SelectedSkill[]) => {
    setSkills(prev => {
      const existing = new Set(prev.map(s => s.uri || s.label.toLowerCase()))
      const unique = newSkills.filter(s => !existing.has(s.uri || s.label.toLowerCase()))
      return unique.length > 0 ? [...prev, ...unique] : prev
    })
  }, [])

  const removeSkill = useCallback((uri: string) => {
    setSkills(prev => prev.filter(s => s.uri !== uri))
  }, [])

  const addOccupation = useCallback((occ: SelectedOccupation) => {
    setOcupaciones(prev => {
      if (prev.some(o => o.id === occ.id)) return prev
      return [...prev, occ]
    })
  }, [])

  const removeOccupation = useCallback((id: string) => {
    setOcupaciones(prev => prev.filter(o => o.id !== id))
  }, [])

  const reset = useCallback(() => {
    setNombre('')
    setDni('')
    setOcupaciones([])
    setSkills([])
  }, [])

  return {
    nombre, setNombre,
    dni, setDni,
    ocupaciones, addOccupation, removeOccupation,
    skills, skillUris, addSkill, addSkills, removeSkill,
    reset,
  }
}
