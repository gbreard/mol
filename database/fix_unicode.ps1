$files = @('fix_encoding_db.py', 'create_tables_nlp_esco.py', 'populate_esco_from_rdf.py', 'populate_dictionaries.py', 'migrate_nlp_csv_to_db.py', 'match_ofertas_to_esco.py')

foreach ($file in $files) {
    $path = "D:\OEDE\Webscrapping\database\$file"
    if (Test-Path $path) {
        Write-Host "Procesando $file..."
        $content = Get-Content $path -Raw -Encoding UTF8

        # Reemplazar caracteres Unicode por ASCII
        $content = $content.Replace('✓', '[OK]')
        $content = $content.Replace('✗', '[ERROR]')
        $content = $content.Replace('⚠', '[WARNING]')
        $content = $content.Replace('📊', '[STATS]')
        $content = $content.Replace('📂', '[FILE]')
        $content = $content.Replace('🤖', '[BOT]')
        $content = $content.Replace('🎯', '[TARGET]')
        $content = $content.Replace('🔗', '[LINK]')
        $content = $content.Replace('🌎', '[WORLD]')
        $content = $content.Replace('📚', '[BOOK]')

        [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  -> Listo"
    }
}
Write-Host 'Conversion completa!'
