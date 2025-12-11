param(
    [switch]$Portable,
    [switch]$Clean,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Read-Version {
    param([string]$PythonBin = "python")
    & $PythonBin -c "import tomllib, pathlib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_text('utf-8'))['project']['version'])"
}

function Invoke-Sign {
    param(
        [string]$FilePath,
        [string]$Signtool,
        [string]$CertPath,
        [string]$CertPass
    )

    if (-not (Test-Path $FilePath)) {
        Write-Warning "Signing skipped, file not found: $FilePath"
        return
    }

    & $Signtool sign /f $CertPath /p $CertPass /tr http://timestamp.digicert.com /td sha256 /fd sha256 $FilePath
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $repoRoot

$python = $Env:PYTHON
if (-not $python) { $python = "python" }

$distRoot = Join-Path $repoRoot "dist\pyinstaller"
$buildRoot = Join-Path $repoRoot "build\pyinstaller"

$argsList = @("--distpath", $distRoot, "--workpath", $buildRoot)
if ($Clean) { $argsList += "--clean" }
if ($Portable) { $argsList += "--portable" }

if (-not $SkipBuild) {
    Write-Host "==> Running PyInstaller..."
    & $python "contrib\packaging\build_pyinstaller.py" @argsList
} else {
    Write-Host "==> Skipping PyInstaller build (SkipBuild set)"
}

$version = Read-Version -PythonBin $python
$platformDist = Join-Path $distRoot "windows"
$stageDir = Get-ChildItem -Path $platformDist -Directory | Select-Object -First 1
if (-not $stageDir) {
    throw "PyInstaller output not found in $platformDist"
}

$nsisScript = Join-Path $repoRoot "contrib\packaging\windows\tagstudio.nsi"
$installerOutDir = Join-Path $repoRoot "dist"
if (-not (Test-Path $installerOutDir)) { New-Item -ItemType Directory -Force -Path $installerOutDir | Out-Null }
$installerName = Join-Path $installerOutDir "TagStudio-$version-win-setup.exe"

Write-Host "==> Building NSIS installer..."
$makensis = Get-Command "makensis.exe" -ErrorAction SilentlyContinue
if (-not $makensis) {
    throw "makensis.exe not found on PATH. Install NSIS and ensure makensis.exe is available."
}
& $makensis.Source "/DVERSION=$version" "/DBUILD_DIR=$($stageDir.FullName)" "/DOUTPUT_DIR=$installerOutDir" "/DINSTALLER_NAME=$installerName" $nsisScript

$signtool = $Env:TS_SIGNTOOL
$certPath = $Env:TS_CERT_PATH
$certPass = $Env:TS_CERT_PASS

if ($signtool -and $certPath -and $certPass -and (Get-Command $signtool -ErrorAction SilentlyContinue)) {
    $stageExe = Join-Path $stageDir.FullName "TagStudio.exe"
    Write-Host "==> Code signing (stage)..."
    Invoke-Sign -FilePath $stageExe -Signtool $signtool -CertPath $certPath -CertPass $certPass

    Write-Host "==> Code signing (installer)..."
    Invoke-Sign -FilePath $installerName -Signtool $signtool -CertPath $certPath -CertPass $certPass
} else {
    Write-Host "==> Skipping code signing (TS_SIGNTOOL/TS_CERT_PATH/TS_CERT_PASS not set or signtool missing)"
}

Write-Host "Done. Installer at $installerName"
