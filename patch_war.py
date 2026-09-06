import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def fail(message: str) -> None:
    print(f"\nERROR: {message}", file=sys.stderr)
    sys.exit(1)


def class_relative_path(class_name: str) -> Path:
    return Path(*class_name.split("."))


def find_jar(war_dir: Path, jar_name: str) -> Path:
    expected = war_dir / "WEB-INF" / "lib" / jar_name

    if expected.is_file():
        return expected

    matches = list(war_dir.rglob(jar_name))

    if not matches:
        fail(f"No se encontro {jar_name} dentro del WAR")

    if len(matches) > 1:
        print(f"Se encontraron varios {jar_name}:")
        for item in matches:
            print(f"  {item}")
        fail("El JAR objetivo es ambiguo")

    return matches[0]


def find_compiled_classes(
    classes_dir: Path,
    class_name: str,
) -> list[Path]:

    relative = class_relative_path(class_name)
    package_dir = classes_dir / relative.parent
    simple_name = relative.name

    if not package_dir.is_dir():
        fail(
            f"No existe el package compilado: {package_dir}"
        )

    # Clase principal + inner/anonymous classes:
    # UserController.class
    # UserController$1.class
    # UserController$Foo.class

    result = []

    main_class = package_dir / f"{simple_name}.class"

    if main_class.is_file():
        result.append(main_class)

    result.extend(
        sorted(package_dir.glob(f"{simple_name}$*.class"))
    )

    if not result:
        fail(
            f"No existen clases compiladas para {class_name}"
        )

    return result


def list_jar_entries(jar_path: Path) -> set[str]:
    with zipfile.ZipFile(jar_path, "r") as jar:
        return set(jar.namelist())


def patch_class(
    jar_path: Path,
    classes_dir: Path,
    class_name: str,
) -> None:

    compiled = find_compiled_classes(
        classes_dir,
        class_name,
    )

    print()
    print("=" * 70)
    print(f"PATCH: {class_name}")
    print(f"JAR  : {jar_path}")
    print("=" * 70)

    for cls in compiled:
        print(f"  -> {cls.relative_to(classes_dir)}")

    #
    # Usamos jar -uf individualmente para NO introducir
    # otras clases del mismo package.
    #
    for cls in compiled:

        relative = cls.relative_to(classes_dir)

        command = [
            "jar",
            "-uf",
            str(jar_path),
            "-C",
            str(classes_dir),
            str(relative),
        ]

        result = subprocess.run(command)

        if result.returncode != 0:
            fail(
                f"No se pudo insertar {relative} "
                f"en {jar_path.name}"
            )

    #
    # Verificacion
    #
    entries = list_jar_entries(jar_path)

    for cls in compiled:

        relative = (
            cls.relative_to(classes_dir)
            .as_posix()
        )

        if relative not in entries:
            fail(
                f"Verificacion fallo: "
                f"{relative} no esta en {jar_path.name}"
            )

    print(f"OK: {class_name}")


def extract_war(
    war_file: Path,
    destination: Path,
) -> None:

    print()
    print("=" * 70)
    print("EXTRACT WAR")
    print("=" * 70)
    print(war_file)

    with zipfile.ZipFile(war_file, "r") as war:
        war.extractall(destination)


def build_war(
    source_dir: Path,
    output_file: Path,
) -> None:

    print()
    print("=" * 70)
    print("BUILD PATCHED WAR")
    print("=" * 70)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_file.exists():
        output_file.unlink()

    with zipfile.ZipFile(
        output_file,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as war:

        for file in source_dir.rglob("*"):

            if not file.is_file():
                continue

            relative = file.relative_to(source_dir)

            war.write(
                file,
                relative.as_posix(),
            )

    print(f"Generado: {output_file}")


def verify_final_war(
    war_file: Path,
    patches: list[tuple[str, str]],
) -> None:

    print()
    print("=" * 70)
    print("VERIFY FINAL WAR")
    print("=" * 70)

    with tempfile.TemporaryDirectory(
        prefix="verify_war_"
    ) as tmp:

        tmp_dir = Path(tmp)

        with zipfile.ZipFile(war_file, "r") as war:
            war.extractall(tmp_dir)

        for jar_name, class_name in patches:

            jar_path = find_jar(
                tmp_dir,
                jar_name,
            )

            entries = list_jar_entries(jar_path)

            expected = (
                class_relative_path(class_name)
                .with_suffix(".class")
                .as_posix()
            )

            if expected not in entries:
                fail(
                    f"{expected} no existe en "
                    f"{jar_name} dentro del WAR final"
                )

            print(
                f"OK: {jar_name} -> {expected}"
            )


def parse_patch(value: str) -> tuple[str, str]:

    if "=" not in value:
        fail(
            "Formato invalido para --patch. "
            "Use JAR=CLASE"
        )

    jar_name, class_name = value.split("=", 1)

    jar_name = jar_name.strip()
    class_name = class_name.strip()

    if not jar_name or not class_name:
        fail(
            "Formato invalido para --patch. "
            "Use JAR=CLASE"
        )

    return jar_name, class_name


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Parchea clases Java compiladas dentro "
            "de JARs contenidos en un WAR."
        )
    )

    parser.add_argument(
        "--war",
        required=True,
        help="WAR original",
    )

    parser.add_argument(
        "--classes",
        required=True,
        help="Directorio raiz de clases compiladas",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="WAR parcheado de salida",
    )

    parser.add_argument(
        "--patch",
        action="append",
        required=True,
        help=(
            "Patch JAR=CLASE. "
            "Puede repetirse varias veces."
        ),
    )

    args = parser.parse_args()

    war_file = Path(args.war).resolve()
    classes_dir = Path(args.classes).resolve()
    output_file = Path(args.output).resolve()

    if not war_file.is_file():
        fail(f"WAR no encontrado: {war_file}")

    if not classes_dir.is_dir():
        fail(
            f"Directorio de clases no encontrado: "
            f"{classes_dir}"
        )

    patches = [
        parse_patch(value)
        for value in args.patch
    ]

    print("=" * 70)
    print("SURGICAL WAR PATCHER")
    print("=" * 70)
    print(f"WAR     : {war_file}")
    print(f"CLASSES : {classes_dir}")
    print(f"OUTPUT  : {output_file}")

    for jar_name, class_name in patches:
        print(
            f"PATCH   : {jar_name} -> {class_name}"
        )

    #
    # Trabajamos siempre sobre una copia temporal.
    # El WAR original NO se modifica.
    #
    with tempfile.TemporaryDirectory(
        prefix="war_patch_"
    ) as tmp:

        work_dir = Path(tmp)

        extract_war(
            war_file,
            work_dir,
        )

        for jar_name, class_name in patches:

            jar_path = find_jar(
                work_dir,
                jar_name,
            )

            patch_class(
                jar_path,
                classes_dir,
                class_name,
            )

        build_war(
            work_dir,
            output_file,
        )

    verify_final_war(
        output_file,
        patches,
    )

    print()
    print("=" * 70)
    print("PATCH COMPLETADO CORRECTAMENTE")
    print("=" * 70)
    print(output_file)


if __name__ == "__main__":
    main()