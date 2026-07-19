#!/usr/bin/env uv run
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

from tomlkit import dumps

from my_package import gitignore
from my_package.toml_template import create_toml

dummy_settings: dict[str, str | list[str] | Any | dict[str, Any]] = {
    "name": "user",
    "email": "example@example.com",
    "main_source_code_folder": "src",
    "main_package_name": "my_package",
    "git_user": "user",
    "dependencies": ["python-dotenv"],
    "dev_dependencies": ["ruff", "pytest", "pytest-xdist"],
    "open_vscode": False,
    "ruff_lint_rules_select": [
        "ASYNC",
        "A",
        "ANN",
        "B",
        "BLE",
        "C4",
        "C90",
        "COM",
        "E",
        "EM",
        "ERA",
        "EXE",
        "F",
        "FBT",
        "FIX",
        "I",
        "ICN",
        "ISC",
        "Q",
        "RET",
        "RSE",
        "S",
        "SIM",
        "SLF",
        "T10",
        "T20",
        "TC",
        "TD",
        "TRY",
        "UP",
        "W",
        "YTT",
        "RUF",
        "N",
    ],
    "ruff_lint_rules_ignore": ["T201", "COM812", "COM819", "EXE002"],
    "vs_code_settings": {},
    "vs_code_extensions": {"recommendations": []},
}


@dataclass(frozen=True)
class CliOptions:
    project_name: str
    version: str
    git: bool
    dependencies: list[str]
    config: bool


def ensure_settings(settings_path: Path) -> None:
    if not settings_path.exists():
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(dummy_settings, f, indent=4, ensure_ascii=False)


def load_settings(settings_path: Path) -> dict[str, Any]:
    ensure_settings(settings_path)
    try:
        with open(settings_path, encoding="utf-8") as f:
            loaded = json.load(f)
    except json.JSONDecodeError as error:
        msg = f"Configuração JSON inválida em {settings_path}: {error}"
        raise ValueError(msg) from error

    if not isinstance(loaded, dict):
        msg = f"A configuração em {settings_path} deve ser um objeto JSON."
        raise TypeError(msg)

    loaded_settings = cast("dict[str, Any]", loaded)
    original_settings = dict(loaded_settings)
    loaded_settings.pop("create_folders", None)
    if loaded_settings.get("dependencies") == ["dotenv"]:
        loaded_settings["dependencies"] = ["python-dotenv"]

    settings = dict(dummy_settings)
    settings.update(loaded_settings)
    if settings != original_settings:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    return settings


def open_settings(settings_path: Path) -> None:
    if sys.platform == "win32":
        command = ["cmd", "/c", "start", "", str(settings_path)]
    elif sys.platform == "darwin":
        command = ["open", str(settings_path)]
    else:
        command = ["xdg-open", str(settings_path)]
    subprocess.run(command, check=True)


def current_python_version() -> str:
    version = sys.version_info
    return f"{version.major}.{version.minor}.{version.micro}"


def parse_python_version(value: str) -> str:
    if value == "global":
        return current_python_version()
    if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value) is None:
        msg = "use 'global' ou uma versão como 3.14.3"
        raise argparse.ArgumentTypeError(msg)
    return value


def parse_dependencies(value: str) -> list[str]:
    dependencies = [dependency.strip() for dependency in value.split(",")]
    if any(not dependency for dependency in dependencies):
        msg = "informe dependências separadas por vírgula, sem itens vazios"
        raise argparse.ArgumentTypeError(msg)
    return dependencies


def parse_args(args: list[str]) -> CliOptions:
    parser = argparse.ArgumentParser(
        prog=Path(args[0]).name,
        description="Cria um novo projeto Python configurado com uv.",
    )
    parser.add_argument("project_name", nargs="?", help="nome do novo projeto")
    parser.add_argument(
        "-cfg",
        "--config",
        action="store_true",
        help="abre o arquivo de configuração do pproject",
    )
    parser.add_argument(
        "-v",
        "--version",
        type=parse_python_version,
        help="versão do Python, por exemplo 3.14.3 ou global",
    )
    parser.add_argument(
        "-d",
        "--dependency",
        action="append",
        type=parse_dependencies,
        default=[],
        help="dependência ou lista separada por vírgulas; pode ser repetido",
    )
    parser.add_argument(
        "-g",
        "--git",
        action="store_true",
        help="inicializa o Git e cria o primeiro commit",
    )
    parsed = parser.parse_args(args[1:])

    if parsed.config:
        if parsed.project_name or parsed.version or parsed.git or parsed.dependency:
            parser.error("--config não pode ser combinado com criação de projeto")
        return CliOptions(
            project_name="",
            version=current_python_version(),
            git=False,
            dependencies=[],
            config=True,
        )

    if parsed.project_name is None:
        parser.error("informe o nome do projeto")

    dependencies = [
        dependency
        for dependency_group in parsed.dependency
        for dependency in dependency_group
    ]
    return CliOptions(
        project_name=parsed.project_name,
        version=parsed.version or current_python_version(),
        git=parsed.git,
        dependencies=dependencies,
        config=False,
    )


def resolve_project_path(path: Path, project_name: str) -> Path:
    relative_path = Path(project_name)
    if (
        not project_name
        or relative_path.is_absolute()
        or len(relative_path.parts) != 1
        or project_name in {".", ".."}
    ):
        msg = "O nome do projeto deve ser um nome simples, sem caminhos."
        raise ValueError(msg)

    project_path = path / relative_path
    if project_path.exists():
        msg = f"O destino já existe: {project_path}"
        raise FileExistsError(msg)

    return project_path


def build_project_structure(
    project_path: Path,
    settings: dict[str, Any],
    version: str,
    project_name: str,
    *,
    git: bool,
) -> None:
    # Vs Code folders and configs
    vscode_path = project_path / ".vscode"
    vscode_path.mkdir(exist_ok=True)

    vscode_settings_path = vscode_path / "settings.json"
    vscode_extensions_path = vscode_path / "extensions.json"
    with open(vscode_settings_path, "w", encoding="utf-8") as f:
        json.dump(settings["vs_code_settings"], f, indent=4)
    with open(vscode_extensions_path, "w", encoding="utf-8") as f:
        json.dump(settings["vs_code_extensions"], f, indent=4)

    # Main package
    package_path = (
        project_path
        / f"{settings['main_source_code_folder']}/{settings['main_package_name']}"
    )
    source_path = project_path / settings["main_source_code_folder"]
    tests_path = project_path / "tests"
    package_path.mkdir(parents=True, exist_ok=True)
    tests_path.mkdir(parents=True, exist_ok=True)

    main_source = dedent(
        r"""
        import os

        from dotenv import load_dotenv


        def main() -> None:
            load_dotenv()
            print(f'\n{os.environ["GREETINGS"]}')


        if __name__ == "__main__":
            main()
        """
    ).lstrip()
    test_source = dedent(
        """\
        from typing import TYPE_CHECKING

        from app.main import main

        if TYPE_CHECKING:
            import pytest


        def test_main(
            monkeypatch: pytest.MonkeyPatch,
            capsys: pytest.CaptureFixture[str],
        ) -> None:
            monkeypatch.setenv("GREETINGS", "Template is working.")

            main()

            assert capsys.readouterr().out.strip() == "Template is working."
        """
    )
    (source_path / "main.py").write_text(main_source, encoding="utf-8")
    (package_path / "__init__.py").write_text("", encoding="utf-8")
    (tests_path / "test_main.py").write_text(test_source, encoding="utf-8")
    # Metadata
    toml_path = project_path / "pyproject.toml"
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(
            dumps(
                data=create_toml(
                    version=version,
                    project_name=project_name,
                    settings=settings,
                )
            )
        )

    if git:
        (project_path / ".gitignore").write_text(gitignore.template, encoding="utf-8")

    (project_path / "README.md").write_text("", encoding="utf-8")


def install_dependencies(
    project_path: Path, settings: dict[str, list[str]], dependencies: list[str]
) -> None:
    if settings["dev_dependencies"]:
        command = ["uv", "add", "--dev", *settings["dev_dependencies"]]
        subprocess.run(command, cwd=project_path, check=True)
    settings["dependencies"].extend(dependencies)
    if settings["dependencies"]:
        command = ["uv", "add", *settings["dependencies"]]
        subprocess.run(command, cwd=project_path, check=True)


def init_git(project_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=project_path, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=project_path, check=True)
    subprocess.run(["git", "add", "."], cwd=project_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Clear Project"], cwd=project_path, check=True
    )


def main(args: list[str], path: Path) -> None:
    options = parse_args(args)

    settings_path = Path.home() / ".pproject.settings.json"
    if options.config:
        ensure_settings(settings_path=settings_path)
        open_settings(settings_path)
        return

    try:
        project_path = resolve_project_path(path, options.project_name)
    except (FileExistsError, ValueError) as error:
        print(f"Erro: {error}")
        sys.exit(1)

    try:
        settings = load_settings(settings_path)
    except (TypeError, ValueError) as error:
        print(f"Erro: {error}")
        sys.exit(1)

    subprocess.run(
        ["uv", "init", str(project_path), "--bare", "--python", options.version],
        check=True,
    )

    build_project_structure(
        project_path=project_path,
        settings=settings,
        version=options.version,
        project_name=options.project_name,
        git=options.git,
    )
    install_dependencies(
        project_path=project_path,
        settings=settings,
        dependencies=options.dependencies,
    )

    env_content = "GREETINGS='Project created, environment variables working fine.'\n"
    (project_path / ".env").write_text(env_content, encoding="utf-8")
    (project_path / ".env.example").write_text(env_content, encoding="utf-8")

    if options.git:
        init_git(project_path=project_path)

    subprocess.run(
        ["uv", "run", f"{settings['main_source_code_folder']}/main.py"],
        cwd=project_path,
        check=True,
    )

    if settings["open_vscode"]:
        subprocess.run(["code", str(project_path)], check=True)


if __name__ == "__main__":
    main(sys.argv, Path.cwd())
