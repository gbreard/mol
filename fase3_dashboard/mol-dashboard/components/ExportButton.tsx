"use client";

import { useState } from "react";
import { Download, FileSpreadsheet, FileText, ChevronDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface ExportColumn {
  key: string;
  header: string;
  format?: (value: any) => string;
}

export interface FormattedExcelOptions {
  title: string;
  subtitle: string;
  source?: string;
  data: { name: string; value: number; porcentaje?: number }[];
  columns: { header: string; key: string }[];
  filename: string;
  showPercentage?: boolean;
}

// Función para exportar Excel formateado con título, subtítulo y fuente
export async function downloadFormattedExcel(options: FormattedExcelOptions) {
  const { title, subtitle, source = "MOL, en base a portales de intermediación laboral", data, columns, filename, showPercentage = true } = options;

  if (!data || data.length === 0) {
    alert('No hay datos para exportar');
    return;
  }

  try {
    const XLSX = await import('xlsx');

    // Calcular total para porcentajes si no vienen calculados
    const total = data.reduce((sum, item) => sum + item.value, 0);

    // Preparar filas con datos
    const dataRows = data.map(item => {
      const row: Record<string, any> = {};
      columns.forEach(col => {
        if (col.key === 'name') {
          row[col.header] = item.name;
        } else if (col.key === 'value') {
          row[col.header] = item.value;
        } else if (col.key === 'porcentaje' && showPercentage) {
          row[col.header] = item.porcentaje ?? (total > 0 ? Math.round((item.value / total) * 100 * 10) / 10 : 0);
        }
      });
      return row;
    });

    // Crear worksheet vacío
    const ws = XLSX.utils.aoa_to_sheet([]);

    // Fila 1: Título (negrita, fusionado)
    XLSX.utils.sheet_add_aoa(ws, [[title]], { origin: 'A1' });

    // Fila 2: Subtítulo (filtros)
    XLSX.utils.sheet_add_aoa(ws, [[subtitle]], { origin: 'A2' });

    // Fila 3: vacía
    XLSX.utils.sheet_add_aoa(ws, [['']], { origin: 'A3' });

    // Fila 4+: Datos con headers
    const headers = columns.map(c => c.header);
    XLSX.utils.sheet_add_aoa(ws, [headers], { origin: 'A4' });

    // Agregar datos desde fila 5
    dataRows.forEach((row, idx) => {
      const rowData = headers.map(h => row[h] ?? '');
      XLSX.utils.sheet_add_aoa(ws, [rowData], { origin: `A${5 + idx}` });
    });

    // Última fila: Fuente
    const lastDataRow = 5 + dataRows.length;
    XLSX.utils.sheet_add_aoa(ws, [['']], { origin: `A${lastDataRow}` });
    XLSX.utils.sheet_add_aoa(ws, [[`Fuente: ${source}`]], { origin: `A${lastDataRow + 1}` });

    // Ajustar ancho de columnas
    const colWidths = columns.map(col => ({
      wch: Math.max(
        col.header.length + 2,
        ...data.map(row => String(row.name || row.value || '').length + 2).slice(0, 50),
        20
      )
    }));
    ws['!cols'] = colWidths;

    // Fusionar celdas para título y subtítulo
    const numCols = columns.length;
    ws['!merges'] = [
      { s: { r: 0, c: 0 }, e: { r: 0, c: numCols - 1 } }, // Título
      { s: { r: 1, c: 0 }, e: { r: 1, c: numCols - 1 } }, // Subtítulo
      { s: { r: lastDataRow, c: 0 }, e: { r: lastDataRow, c: numCols - 1 } }, // Fuente
    ];

    // Crear workbook y agregar worksheet
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Datos');

    // Descargar
    XLSX.writeFile(wb, `${filename}_${new Date().toISOString().split('T')[0]}.xlsx`);
  } catch (e) {
    console.error('Error al exportar Excel:', e);
    alert('Error al exportar. Intente nuevamente.');
  }
}

interface ExportButtonProps {
  data: any[];
  columns: ExportColumn[];
  filename: string;
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg";
  showLabel?: boolean;
}

// Función para escapar valores CSV
function escapeCSV(value: any): string {
  if (value === null || value === undefined) return '';
  const str = String(value);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

// Función para descargar CSV
function downloadCSV(data: any[], columns: ExportColumn[], filename: string) {
  const headers = columns.map(c => c.header);
  const rows = data.map(row =>
    columns.map(col => {
      const value = row[col.key];
      const formatted = col.format ? col.format(value) : value;
      return escapeCSV(formatted);
    }).join(',')
  );

  const csvContent = [headers.join(','), ...rows].join('\n');
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Función para descargar Excel (usando xlsx si está disponible, sino CSV)
async function downloadExcel(data: any[], columns: ExportColumn[], filename: string) {
  try {
    // Intentar usar xlsx si está instalado
    const XLSX = await import('xlsx');

    // Preparar datos para Excel
    const headers = columns.map(c => c.header);
    const rows = data.map(row =>
      columns.reduce((acc, col) => {
        const value = row[col.key];
        acc[col.header] = col.format ? col.format(value) : value;
        return acc;
      }, {} as Record<string, any>)
    );

    // Crear worksheet y workbook
    const ws = XLSX.utils.json_to_sheet(rows, { header: headers });
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Datos');

    // Ajustar ancho de columnas
    const colWidths = columns.map(col => ({
      wch: Math.max(
        col.header.length,
        ...data.map(row => String(row[col.key] ?? '').length).slice(0, 100)
      ) + 2
    }));
    ws['!cols'] = colWidths;

    // Descargar
    XLSX.writeFile(wb, `${filename}_${new Date().toISOString().split('T')[0]}.xlsx`);
  } catch (e) {
    // Si xlsx no está disponible, usar CSV como fallback
    console.warn('xlsx no disponible, usando CSV como fallback');
    downloadCSV(data, columns, filename);
  }
}

export function ExportButton({
  data,
  columns,
  filename,
  variant = "outline",
  size = "sm",
  showLabel = true,
}: ExportButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleExport = async (format: 'csv' | 'excel') => {
    if (!data || data.length === 0) {
      alert('No hay datos para exportar');
      return;
    }

    setLoading(true);
    try {
      if (format === 'csv') {
        downloadCSV(data, columns, filename);
      } else {
        await downloadExcel(data, columns, filename);
      }
    } catch (error) {
      console.error('Error al exportar:', error);
      alert('Error al exportar los datos');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Button variant={variant} size={size} disabled className="gap-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        {showLabel && <span>Exportando...</span>}
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          className="gap-2 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-all"
        >
          <Download className="w-4 h-4" />
          {showLabel && <span className="font-medium">Exportar</span>}
          <ChevronDown className="w-3 h-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleExport('csv')} className="gap-2 cursor-pointer">
          <FileText className="w-4 h-4 text-green-600" />
          <span>Descargar CSV</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport('excel')} className="gap-2 cursor-pointer">
          <FileSpreadsheet className="w-4 h-4 text-blue-600" />
          <span>Descargar Excel</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Componente simple para export rápido (solo CSV, sin dropdown)
export function QuickExportButton({
  data,
  columns,
  filename,
  label = "CSV",
}: {
  data: any[];
  columns: ExportColumn[];
  filename: string;
  label?: string;
}) {
  const handleDownload = () => {
    if (!data || data.length === 0) {
      alert('No hay datos para exportar');
      return;
    }
    downloadCSV(data, columns, filename);
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleDownload}
      className="gap-2 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300 transition-all"
    >
      <Download className="w-4 h-4" />
      <span className="font-medium">{label}</span>
    </Button>
  );
}
