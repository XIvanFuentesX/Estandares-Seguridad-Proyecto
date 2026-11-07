# Abre el .docx en Word, actualiza la tabla de contenido y los campos, guarda y exporta a PDF.
# Uso: powershell -ExecutionPolicy Bypass -File documento\actualizar_y_exportar.ps1
param(
    [string]$Docx = (Join-Path $PSScriptRoot 'Proyecto_Final_SGSI_UVCG.docx')
)
$ErrorActionPreference = 'Stop'
$pdf = [System.IO.Path]::ChangeExtension($Docx, '.pdf')
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx)
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Save()
    $doc.ExportAsFixedFormat($pdf, 17)  # 17 = wdExportFormatPDF
    try { $doc.Close([ref]0) } catch { }
    Write-Output "OK: pdf=$pdf"
}
finally {
    try { $word.Quit() } catch { }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
