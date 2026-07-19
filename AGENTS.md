# Repository Notes

## Project Shape

- This is a `uv`-managed project scaffolder, not the example application described by much of `README.md`.
- The `pproject` console script enters through `src/main.py` and delegates to `src/my_package/main.py`.
- Generated `pyproject.toml` content belongs in `src/my_package/toml_template.py`; generated `.gitignore` content belongs in `src/my_package/gitignore.py`. Change the templates when changing generated projects.
- Running the CLI is side-effectful: it creates `~/.pproject.settings.json`, creates a project under the current directory, runs `uv`, writes `.env`, and can initialize and commit a Git repository. Exercise it only in a temporary directory and isolate `HOME` or mock subprocesses in tests.
- The root project pins Python exactly to 3.14.3 in `.python-version`, project metadata, Pyright, and `uv.lock`, with Ruff targeting `py314`; keep them synchronized when changing Python versions.

## Commands

- Install the locked runtime and development dependencies: `uv sync`.
- Run the CLI: `uv run pproject <project-name> [-v <version|global>] [-d <pkg[,pkg...]>] [-g]`; inspect all options with `uv run pproject --help`. Open the persistent settings with `uv run pproject --config`.
- Check lint without modifying files: `uv run ruff check --no-fix .`. The configured `fix = true` means omitting `--no-fix` applies fixes.
- Check formatting: `uv run ruff format --check .`. Ruff is configured to emit CRLF line endings in this repository.
- Type-check: `uvx pyright`. Pyright is configured in `pyproject.toml` but is not a project dependency.
- Run tests: `uv run pytest`; focus with `uv run pytest tests/test_file.py::test_name`.
