from pathlib import Path

def create_runner(destination: Path):
    run_bat = destination / "run.bat"

    node_home = (
        r"C:\wildfly-18.0.1.Final\bin\.data"
        r"\node-v22.13.0-win-x64"
    )

    content = rf"""@echo off

cd /d "{destination}"

REM ==========================================
REM UTF-8 para Python / Reflex / Rich
REM ==========================================

chcp 65001 >NUL

SET PYTHONUTF8=1
SET PYTHONIOENCODING=utf-8

REM ==========================================
REM Node aislado de Nodist
REM ==========================================

SET NODE_HOME={node_home}

SET NODIST_PREFIX=
SET NODE_PATH=
SET NPM_CONFIG_SAVE_EXACT=true

REM Node + comandos basicos Windows + PowerShell
SET PATH=%NODE_HOME%;C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0

echo ==========================================
echo Starting Reflex application
echo ==========================================

echo Python:
".venv\Scripts\python.exe" --version

echo.

echo Node:
where node
"%NODE_HOME%\node.exe" --version

echo.

echo NPM:
where npm
CALL "%NODE_HOME%\npm.cmd" --version

echo.

echo Python Encoding:
".venv\Scripts\python.exe" -c "import sys; print(sys.stdout.encoding)"

REM ==========================================
REM Custom MapRegistry
REM ==========================================

if not exist ".web\components" (
    mkdir ".web\components"
)

copy /Y ^
    "app\components\map_registry.jsx" ^
    ".web\components\map_registry.jsx"

if errorlevel 1 (
    echo ERROR: Could not copy map_registry.jsx
    exit /B 1
)

echo ==========================================
echo Launching Reflex
echo ==========================================

".venv\Scripts\reflex.exe" run --env prod --loglevel debug

SET REFLEX_EXIT_CODE=%ERRORLEVEL%

echo ==========================================
echo Reflex exited with code %REFLEX_EXIT_CODE%
echo ==========================================

exit /B %REFLEX_EXIT_CODE%
"""

    run_bat.write_text(
        content,
        encoding="utf-8",
    )

    print(f"Created: {run_bat}")
