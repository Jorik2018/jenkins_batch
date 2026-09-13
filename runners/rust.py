from pathlib import Path

def create_runner(
    destination: Path,
    executable: str,
    port: int,
    database_url: str,
):
    run_bat = destination / "run.bat"

    content = rf"""@echo off

cd /d "{destination}"

SET PORT={port}
SET DATABASE_URL={database_url}

echo ==========================================
echo Starting Rust application
echo ==========================================
echo Executable: {executable}
echo Port: %PORT%
echo ==========================================

if not exist "{executable}" (
    echo ERROR: Executable not found: {executable}
    exit /B 1
)

"{executable}"

SET APP_EXIT_CODE=%ERRORLEVEL%

echo Rust application exited with code %APP_EXIT_CODE%

exit /B %APP_EXIT_CODE%
"""

    run_bat.write_text(
        content,
        encoding="utf-8",
    )