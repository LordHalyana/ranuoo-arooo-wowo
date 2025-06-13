# Sprint 1 Automation Script for LocalAI CLI
# This script automates dependency installation, testing, and manual smoke test.

# Step 1: Install dependencies
if (Test-Path "pyproject.toml") {
    if (Get-Command poetry -ErrorAction SilentlyContinue) {
        Write-Host "Installing dependencies with Poetry..."
        poetry install
    }
    else {
        Write-Host "Poetry not found. Please install Poetry or use pip."
        exit 1
    }
}
elseif (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies with pip..."
    pip install -r requirements.txt
}
else {
    Write-Host "No dependency file found."
    exit 1
}

# Step 2: Run unit tests
Write-Host "Running pytest..."
pytest -q

# Step 3: Manual smoke test
Write-Host "Running manual smoke test..."
$svcName = "demo-svc"
python main.py init $svcName
python main.py run $svcName --watch &
Start-Sleep -Seconds 5

# Simulate editing app.js to trigger auto-restart
$appJsPath = "workspace/$svcName/src/app.js"
if (Test-Path $appJsPath) {
    Add-Content $appJsPath "`n// Smoke test edit: $(Get-Date)"
    Write-Host "Edited $appJsPath to trigger auto-restart."
}
else {
    Write-Host "$appJsPath not found."
}

Write-Host "Please check the output above to confirm auto-restart occurred."
Write-Host "Automation complete."
