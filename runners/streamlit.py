
from pathlib import Path

def create_runner(
    destination: Path,
    port: int = 7878,
    base_path: str = "streamlit",
    app_file: str = "streamlit_erp/app.py",
):
    run_bat = destination / "run.bat"

    content = rf"""@echo off

cd /d "{destination}"

REM ==========================================
REM UTF-8
REM ==========================================

chcp 65001 >NUL

SET PYTHONUTF8=1
SET PYTHONIOENCODING=utf-8

echo ==========================================
echo Starting Streamlit application
echo ==========================================

echo Python:
".venv\Scripts\python.exe" --version

echo.

echo Streamlit:
".venv\Scripts\streamlit.exe" version

echo.

echo ==========================================
echo Launching Streamlit
echo ==========================================

".venv\Scripts\streamlit.exe" run "{app_file}" ^
    --server.address=127.0.0.1 ^
    --server.port={port} ^
    --server.baseUrlPath={base_path} ^
    --server.headless=true

SET STREAMLIT_EXIT_CODE=%ERRORLEVEL%

echo ==========================================
echo Streamlit exited with code %STREAMLIT_EXIT_CODE%
echo ==========================================

exit /B %STREAMLIT_EXIT_CODE%
"""

    run_bat.write_text(
        content,
        encoding="utf-8",
    )

    print(f"Created Streamlit runner: {run_bat}")
