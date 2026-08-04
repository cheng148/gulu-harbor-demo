$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding

function Find-UvExecutable {
    $command = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $packageRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path -LiteralPath $packageRoot) {
        $packages = @(Get-ChildItem -LiteralPath $packageRoot -Directory -Filter "astral-sh.uv_*")
        foreach ($package in $packages) {
            $candidate = Join-Path $package.FullName "uv.exe"
            if (Test-Path -LiteralPath $candidate) {
                return $candidate
            }
        }
    }

    throw "未找到uv。请先按 https://docs.astral.sh/uv/getting-started/installation/ 安装，然后重新打开终端。"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot "frontend"
$backendRoot = Join-Path $projectRoot "backend"
$pnpm = (Get-Command pnpm -ErrorAction Stop).Source
$uv = Find-UvExecutable

Write-Host "[1/2] 安装前端锁定依赖"
& $pnpm --dir $frontendRoot install --frozen-lockfile
if ($LASTEXITCODE -ne 0) { throw "前端依赖安装失败。" }

Write-Host "[2/2] 安装后端锁定依赖"
Push-Location $backendRoot
try {
    & $uv sync --all-groups --frozen
    if ($LASTEXITCODE -ne 0) { throw "后端依赖安装失败。" }
}
finally {
    Pop-Location
}

Write-Host "Phase 0依赖准备完成。默认Mock模式不需要DeepSeek Key。"
