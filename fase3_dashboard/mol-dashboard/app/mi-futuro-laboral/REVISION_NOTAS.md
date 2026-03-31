# S1 Notas de revisión — 2026-03-25

Ver plan completo en: /docs/plan/S1_REVISION_2026-03-25.md

## TO-DO en orden de ejecución

- [ ] 1. S1-3: fix por ocupación (mock funcional si API no responde)
- [ ] 2. S1-3: botón "+" explícito por skill en dropdown
- [ ] 3. S1-3: tipos de skill en acumulador (competencia / conocimiento / herramienta / idioma)
- [ ] 4. S1-3: entrada dedicada para idiomas
- [ ] 5. S1-3: texto libre y formación con mock funcional
- [ ] 6. S1-1: sacar botón "Soy técnico de OE"
- [ ] 7. S1-1: agregar "Ya cargué mis competencias → Ver mi perfil"
- [ ] 8. S1-4/5: nueva pantalla /perfil/review con freemium gate
- [ ] 9. S1-6: tab inicial según propósito + elegir destino embedded
- [ ] 10. S1-8: leer destino del store
- [ ] 11. S1-2: propósito → comportamiento diferenciado
- [ ] 12. Dashboard /mi-futuro-laboral/dashboard (post-MVP)

## Cambios al store (use-s1-store.ts)
- Agregar `destino: { uri, label, match } | null`
- Agregar `idiomas: { label, nivel }[]`

## Cambios al tipo SkillItem (SkillWithDefinition.tsx)
- Agregar `tipo?: 'competencia' | 'conocimiento' | 'herramienta' | 'idioma'`
