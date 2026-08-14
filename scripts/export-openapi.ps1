$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "backend"
$outputPath = Join-Path $backendRoot "openapi.json"
$env:GULU_OPENAPI_OUTPUT = $outputPath
$pythonExecutable = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Backend Python environment not found. Run scripts/bootstrap.ps1 first."
}

$python = @'
import json
import os
from pathlib import Path

from app.core.config import AppSettings, ModelProvider
from app.main import create_app

app = create_app(settings=AppSettings(modelProvider=ModelProvider.MOCK))
output = json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
Path(os.environ["GULU_OPENAPI_OUTPUT"]).write_text(output, encoding="utf-8")
'@

Push-Location $backendRoot
try {
    $python | & $pythonExecutable -
    if ($LASTEXITCODE -ne 0) {
        throw "OpenAPI export failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Generated $outputPath"
