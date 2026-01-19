# Script para convertir Markdown a Word (.docx)
# Utiliza Microsoft Word COM object

$mdFile = "D:\OEDE\Webscrapping\docs\PLAN_TECNICO_MOL_v2.0_COMPLETO.md"
$docxFile = "D:\OEDE\Webscrapping\docs\PLAN_TECNICO_MOL_v2.0_COMPLETO.docx"

Write-Host "Iniciando conversión de Markdown a Word..."

try {
    # Crear objeto Word
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false

    # Abrir el archivo markdown como texto
    $doc = $word.Documents.Add()

    # Leer contenido markdown
    $content = Get-Content $mdFile -Raw -Encoding UTF8

    # Insertar contenido
    $doc.Content.Text = $content

    # Aplicar formato básico
    $doc.Content.Font.Name = "Calibri"
    $doc.Content.Font.Size = 11

    # Procesar encabezados (líneas que empiezan con #)
    $paragraphs = $doc.Paragraphs
    foreach ($para in $paragraphs) {
        $text = $para.Range.Text.Trim()

        # Título principal (# )
        if ($text -match '^# [^#]') {
            $para.Range.Font.Size = 24
            $para.Range.Font.Bold = $true
            $para.Range.Font.Color = 0x0000FF  # Azul
            $para.SpaceBefore = 12
            $para.SpaceAfter = 6
        }
        # Subtítulo nivel 2 (## )
        elseif ($text -match '^## ') {
            $para.Range.Font.Size = 18
            $para.Range.Font.Bold = $true
            $para.Range.Font.Color = 0x000080  # Azul oscuro
            $para.SpaceBefore = 10
            $para.SpaceAfter = 6
        }
        # Subtítulo nivel 3 (### )
        elseif ($text -match '^### ') {
            $para.Range.Font.Size = 14
            $para.Range.Font.Bold = $true
            $para.SpaceBefore = 8
            $para.SpaceAfter = 4
        }
        # Bloques de código (```)
        elseif ($text -match '^```') {
            $para.Range.Font.Name = "Courier New"
            $para.Range.Font.Size = 9
            $para.Range.Shading.BackgroundPatternColor = 0xF0F0F0  # Gris claro
        }
        # Negrita (**texto**)
        if ($text -match '\*\*') {
            $para.Range.Font.Bold = $true
        }
    }

    # Guardar como .docx
    $doc.SaveAs([ref]$docxFile, [ref]16)  # 16 = wdFormatXMLDocument (.docx)
    $doc.Close()
    $word.Quit()

    # Liberar objetos COM
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($doc) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    Write-Host "Conversión exitosa!" -ForegroundColor Green
    Write-Host "Archivo generado: $docxFile"

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red

    # Intentar cerrar Word si quedó abierto
    if ($word) {
        $word.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}
