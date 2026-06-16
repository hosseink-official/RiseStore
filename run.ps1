$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

Write-Host "Starting RiseStore Desktop app..."

$venvPython = Join-Path $rootDir "desktop\venv\Scripts\python.exe"
$requirements = Join-Path $rootDir "desktop\requirements.txt"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv "desktop\venv"
    Write-Host "Installing dependencies..."
    & "desktop\venv\Scripts\pip" install -r $requirements
}

& $venvPython "desktop\main.py"

if ($LASTEXITCODE -ne 0) {
    Read-Host "Press Enter to exit"
}
