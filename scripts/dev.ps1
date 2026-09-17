<#
.SYNOPSIS
    RAG2ATT&CK development helper - enforces .venv for all commands.
.DESCRIPTION
    All commands delegate to `uv run` so the correct .venv is always used.
    Never invoke python/pytest/pip directly outside this wrapper.
.EXAMPLE
    .\scripts\dev.ps1 test
    .\scripts\dev.ps1 test -k "test_acquisition"
    .\scripts\dev.ps1 run src\dataset.py
    .\scripts\dev.ps1 add httpx
    .\scripts\dev.ps1 sync
    .\scripts\dev.ps1 check-env
    .\scripts\dev.ps1 shell
#>

param(
    [Parameter(Position = 0, Mandatory = $true)]
    [ValidateSet("test", "run", "add", "remove", "lint", "check-env", "sync", "shell")]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

Set-StrictMode -Version Latest
# NOTE: Keep SilentlyContinue here so uv's stderr noise doesn't trigger Stop.
# We check $LASTEXITCODE manually for every external command.
$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LockFile    = Join-Path $ProjectRoot "uv.lock"

function Fail([string]$Msg) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ENVIRONMENT ERROR" -ForegroundColor Red
    Write-Host "  $Msg" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Assert-Venv {
    if (-not (Test-Path $VenvPython)) { Fail ".venv not found. Run: uv sync" }
}

Assert-Venv

switch ($Command) {

    "test" {
        Write-Host "[dev] uv run pytest $Rest" -ForegroundColor Cyan
        uv run pytest @Rest
        exit $LASTEXITCODE
    }

    "run" {
        Write-Host "[dev] uv run python $Rest" -ForegroundColor Cyan
        uv run python @Rest
        exit $LASTEXITCODE
    }

    "add" {
        Write-Host "[dev] uv add $Rest" -ForegroundColor Cyan
        uv add @Rest
        exit $LASTEXITCODE
    }

    "remove" {
        Write-Host "[dev] uv remove $Rest" -ForegroundColor Cyan
        uv remove @Rest
        exit $LASTEXITCODE
    }

    "lint" {
        Write-Host "[dev] uv run ruff check src tests" -ForegroundColor Cyan
        uv run ruff check src tests @Rest
        exit $LASTEXITCODE
    }

    "sync" {
        Write-Host "[dev] uv sync" -ForegroundColor Cyan
        uv sync
        exit $LASTEXITCODE
    }

    "shell" {
        Write-Host "[dev] Activating .venv..." -ForegroundColor Cyan
        & "$ProjectRoot\.venv\Scripts\Activate.ps1"
        Write-Host "[dev] .venv active. Run 'deactivate' to exit." -ForegroundColor Green
    }

    "check-env" {
        $anyFailed = $false

        function Show-Check([string]$Label, [bool]$Pass, [string]$Detail) {
            $pad = $Label.PadRight(32)
            if ($Pass) {
                Write-Host "  $pad OK   $Detail" -ForegroundColor Green
            } else {
                Write-Host "  $pad FAIL $Detail" -ForegroundColor Red
                $script:anyFailed = $true
            }
        }

        # Helper: run a uv command, suppress stderr, return stdout last line
        function Uv-Out([string[]]$Cmd) {
            $result = & uv @Cmd 2>$null
            return $result | Select-Object -Last 1
        }

        Write-Host ""
        Write-Host "=== RAG2ATT&CK Environment Check ===" -ForegroundColor Cyan
        Write-Host ""

        # 1. Python executable must come from .venv
        $py = Uv-Out @("run","python","-c","import sys; print(sys.executable)")
        $ok = ($LASTEXITCODE -eq 0) -and ($py -like "*\.venv\*")
        Show-Check "Python executable" $ok $py

        # 2. Python version
        $pver = Uv-Out @("run","python","-c","import sys; print(sys.version.split()[0])")
        Show-Check "Python version" ($LASTEXITCODE -eq 0) $pver

        # 3. .venv exists on disk
        $ok = Test-Path $VenvPython
        Show-Check ".venv exists" $ok $(if ($ok){"yes"}else{"MISSING: $VenvPython"})

        # 4. uv.lock exists on disk
        $ok = Test-Path $LockFile
        Show-Check "uv.lock exists" $ok $(if ($ok){"yes"}else{"MISSING: $LockFile"})

        # 5. uv sync state - lockfile vs venv drift
        & uv sync --check 2>$null | Out-Null
        $ok = ($LASTEXITCODE -eq 0)
        Show-Check "uv sync state" $ok $(if ($ok){"in sync with uv.lock"}else{"DRIFT - run: uv sync"})

        # 6. google-antigravity pinned to exactly 0.1.17
        $gav = Uv-Out @("run","python","-c","from importlib.metadata import version; v=version('google-antigravity'); assert v=='0.1.17', f'expected 0.1.17, got {v}'; print(v)")
        $ok = ($LASTEXITCODE -eq 0)
        Show-Check "google-antigravity version" $ok $(if ($ok){$gav}else{"MISMATCH - $gav"})

        # 7. google.antigravity importable
        & uv run python -c "import google.antigravity" 2>$null | Out-Null
        $ok = ($LASTEXITCODE -eq 0)
        Show-Check "google.antigravity import" $ok $(if ($ok){"importable"}else{"ImportError"})

        # 8. pytest version
        $ptver = Uv-Out @("run","python","-c","from importlib.metadata import version; print(version('pytest'))")
        Show-Check "pytest version" ($LASTEXITCODE -eq 0) $ptver

        # 9. Dependency consistency scoped to .venv via uv pip check
        & uv pip check 2>$null | Out-Null
        $ok = ($LASTEXITCODE -eq 0)
        Show-Check "dependency consistency" $ok $(if ($ok){"no conflicts"}else{"CONFLICTS - run: uv pip check"})

        Write-Host ""
        if ($anyFailed) {
            Write-Host "[FAIL] One or more checks failed." -ForegroundColor Red
            exit 1
        } else {
            Write-Host "[OK] Environment is healthy." -ForegroundColor Green
            exit 0
        }
    }
}
