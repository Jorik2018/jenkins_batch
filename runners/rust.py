from pathlib import Path


def create_runner(
    destination: Path,
    executable: str,
    env_vars: list[str],
):
    run_bat = destination / "run.bat"

    env_lines = []

    for item in env_vars:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        env_lines.append(f'SET "{key}={value}"')

    env_block = "\n".join(env_lines)

    content = rf"""@echo off

cd /d "{destination}"

{env_block}

echo ==========================================
echo Starting Rust application
echo ==========================================
echo Executable: {executable}
echo Port: %PORT%
echo Vault: %VAULT_ADDR%
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