# Script para consolidar documento Plan Técnico MOL v2.0

$header = Get-Content "D:\OEDE\Webscrapping\docs\PLAN_TECNICO_MOL_v2.0_COMPLETO.md" -Raw -Encoding UTF8

$seccion1 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_1.md" -Raw -Encoding UTF8
$seccion2 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_2.md" -Raw -Encoding UTF8
$seccion3 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_3.md" -Raw -Encoding UTF8
$seccion4 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_4.md" -Raw -Encoding UTF8
$seccion5 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_5.md" -Raw -Encoding UTF8
$seccion6 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_6.md" -Raw -Encoding UTF8
$seccion7 = Get-Content "D:\OEDE\Webscrapping\docs\plan_tecnico_v2_seccion_7.md" -Raw -Encoding UTF8

$documentoCompleto = $header + "`n`n" + $seccion1 + "`n`n" + $seccion2 + "`n`n" + $seccion3 + "`n`n" + $seccion4 + "`n`n" + $seccion5 + "`n`n" + $seccion6 + "`n`n" + $seccion7

$documentoCompleto | Out-File -FilePath "D:\OEDE\Webscrapping\docs\PLAN_TECNICO_MOL_v2.0_COMPLETO.md" -Encoding UTF8

Write-Host "Documento consolidado creado exitosamente: PLAN_TECNICO_MOL_v2.0_COMPLETO.md"
