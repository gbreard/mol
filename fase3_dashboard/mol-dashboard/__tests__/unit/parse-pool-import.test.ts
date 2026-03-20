import { describe, it, expect } from 'vitest'
import {
  sanitizeCell, parseCSV, parsePersonas, parseVacantes, parseCursos,
  MAX_ROWS, MAX_CELL_LENGTH,
} from '@/lib/parse-pool-import'

describe('Sanitización de celdas (S-25)', () => {
  it('remueve fórmulas Excel al inicio (=, +, -, @)', () => {
    expect(sanitizeCell('=CMD("malicious")')).toBe('CMD("malicious")')
    expect(sanitizeCell('+1+1')).toBe('1+1')
    expect(sanitizeCell('-1-1')).toBe('1-1')
    expect(sanitizeCell('@SUM(A1:A2)')).toBe('SUM(A1:A2)')
  })

  it('remueve HTML tags', () => {
    expect(sanitizeCell('<script>alert("xss")</script>')).toBe('alert("xss")')
    expect(sanitizeCell('Juan <b>Pérez</b>')).toBe('Juan Pérez')
  })

  it('remueve caracteres de control', () => {
    expect(sanitizeCell('Hola\x00Mundo')).toBe('HolaMundo')
    expect(sanitizeCell('Test\x07Bell')).toBe('TestBell')
  })

  it('trunca celdas largas', () => {
    const longText = 'a'.repeat(1000)
    expect(sanitizeCell(longText).length).toBe(MAX_CELL_LENGTH)
  })

  it('maneja null y undefined', () => {
    expect(sanitizeCell(null)).toBe('')
    expect(sanitizeCell(undefined)).toBe('')
  })

  it('texto normal pasa sin cambios', () => {
    expect(sanitizeCell('Juan Pérez')).toBe('Juan Pérez')
    expect(sanitizeCell('Desarrollador Python')).toBe('Desarrollador Python')
  })

  it('escapa patrones SQL', () => {
    expect(sanitizeCell("'; DROP TABLE users;--")).not.toContain("'")
    expect(sanitizeCell("'; DROP TABLE users;--")).not.toContain(";")
  })
})

describe('Parser CSV', () => {
  it('parsea CSV básico', () => {
    const csv = 'nombre,email\nJuan,juan@test.com\nMaria,maria@test.com'
    const rows = parseCSV(csv)
    expect(rows).toHaveLength(2)
    expect(rows[0].nombre).toBe('Juan')
    expect(rows[1].email).toBe('maria@test.com')
  })

  it('normaliza headers a lowercase + underscore', () => {
    const csv = 'Nombre Completo,Email Contacto\nJuan,j@t.com'
    const rows = parseCSV(csv)
    expect(rows[0]).toHaveProperty('nombre_completo')
    expect(rows[0]).toHaveProperty('email_contacto')
  })

  it('sanitiza valores', () => {
    const csv = 'nombre\n=CMD("hack")'
    const rows = parseCSV(csv)
    expect(rows[0].nombre).not.toContain('=')
  })

  it('archivo vacío retorna array vacío', () => {
    expect(parseCSV('')).toHaveLength(0)
    expect(parseCSV('nombre')).toHaveLength(0) // solo header, sin datos
  })

  it('respeta límite de filas', () => {
    let csv = 'nombre\n'
    for (let i = 0; i < MAX_ROWS + 100; i++) {
      csv += `Persona${i}\n`
    }
    const rows = parseCSV(csv)
    expect(rows.length).toBeLessThanOrEqual(MAX_ROWS)
  })
})

describe('Parser Personas', () => {
  it('parsea personas con columna nombre', () => {
    const csv = 'nombre,dni,email\nJuan Pérez,30123456,juan@test.com\nMaria López,31456789,maria@test.com'
    const result = parsePersonas(csv)
    expect(result.valid_rows).toBe(2)
    expect(result.errors).toHaveLength(0)
    expect(result.data[0].nombre).toBe('Juan Pérez')
    expect(result.data[0].dni).toBe('30123456')
  })

  it('acepta variantes de columna nombre', () => {
    const csv = 'nombre_completo,documento\nJuan Pérez,30123456'
    const result = parsePersonas(csv)
    expect(result.valid_rows).toBe(1)
  })

  it('error si falta columna nombre', () => {
    const csv = 'email,telefono\njuan@test.com,1155667788'
    const result = parsePersonas(csv)
    expect(result.errors.length).toBeGreaterThan(0)
    expect(result.errors[0]).toContain('nombre')
  })

  it('salta filas sin nombre', () => {
    const csv = 'nombre,email\nJuan,j@t.com\n,sin@nombre.com\nMaria,m@t.com'
    const result = parsePersonas(csv)
    expect(result.valid_rows).toBe(2)
    expect(result.skipped_rows).toBe(1)
  })

  it('mapea columnas alternativas (competencias → skills_declaradas)', () => {
    const csv = 'nombre,competencias\nJuan,Python y SQL'
    const result = parsePersonas(csv)
    expect(result.data[0].skills_declaradas).toBe('Python y SQL')
  })
})

describe('Parser Vacantes', () => {
  it('parsea vacantes con columna titulo', () => {
    const csv = 'titulo,empresa,ubicacion\nDesarrollador,TechCorp,CABA'
    const result = parseVacantes(csv)
    expect(result.valid_rows).toBe(1)
    expect(result.data[0].titulo).toBe('Desarrollador')
  })

  it('acepta variante puesto', () => {
    const csv = 'puesto,empresa\nAnalista,BancoCo'
    const result = parseVacantes(csv)
    expect(result.valid_rows).toBe(1)
  })

  it('error si falta columna titulo/puesto', () => {
    const csv = 'empresa,ubicacion\nTechCorp,CABA'
    const result = parseVacantes(csv)
    expect(result.errors.length).toBeGreaterThan(0)
  })
})

describe('Parser Cursos', () => {
  it('parsea cursos con columna nombre', () => {
    const csv = 'nombre,duracion,modalidad\nPython Básico,3 meses,Virtual'
    const result = parseCursos(csv)
    expect(result.valid_rows).toBe(1)
    expect(result.data[0].nombre).toBe('Python Básico')
    expect(result.data[0].modalidad).toBe('Virtual')
  })

  it('acepta variante curso', () => {
    const csv = 'curso,institucion\nSoldadura,CENOF'
    const result = parseCursos(csv)
    expect(result.valid_rows).toBe(1)
  })
})
