param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot "frontend"
$schemaPath = Join-Path $projectRoot "backend\openapi.json"
$outputPath = Join-Path $frontendRoot "src\lib\api\generated.ts"
$generator = Join-Path $frontendRoot "node_modules\.bin\openapi-typescript.cmd"

if (-not (Test-Path -LiteralPath $schemaPath)) {
    throw "OpenAPI snapshot is missing. Run scripts/export-openapi.ps1 first."
}

if (-not (Test-Path -LiteralPath $generator)) {
    throw "OpenAPI type generator is missing. Run pnpm install in frontend first."
}

New-Item -ItemType Directory -Path (Split-Path -Parent $outputPath) -Force | Out-Null
$arguments = @($schemaPath, "--output", $outputPath, "--immutable")
if ($Check) {
    $arguments += "--check"
}

& $generator @arguments
if ($LASTEXITCODE -ne 0) {
    if ($Check) {
        throw "Generated frontend API types are stale. Regenerate them before continuing."
    }
    throw "Frontend API type generation failed."
}

if ($Check) {
    Write-Host "Generated API types are up to date."
}
else {
    Write-Host "Generated $outputPath"
}
