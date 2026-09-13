from pathlib import Path


def create_runner(
    destination: Path,
    executable: str,
):
    run_bat = destination / "run.bat"

    content = rf"""@echo off

call :main >> "%~dp0run.log" 2>&1
exit /B %ERRORLEVEL%


:main

echo.
echo ==========================================
echo Starting Rust application
echo Date: %DATE% %TIME%
echo ==========================================

cd /d "%~dp0"

echo Working directory: %CD%
echo Executable: {executable}
echo Port: %PORT%

if defined VAULT_TOKEN (
    echo VAULT_TOKEN: configured
) else (
    echo VAULT_TOKEN: NOT CONFIGURED
)

echo ==========================================

if not exist "{executable}" (
    echo ERROR: Executable not found: {executable}
    exit /B 1
)

echo Starting executable...
echo.

"{executable}"

SET "APP_EXIT_CODE=%ERRORLEVEL%"

echo.
echo ==========================================
echo Rust application exited with code %APP_EXIT_CODE%
echo ==========================================

exit /B %APP_EXIT_CODE%
"""

    run_bat.write_text(
        content,
        encoding="utf-8",
    )

    print(f"Created Rust runner: {run_bat}")