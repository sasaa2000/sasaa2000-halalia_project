# backend/run_tests.ps1

Write-Host "🧪 Running tests with coverage..." -ForegroundColor Cyan

pytest tests/ `
    --cov=core.configuration `
    --cov=core.logging `
    --cov=core.monitoring `
    --cov-branch `
    --no-cov-on-fail `
    --cov-report=term-missing