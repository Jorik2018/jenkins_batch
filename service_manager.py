import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


SERVICE_WRAPPER = Path(r"D:\wildfly\bin\service.exe")


def execute(command: list[str], cwd: Path | None = None, check: bool = False):
    print()
    print(">", subprocess.list2cmdline(command))

    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="cp1252",
        errors="replace",
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{subprocess.list2cmdline(command)}"
        )

    return result


def service_exists(service_id: str) -> bool:
    result = execute(
        ["sc", "query", service_id]
    )

    return result.returncode == 0


def service_state(service_id: str) -> str | None:
    result = execute(
        ["sc", "query", service_id]
    )

    if result.returncode != 0:
        return None

    output = result.stdout.upper()

    for state in (
        "RUNNING",
        "STOPPED",
        "START_PENDING",
        "STOP_PENDING",
        "PAUSED",
    ):
        if state in output:
            return state

    return "UNKNOWN"


def wait_for_state(
    service_id: str,
    expected_state: str,
    timeout: int = 60,
):
    print(
        f'Waiting for service "{service_id}" '
        f"to become {expected_state}..."
    )

    deadline = time.time() + timeout

    while time.time() < deadline:
        state = service_state(service_id)

        if state == expected_state:
            print(
                f'Service "{service_id}" is {expected_state}.'
            )
            return

        time.sleep(2)

    raise RuntimeError(
        f'Service "{service_id}" did not become '
        f"{expected_state} after {timeout} seconds."
    )


def stop(service_id: str):
    if not service_exists(service_id):
        print(
            f'Service "{service_id}" does not exist. '
            "Nothing to stop."
        )
        return

    state = service_state(service_id)

    if state == "STOPPED":
        print(
            f'Service "{service_id}" is already stopped.'
        )
        return

    execute(
        ["sc", "stop", service_id],
    )

    wait_for_state(
        service_id,
        "STOPPED",
    )


def start(service_id: str):
    if not service_exists(service_id):
        raise RuntimeError(
            f'Service "{service_id}" is not installed.'
        )

    state = service_state(service_id)

    if state == "RUNNING":
        print(
            f'Service "{service_id}" is already running.'
        )
        return

    execute(
        ["sc", "start", service_id],
        check=True,
    )

    wait_for_state(
        service_id,
        "RUNNING",
    )


def create_reflex_run_bat(destination: Path):
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

def create_streamlit_run_bat(
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

def create_service_xml(
    destination: Path,
    service_id: str,
    service_name: str,
    description: str,
):
    xml = f"""<service>
  <id>{service_id}</id>
  <name>{service_name}</name>
  <description>{description}</description>

  <executable>cmd.exe</executable>
  <arguments>/c "{destination}\\run.bat"</arguments>

  <workingdirectory>{destination}</workingdirectory>

  <logmode>rotate</logmode>

  <stopparentprocessfirst>true</stopparentprocessfirst>

  <onfailure action="restart" delay="10 sec"/>
  <onfailure action="restart" delay="30 sec"/>
</service>
"""

    service_xml = destination / "service.xml"

    service_xml.write_text(
        xml,
        encoding="utf-8",
    )

    print(f"Created: {service_xml}")

def create_run_bat(
    destination: Path,
    app_type: str,
    port: int = 7878,
    base_path: str = "streamlit",
    app_file: str = "streamlit_erp/app.py",
):
    if app_type == "reflex":
        create_reflex_run_bat(destination)

    elif app_type == "streamlit":
        create_streamlit_run_bat(
            destination=destination,
            port=port,
            base_path=base_path,
            app_file=app_file,
        )

    else:
        raise RuntimeError(
            f"Unsupported application type: {app_type}"
        )
    
def install(
    service_id: str,
    destination: Path,
    service_name: str | None = None,
    description: str | None = None,
    app_type: str = "reflex",
    port: int = 7878,
    base_path: str = "streamlit",
    app_file: str = "streamlit_erp/app.py",
):
    destination = destination.resolve()

    if not destination.exists():
        raise RuntimeError(
            f"Destination does not exist: {destination}"
        )

    service_name = service_name or service_id
    description = (
        description
        or f"Reflex application - {service_id}"
    )

    print("=" * 60)
    print("CONFIGURING WINDOWS SERVICE")
    print("=" * 60)

    print("Service ID: ", service_id)
    print("Destination:", destination)

    wrapper_destination = (
        destination / "service.exe"
    )

    shutil.copy2(
        SERVICE_WRAPPER,
        wrapper_destination,
    )

    print(
        f"Copied wrapper: {wrapper_destination}"
    )

    create_run_bat(
        destination=destination,
        app_type=app_type,
        port=port,
        base_path=base_path,
        app_file=app_file,
    )

    create_service_xml(
        destination,
        service_id,
        service_name,
        description,
    )

    if service_exists(service_id):
        print(
            f'Service "{service_id}" is already installed.'
        )
        print(
            "Configuration files were refreshed; "
            "installation skipped."
        )
        return

    print(
        f'Installing service "{service_id}"...'
    )

    execute(
        [
            str(wrapper_destination),
            "install",
        ],
        cwd=destination,
        check=True,
    )

    if not service_exists(service_id):
        raise RuntimeError(
            f'Service "{service_id}" '
            "was not registered correctly."
        )

    print(
        f'Service "{service_id}" installed.'
    )


def uninstall(service_id: str, destination: Path):
    if not service_exists(service_id):
        print(
            f'Service "{service_id}" '
            "is already uninstalled."
        )
        return

    stop(service_id)

    wrapper = (
        destination.resolve()
        / "service.exe"
    )

    execute(
        [
            str(wrapper),
            "uninstall",
        ],
        cwd=destination,
        check=True,
    )

    print(
        f'Service "{service_id}" uninstalled.'
    )


def status(service_id: str):
    state = service_state(service_id)

    if state is None:
        print(
            f'{service_id}: NOT INSTALLED'
        )
        return

    print(
        f"{service_id}: {state}"
    )


def restart(service_id: str):
    stop(service_id)
    start(service_id)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Windows service manager for Python web apps."
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    stop_parser = sub.add_parser("stop")
    stop_parser.add_argument("service_id")

    start_parser = sub.add_parser("start")
    start_parser.add_argument("service_id")

    restart_parser = sub.add_parser("restart")
    restart_parser.add_argument("service_id")

    status_parser = sub.add_parser("status")
    status_parser.add_argument("service_id")

    install_parser = sub.add_parser("install")

    install_parser.add_argument(
        "service_id"
    )

    install_parser.add_argument(
        "destination",
        type=Path,
    )

    install_parser.add_argument(
        "--name"
    )

    install_parser.add_argument(
        "--description"
    )

    install_parser.add_argument(
        "--type",
        dest="app_type",
        choices=[
            "reflex",
            "streamlit",
        ],
        default="reflex",
        help="Application type. Default: reflex",
    )

    install_parser.add_argument(
        "--port",
        type=int,
        default=7878,
        help="Port used by the application",
    )

    install_parser.add_argument(
        "--base-path",
        default="streamlit",
        help="Base URL path for Streamlit",
    )

    install_parser.add_argument(
        "--app-file",
        default="streamlit_erp/app.py",
        help="Streamlit application entry point",
    )

    uninstall_parser = sub.add_parser(
        "uninstall"
    )

    uninstall_parser.add_argument(
        "service_id"
    )

    uninstall_parser.add_argument(
        "destination",
        type=Path,
    )

    return parser.parse_args()

def main():
    args = parse_args()

    try:
        if args.command == "stop":
            stop(args.service_id)

        elif args.command == "start":
            start(args.service_id)

        elif args.command == "restart":
            restart(args.service_id)

        elif args.command == "status":
            status(args.service_id)

        elif args.command == "install":
            install(
                service_id=args.service_id,
                destination=args.destination,
                service_name=args.name,
                description=args.description,
                app_type=args.app_type,
                port=args.port,
                base_path=args.base_path,
                app_file=args.app_file,
            )

        elif args.command == "uninstall":
            uninstall(
                args.service_id,
                args.destination,
            )

    except Exception as exc:
        print()
        print("ERROR:", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()