$ErrorActionPreference = "Stop"

uv run pyinstaller -F -n korus-checker --collect-submodules src.checkers src/launcher.py
Write-Host "Build complete: dist\\korus-checker.exe"
