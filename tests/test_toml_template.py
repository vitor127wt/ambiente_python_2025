import json
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from tomlkit import dumps

from my_package.gitignore import template as gitignore_template
from my_package.main import (
    build_project_structure,
    dummy_settings,
    load_settings,
    open_settings,
    resolve_project_path,
)
from my_package.toml_template import create_toml


def test_create_toml_serializes_configured_source_paths() -> None:
    settings: dict[str, Any] = {
        "name": "Test User",
        "email": "test@example.com",
        "git_user": "test-user",
        "main_source_code_folder": "source",
        "main_package_name": "example_package",
        "ruff_lint_rules_select": ["E", "F"],
        "ruff_lint_rules_ignore": ["E501"],
    }

    generated = tomllib.loads(
        dumps(create_toml("3.14.3", "example-project", settings=settings))
    )

    assert generated["project"]["requires-python"] == "==3.14.3"
    assert generated["tool"]["ruff"]["target-version"] == "py314"
    assert generated["tool"]["pyright"]["include"] == ["source", "tests"]
    assert generated["tool"]["pyright"]["executionEnvironments"] == [{"root": "source"}]
    assert generated["tool"]["pytest"]["ini_options"]["pythonpath"] == ["source"]
    assert generated["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
    assert "optional-dependencies" not in generated["project"]


def test_build_project_structure_creates_importable_entrypoint(tmp_path: Path) -> None:
    project_path = tmp_path / "example-project"
    project_path.mkdir()
    settings = deepcopy(dummy_settings)

    build_project_structure(
        project_path,
        settings,
        "3.14.3",
        "example-project",
        git=False,
    )

    main_path = project_path / "src" / "main.py"
    compile(main_path.read_text(encoding="utf-8"), str(main_path), "exec")
    test_path = project_path / "tests" / "test_main.py"
    compile(test_path.read_text(encoding="utf-8"), str(test_path), "exec")
    generated = tomllib.loads((project_path / "pyproject.toml").read_text())

    assert generated["project"]["scripts"] == {"example-project": "main:main"}
    assert generated["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src",
    ]
    assert "tests/" not in gitignore_template.splitlines()


@pytest.mark.parametrize("project_name", [".", "..", "nested/project"])
def test_resolve_project_path_rejects_unsafe_names(
    tmp_path: Path, project_name: str
) -> None:
    with pytest.raises(ValueError, match="nome simples"):
        resolve_project_path(tmp_path, project_name)


def test_resolve_project_path_rejects_absolute_path(tmp_path: Path) -> None:
    absolute_path = f"{tmp_path.anchor}outside"

    with pytest.raises(ValueError, match="nome simples"):
        resolve_project_path(tmp_path, absolute_path)


def test_resolve_project_path_rejects_existing_destination(tmp_path: Path) -> None:
    project_path = tmp_path / "existing"
    project_path.mkdir()

    with pytest.raises(FileExistsError, match="já existe"):
        resolve_project_path(tmp_path, project_path.name)


def test_load_settings_migrates_old_defaults(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "name": "Personal Name",
                "create_folders": False,
                "dependencies": ["dotenv"],
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(settings_path)
    persisted = json.loads(settings_path.read_text(encoding="utf-8"))

    assert settings["name"] == "Personal Name"
    assert settings["dependencies"] == ["python-dotenv"]
    assert settings["main_source_code_folder"] == "src"
    assert "create_folders" not in settings
    assert persisted == settings


def test_load_settings_rejects_invalid_json(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON inválida"):
        load_settings(settings_path)


@pytest.mark.parametrize(
    ("platform", "expected_command"),
    [
        ("linux", ["xdg-open", "settings.json"]),
        ("darwin", ["open", "settings.json"]),
        ("win32", ["cmd", "/c", "start", "", "settings.json"]),
    ],
)
def test_open_settings_uses_platform_command(
    platform: str,
    expected_command: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("my_package.main.sys.platform", platform)

    with patch("my_package.main.subprocess.run") as run:
        open_settings(Path("settings.json"))

    run.assert_called_once_with(expected_command, check=True)
