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

    throw "未找到uv。请先运行scripts/bootstrap.ps1准备环境。"
}

function Run-Step([string]$Label, [scriptblock]$Action) {
    Write-Host "`n[检查] $Label"
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Label 失败，已停止后续检查。"
    }
    Write-Host "[通过] $Label"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot "frontend"
$backendRoot = Join-Path $projectRoot "backend"
$pnpm = (Get-Command pnpm -ErrorAction Stop).Source
$uv = Find-UvExecutable

Run-Step "前端代码规范" { & $pnpm --dir $frontendRoot lint }
Run-Step "前端类型" { & $pnpm --dir $frontendRoot typecheck }
Run-Step "前端单元与组件测试" { & $pnpm --dir $frontendRoot test }
Run-Step "前端浏览器测试入口" { & $pnpm --dir $frontendRoot test:e2e }
Run-Step "前端生产构建" { & $pnpm --dir $frontendRoot build }

Push-Location $backendRoot
try {
    Run-Step "后端依赖锁" { & $uv sync --all-groups --frozen }
    Run-Step "后端代码规范" { & $uv run ruff check . }
    Run-Step "后端类型" { & $uv run mypy app tests }
    Run-Step "后端测试与覆盖率" { & $uv run pytest --cov=app --cov-report=term-missing }
}
finally {
    Pop-Location
}

Write-Host "`nPhase 0全部检查通过。OpenAPI、Mock端到端和固定评测将在对应获批阶段加入。"
