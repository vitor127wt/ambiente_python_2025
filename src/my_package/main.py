import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from tomlkit import dumps

from my_package.toml_template import create_toml


def main() -> None:

    args = sys.argv
    path = Path.cwd()

    dummy_settings: dict[str, str | list[str] | dict[str, Any]] = {
        "name": "user",
        "email": "example@example.com",
        "main_package_name": "my_package",
        "git_user": "user",
        "dependencies": ["python-dotenv"],
        "dev_dependencies": ["ruff", "pyright", "pytest", "pytest-xdist"],
        "ruff_lint_rules_select": [],
        "ruff_lint_rules_ignore": ["T201", "COM812"],
        "vs_code_settings": {},
        "vs_code_extensions": {"recommendations": []},
    }
    settings_path = Path.home() / ".pproject.settings.json"

    if not settings_path.exists():
        settings_path.touch(exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(dummy_settings, f, indent=4, ensure_ascii=False)

    if len(args) < 2:
        print("Uso: pproject <nome_do_projeto>  OU  pproject -cfg")
        sys.exit(1)

    if args[1] in ["-cfg", "--config"]:
        subprocess.call(f"notepad {settings_path}")
        sys.exit(0)

    _, project_name, *left_args = args

    version = None
    for i, arg in enumerate(left_args):
        match arg:
            case "-v" | "--version":
                if i + 1 < len(left_args):
                    if left_args[i + 1] == "global":
                        version = subprocess.getoutput("python --version").split()[1]
                    if version := re.search(r"[0-9]+[.][0-9]+", left_args[i + 1]):
                        version = version.group(0)
                    else:
                        print("❌ Erro: Versão do Python inválida.")
                        sys.exit(1)
                else:
                    print("❌ Erro: Informe a versão após o parâmetro -v.")
                    sys.exit(1)
            case _:
                pass

    if version is None:
        version = subprocess.getoutput("python --version").split()[1]

    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    subprocess.call(["uv", "init", project_name, "--python", version])

    project_path = path / f"{project_name}"
    vscode_path = project_path / ".vscode"
    vscode_path.mkdir(exist_ok=True)

    vscode_settings_path = vscode_path / "settings.json"
    vscode_extensions_path = vscode_path / "extensions.json"
    with open(vscode_settings_path, "w", encoding="utf-8") as f:
        json.dump(settings["vs_code_settings"], f, indent=4)
    with open(vscode_extensions_path, "w", encoding="utf-8") as f:
        json.dump(settings["vs_code_extensions"], f, indent=4)

    package_path = project_path / f"src/{settings['main_package_name']}"
    package_path.mkdir(parents=True, exist_ok=True)

    main_file = project_path / "src/main.py"
    main_file.write_text('print("Ola Mundo")', encoding="utf-8")

    toml_path = project_path / "pyproject.toml"
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(dumps(data=create_toml(version=version, project_name=project_name, settings=settings)))

    if settings["dev_dependencies"]:
        command = ["uv", "add", "--dev", *settings["dev_dependencies"]]
        subprocess.call(command, cwd=project_name)

    if settings["dependencies"]:
        command = ["uv", "add", *settings["dependencies"]]
        subprocess.call(command, cwd=project_name)

    env_file = project_path / ".venv/.env"
    env_file.write_text("GREETINGS='hello'\n", encoding="utf-8")


if __name__ == "__main__":
    main()
