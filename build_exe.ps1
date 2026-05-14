param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found at .venv. Create it first and install requirements."
}

$appName = "BioFlowGBIF"
$appInfoPath = Join-Path $PSScriptRoot "app\config\app_info.py"
$logoPath = Join-Path $PSScriptRoot "bioflow_logo.png"

if (-not (Test-Path $appInfoPath)) {
    throw "App info file not found: $appInfoPath"
}

if (-not (Test-Path $logoPath)) {
    throw "Logo file not found: $logoPath"
}

$appInfoText = Get-Content -LiteralPath $appInfoPath -Raw
$appVersion = $Version

if ([string]::IsNullOrWhiteSpace($appVersion)) {
    $versionMatch = [regex]::Match(
        $appInfoText,
        'APP_VERSION\s*=\s*["''](?<version>[^"'']+)["'']'
    )

    if (-not $versionMatch.Success) {
        throw "APP_VERSION not found in app\config\app_info.py"
    }

    $appVersion = $versionMatch.Groups["version"].Value
}

$safeVersion = $appVersion -replace '[\\/:*?"<>|]', '-'
$folderName = "${appName}_v${safeVersion}"

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --add-data "bioflow_logo.png;." `
    --name $appName `
    main.py

$defaultOutputDir = Join-Path $PSScriptRoot "dist\$appName"
$versionOutputDir = Join-Path $PSScriptRoot "dist\$folderName"

if (Test-Path $versionOutputDir) {
    throw "Version output folder already exists: $versionOutputDir"
}

Move-Item -LiteralPath $defaultOutputDir -Destination $versionOutputDir

Write-Host ""
Write-Host "Build complete:"
Write-Host "  Version: $appVersion"
Write-Host "  $versionOutputDir\$appName.exe"
