from pathlib import Path

def create_runner(
    destination: Path,
    port: int = 5000,
    host: str = "0.0.0.0",
    wsgi_app: str = "app:app",
):
    run_bat = destination / "run.bat"

    content = rf"""@echo off

cd /d "{destination}"

chcp 65001 >NUL

SET PYTHONUTF8=1
SET PYTHONIOENCODING=utf-8

echo ==========================================
echo Starting Flask application
echo ==========================================

echo Python:
".venv\Scripts\python.exe" --version

echo.
echo ==========================================
echo Launching Waitress
echo ==========================================

".venv\Scripts\python.exe" -m waitress ^
    --listen={host}:{port} ^
    {wsgi_app}

SET APP_EXIT_CODE=%ERRORLEVEL%

echo ==========================================
echo Flask application exited with code %APP_EXIT_CODE%
echo ==========================================

exit /B %APP_EXIT_CODE%
"""

    run_bat.write_text(
        content,
        encoding="utf-8",
    )

    print(f"Created Flask runner: {run_bat}")
