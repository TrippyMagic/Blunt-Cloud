$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
uv sync --locked --extra desktop --extra build
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$originalPath = $env:PATH
try {
    # Keep unrelated native toolchains out of PyInstaller's DLL search.
    $env:PATH = "$PWD\.venv\Scripts;$env:SystemRoot\System32;$env:SystemRoot"
    .\.venv\Scripts\pyinstaller.exe --clean --noconfirm --onedir --name BluntCloud --specpath build --add-data '../LICENSE.txt;.' desktop_launcher.py
} finally {
    $env:PATH = $originalPath
}
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& ./dist/BluntCloud/BluntCloud.exe --smoke-desktop
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --no-sync python packaging/notices.py
exit $LASTEXITCODE
