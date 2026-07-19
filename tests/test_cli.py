import sys
from pathlib import Path  # noqa: TC003

import pytest

from my_package.main import current_python_version, main, parse_args


def test_parse_args_preserves_full_version_and_dependencies() -> None:
    options = parse_args(
        [
            "pproject",
            "example",
            "--version",
            "3.14.3",
            "--dependency",
            "requests, rich",
            "-d",
            "httpx",
            "--git",
        ]
    )

    assert options.project_name == "example"
    assert options.version == "3.14.3"
    assert options.dependencies == ["requests", "rich", "httpx"]
    assert options.git is True
    assert options.config is False


def test_parse_args_resolves_global_to_running_python() -> None:
    options = parse_args(["pproject", "example", "-v", "global"])

    assert options.version == current_python_version()
    assert options.version == (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


@pytest.mark.parametrize(
    "args",
    [
        ["pproject"],
        ["pproject", "example", "--unknown"],
        ["pproject", "example", "-v", "3.14.invalid"],
        ["pproject", "example", "-d", "requests,,rich"],
        ["pproject", "example", "-d", "-g"],
        ["pproject", "example", "--config"],
        ["pproject", "--config", "--version", "3.14.3"],
    ],
)
def test_parse_args_rejects_invalid_combinations(args: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        parse_args(args)

    assert error.value.code == 2


def test_help_does_not_create_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    with pytest.raises(SystemExit) as error:
        main(["pproject", "--help"], tmp_path)

    assert error.value.code == 0
    assert not (home / ".pproject.settings.json").exists()


def test_invalid_destination_does_not_create_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    existing_project = tmp_path / "existing"
    existing_project.mkdir()
    monkeypatch.setenv("HOME", str(home))

    with pytest.raises(SystemExit) as error:
        main(["pproject", existing_project.name], tmp_path)

    assert error.value.code == 1
    assert not (home / ".pproject.settings.json").exists()
