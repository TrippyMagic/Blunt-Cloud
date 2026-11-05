$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
uv sync --locked --extra desktop --extra build
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --no-sync pyinstaller --noconfirm --onedir --name BluntCloud --specpath build --add-data '../LICENSE.txt;.' desktop_launcher.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --no-sync python packaging/notices.py
exit $LASTEXITCODE
