'use client'

import jsPDF from 'jspdf'
import QRCode from 'qrcode'

interface ReportPDFData {
  candidatoNombre: string
  candidatoDNI?: string
  ocupacionLabel: string
  matchScore: number
  reportUrl: string
  fecha: string
}

/**
 * Genera la carta PDF con QR para el reporte de compatibilidad.
 *
 * Contenido:
 * - Logo MOL (texto)
 * - Título institucional
 * - Fecha
 * - Texto presentación OEDE + ESCO
 * - Datos del candidato y vacante
 * - Código QR apuntando al reporte web
 * - Contacto
 */
export async function generateReportPDF(data: ReportPDFData): Promise<Blob> {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const margin = 25
  const contentWidth = pageWidth - margin * 2
  let y = margin

  // --- Logo MOL ---
  doc.setFillColor(26, 86, 142) // HEADER_BG
  doc.roundedRect(margin, y, 35, 12, 3, 3, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(14)
  doc.setFont('helvetica', 'bold')
  doc.text('MOL', margin + 5, y + 8.5)
  y += 20

  // --- Título ---
  doc.setTextColor(26, 86, 142)
  doc.setFontSize(13)
  doc.setFont('helvetica', 'bold')
  doc.text('ACCESO AL REPORTE DE COMPATIBILIDAD', margin, y)
  y += 6
  doc.text('DEL PERFIL LABORAL', margin, y)
  y += 8
  doc.setTextColor(127, 140, 141)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text('Monitor de Ofertas Laborales', margin, y)
  y += 10

  // --- Fecha ---
  doc.setTextColor(33, 37, 41)
  doc.setFontSize(10)
  doc.text(`Fecha: ${data.fecha}`, margin, y)
  y += 8

  // --- Línea separadora ---
  doc.setDrawColor(26, 86, 142)
  doc.setLineWidth(0.5)
  doc.line(margin, y, pageWidth - margin, y)
  y += 10

  // --- Texto institucional ---
  doc.setTextColor(33, 37, 41)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')

  const textoInstitucional = `El Monitor de Ofertas Laborales (MOL) es una herramienta diseñada para optimizar el encuentro entre la oferta y la demanda de trabajo. A través de la identificación de competencias laborales estandarizadas (Taxonomía ESCO), el MOL evalúa la afinidad técnica de los perfiles frente a los requerimientos de las ocupaciones.`

  const lines1 = doc.splitTextToSize(textoInstitucional, contentWidth)
  doc.text(lines1, margin, y)
  y += lines1.length * 5 + 8

  // --- Datos del candidato ---
  const textoCandidato = `De acuerdo con la información procesada, ${data.candidatoNombre}${data.candidatoDNI ? `, DNI ${data.candidatoDNI}` : ''}, presenta un perfil de competencias laborales alineado con los requerimientos definidos para la posición de ${data.ocupacionLabel}.`

  doc.setFont('helvetica', 'normal')
  const lines2 = doc.splitTextToSize(textoCandidato, contentWidth)
  doc.text(lines2, margin, y)
  y += lines2.length * 5 + 8

  // --- Compatibilidad ---
  doc.setFont('helvetica', 'bold')
  doc.text(`Compatibilidad: ${data.matchScore}%`, margin, y)
  y += 10

  // --- Texto QR ---
  doc.setFont('helvetica', 'normal')
  doc.text('Para acceder al análisis detallado de compatibilidad', margin, y)
  y += 5
  doc.text('técnica, por favor escanee el siguiente código QR:', margin, y)
  y += 12

  // --- QR Code ---
  try {
    const qrDataUrl = await QRCode.toDataURL(data.reportUrl, {
      width: 400,
      margin: 2,
      color: { dark: '#1A568E', light: '#FFFFFF' },
    })

    const qrSize = 45
    const qrX = (pageWidth - qrSize) / 2
    doc.addImage(qrDataUrl, 'PNG', qrX, y, qrSize, qrSize)
    y += qrSize + 5

    // URL debajo del QR
    doc.setTextColor(44, 125, 181)
    doc.setFontSize(8)
    const urlWidth = doc.getTextWidth(data.reportUrl)
    doc.text(data.reportUrl, (pageWidth - urlWidth) / 2, y)
    y += 15
  } catch {
    // Si falla QR, mostrar URL como texto
    doc.setTextColor(44, 125, 181)
    doc.setFontSize(10)
    doc.text(data.reportUrl, margin, y)
    y += 15
  }

  // --- Línea separadora ---
  doc.setDrawColor(26, 86, 142)
  doc.line(margin, y, pageWidth - margin, y)
  y += 8

  // --- Contacto ---
  doc.setTextColor(127, 140, 141)
  doc.setFontSize(9)
  doc.text('Consultas: contacto@oede.gob.ar', margin, y)
  doc.text('Observatorio de Empleo y Dinámica Empresarial (OEDE)', pageWidth - margin - 75, y)

  return doc.output('blob')
}

/**
 * Descarga el PDF en el navegador.
 */
export async function downloadReportPDF(data: ReportPDFData, filename?: string): Promise<void> {
  const blob = await generateReportPDF(data)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || `reporte-compatibilidad-${data.candidatoNombre.replace(/\s+/g, '-').toLowerCase()}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
