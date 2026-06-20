import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from tomlkit import dumps

from my_package import gitignore
from my_package.toml_template import create_toml

load_dotenv(".env")


dummy_settings: dict[str, str | list[str] | Any | dict[str, Any]] = {
    "name": "user",
    "email": "example@example.com",
    "main_package_name": "my_package",
    "git_user": "user",
    "dependencies": ["python-dotenv"],
    "dev_dependencies": ["pytest", "pytest-xdist"],
    "open_vscode": False,
    "ruff_lint_rules_select": [],
    "ruff_lint_rules_ignore": ["T201", "COM812"],
    "vs_code_settings": {},
    "vs_code_extensions": {"recommendations": []},
}


def ensure_settings(settings_path: Path) -> None:

    if not settings_path.exists():
        settings_path.touch(exist_ok=True)

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(dummy_settings, f, indent=4, ensure_ascii=False)


def parse_args(args: list[str], settings_path: Path) -> tuple[str, str, bool]:

    if len(args) < 2:
        print("Uso: pproject <nome_do_projeto>  OU  pproject -cfg")
        sys.exit(1)

    if args[1] in ["-cfg", "--config"]:
        subprocess.run(f"notepad {settings_path}")  # noqa: S603
        sys.exit(0)

    project_name = args[1]
    left_args = args[2:]

    version = None
    git = False

    for i, arg in enumerate(left_args):
        match arg:
            case "-v" | "--version":
                if i + 1 < len(left_args):
                    if left_args[i + 1] == "global":
                        version = subprocess.getoutput("python --version").split()[1]  # noqa: S605, S607
                    if version := re.search(r"[0-9]+[.][0-9]+", left_args[i + 1]):
                        version = version.group(0)
                    else:
                        print("❌ Erro: Versão do Python inválida.")
                        sys.exit(1)
                else:
                    print("❌ Erro: Informe a versão após o parâmetro -v.")
                    sys.exit(1)
            case "-g" | "--git":
                git = True
            case _:
                pass

    if version is None:
        version = subprocess.getoutput("python --version").split()[1]  # noqa: S605, S607

    return project_name, version, git


def build_project_structure(project_path: Path, settings: dict[str, Any], version: str, project_name: str) -> None:
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
    package_path = project_path / f"src/{settings['main_package_name']}"
    package_path.mkdir(parents=True, exist_ok=True)

    main = r"""import os

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    print(f'\n{os.environ["GREETINGS"]}')


if __name__ == "__main__":
    main()
"""
    main_file = project_path / "src/main.py"
    main_file.write_text(main, encoding="utf-8")
    (package_path / "__init__.py").write_text("", encoding="utf-8")

    (project_path / "tests").mkdir(parents=True, exist_ok=True)

    # Metadata
    toml_path = project_path / "pyproject.toml"
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(dumps(data=create_toml(version=version, project_name=project_name, settings=settings)))

    (project_path / ".gitignore").write_text(gitignore.template, encoding="utf-8")
    (project_path / "README.md").write_text("", encoding="utf-8")


def install_dependencies(project_name: str, settings: dict[str, Any]) -> None:

    if settings["dev_dependencies"]:
        command = ["uv", "add", "--dev", *settings["dev_dependencies"]]
        subprocess.run(command, cwd=project_name)  # noqa: S603

    if settings["dependencies"]:
        command = ["uv", "add", *settings["dependencies"]]
        subprocess.run(command, cwd=project_name)  # noqa: S603


def init_git(project_name: str) -> None:

    subprocess.run(["git", "init"], cwd=project_name, check=True)  # noqa: S607
    subprocess.run(["git", "branch", "-M", "main"], cwd=project_name, check=True)  # noqa: S607
    subprocess.run(["git", "add", "."], cwd=project_name, check=True)  # noqa: S607
    subprocess.run(["git", "commit", "-m", "Clear Project"], cwd=project_name, check=True)  # noqa: S607


def main() -> None:
    args = sys.argv
    path = Path.cwd()

    settings_path = Path.home() / ".pproject.settings.json"
    ensure_settings(settings_path=settings_path)

    project_name, version, git = parse_args(args, settings_path=settings_path)

    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    subprocess.call(["uv", "init", project_name, "--bare", "--python", version])  # noqa: S607, S603

    project_path = path / f"{project_name}"
    build_project_structure(project_path=project_path, settings=settings, version=version, project_name=project_name)

    install_dependencies(project_name=project_name, settings=settings)

    (project_path / ".env").write_text(
        "GREETINGS='Project created, enviroment variables working fine.'\n", encoding="utf-8"
    )

    if git:
        init_git(project_name=project_name)

    subprocess.call(["uv", "run", "main.py"], cwd=(project_path / "src"))  # noqa: S607

    if settings["open_vscode"]:
        subprocess.run(["code", str(project_name)], shell=True)  # noqa: S607, S602


if __name__ == "__main__":
    main()
