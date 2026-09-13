import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path
from xml.sax.saxutils import escape

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

def parse_env_vars(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}

    for item in items:
        if "=" not in item:
            raise RuntimeError(
                f"Invalid --env value: {item}. Expected NAME=VALUE"
            )

        name, value = item.split("=", 1)

        name = name.strip()

        if not name:
            raise RuntimeError(
                f"Invalid --env value: {item}"
            )

        result[name] = value

    return result

def create_service_xml(
    destination: Path,
    service_id: str,
    service_name: str,
    description: str,
    env_vars: list[str] | None = None,
):
    print("DEBUG create_service_xml env_vars:", repr(env_vars))

    env_vars = env_vars or []

    print("DEBUG normalized env_vars:", repr(env_vars))

    def xml_attr(value: str) -> str:
        return escape(
            value,
            {
                '"': "&quot;",
                "'": "&apos;",
            },
        )

    env_lines = []

    for item in env_vars:
        if "=" not in item:
            raise RuntimeError(
                f"Invalid environment variable: {item}. "
                "Expected NAME=VALUE"
            )

        name, value = item.split("=", 1)

        name = name.strip()

        if not name:
            raise RuntimeError(
                f"Invalid environment variable: {item}"
            )

        env_lines.append(
            f'  <env name="{xml_attr(name)}" '
            f'value="{xml_attr(value)}" />'
        )

    env_xml = "\n".join(env_lines)

    xml = f"""<service>
  <id>{xml_attr(service_id)}</id>
  <name>{xml_attr(service_name)}</name>
  <description>{xml_attr(description)}</description>

  <executable>cmd.exe</executable>
  <arguments>/c "{xml_attr(str(destination))}\\run.bat"</arguments>

  <workingdirectory>{xml_attr(str(destination))}</workingdirectory>

{env_xml}

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

def create_runner(
    destination: Path,
    app_type: str,
    base_path: str = "streamlit",
    app_file: str = "streamlit_erp/app.py",
    host: str = "0.0.0.0",
    wsgi_app: str = "app:app",
    executable: str | None = None,
    env_vars: list[str] | None = None,
):
    if app_type == "reflex":
        from runners.reflex import create_runner
        create_runner(destination)

    elif app_type == "streamlit":
        from runners.streamlit import create_runner
        create_runner(
            destination=destination,
            base_path=base_path,
            app_file=app_file,
        )
    elif app_type == "flask":
        from runners.flask import create_runner
        create_runner(
            destination=destination,
            host=host,
            wsgi_app=wsgi_app,
        )
    elif app_type == "go":
        from runners.flask import create_runner
        create_runner(
            destination=destination,
            executable=executable
        )
    elif app_type == "rust":
        from runners.rust import create_runner
        create_runner(
            destination=destination,
            executable=executable
        )
    else:
        raise RuntimeError(
            f"Unsupported application type: {app_type}"
        )
    
def install(
    service_id: str,
    destination: Path,
    service_name: str,
    description: str,
    app_type: str,
    base_path: str = "streamlit",
    app_file: str = "streamlit_erp/app.py",
    host: str = "0.0.0.0",
    wsgi_app: str = "app:app",
    executable: str | None = None,
    env_vars: list[str] | None = None,
):
    destination = destination.resolve()
    env_vars = env_vars or []

    print("DEBUG install env_vars:", repr(env_vars))

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

    create_runner(
        destination=destination,
        app_type=app_type,
        base_path=base_path,
        app_file=app_file,
        host=host,
        wsgi_app=wsgi_app,
        executable=executable,
        env_vars=env_vars or [],
    )

    create_service_xml(
        destination,
        service_id,
        service_name,
        description,
        env_vars=env_vars or [],
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
        help="Application type",
    )

    install_parser.add_argument(
        "--env",
        action="append",
        default=[],
        help="Environment variable NAME=VALUE. Can be repeated.",
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

    install_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host used by the application",
    )

    install_parser.add_argument(
        "--wsgi-app",
        default="app:app",
        help="WSGI application entry point, e.g. app:app",
    )

    install_parser.add_argument(
        "--executable",
        help="Executable file for Go applications, e.g. my-api.exe",
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
                base_path=args.base_path,
                app_file=args.app_file,
                host=args.host,
                wsgi_app=args.wsgi_app,
                executable=args.executable,
                env_vars=args.env,
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