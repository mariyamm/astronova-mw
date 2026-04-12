# preview_pdf.ps1
# Fast PDF preview — edit pdf_tasks.py, then run this script. No restart needed.
# Usage:  .\preview_pdf.ps1           (uses analysis id 74)
#         .\preview_pdf.ps1 -Id 99    (any analysis id)

param([int]$Id = 74)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Rendering PDF for analysis $Id..." -ForegroundColor Cyan

docker exec astronova_celery python /app/preview_render.py $Id

if ($LASTEXITCODE -ne 0) {
    Write-Host "Render failed — check output above." -ForegroundColor Red
    exit 1
}

$dest = Join-Path $scriptDir "preview.pdf"
docker cp astronova_celery:/app/pdf_output/preview.pdf $dest

Write-Host "Done -> $dest" -ForegroundColor Green
Start-Process $dest
