$ErrorActionPreference = "Stop"

uv run pyinstaller -F -n korus-checker --collect-submodules src.checkers -m src.launcher
Write-Host "Build complete: dist\\korus-checker.exe"
