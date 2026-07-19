#!/usr/bin/env uv run
from typing import TYPE_CHECKING, Any

from tomlkit import TOMLDocument, array, comment, document, table

if TYPE_CHECKING:
    from tomlkit.items import Table


def project_toml(project_name: str, version: str, settings: dict[Any, Any]) -> Table:
    project = table()
    urls = table()
    authors = array()
    scripts = table()

    project.add("name", project_name)
    project.add("version", "0.0.1")
    project.add("description", project_name)
    project.add("readme", "README.md")
    project.add("requires-python", f"=={version}")
    project.add("dependencies", [])

    urls.add(
        "Repository",
        f"https://github.com/{settings['git_user']}/{project_name}",
    )

    authors.append({"name": settings["name"], "email": settings["email"]})  # type: ignore

    comment_ = (
        f"Define os comandos de console. A chave ('{project_name}')\n"
        "# é o comando.\n"
        "# O valor aponta para 'nome_do_pacote.nome_do_modulo:nome_da_funcao'.\n"
        "# Ex: 'my_package.main:run'\n"
        "# -> src/my_package/main.py (e a função run lá dentro).\n"
        "# Lembre de sincronizar o nome do pacote com 'known-first-party' do Ruff"
        f"\n# {project_name} = "
        f'"{settings["main_package_name"]}.main:main"'
    )

    scripts.add(comment(comment_))
    scripts.add(
        f"{project_name}",
        f"{settings['main_package_name']}.main:main",
    )

    project.add("urls", urls)
    project.add("authors", authors)
    project.add("scripts", scripts)

    return project


def tool_ruff_toml(version: str, settings: dict[Any, Any]) -> Table:
    # Add to a tool() object

    ruff = table()
    ruff.add(
        comment(
            "============================\n# Lint e formatação (Ruff)\n# ====="
            "======================="
        )
    )
    lint = table()  # -> ruff
    format_ = table()  # -> ruff
    per_file_ignores = table()  # -> lint
    isort = table()  # -> lint
    mccabe = table()  # -> lint

    ruff.add("line-length", 88)
    ruff.add("target-version", f"py{version.replace('.', '')[:3]}")
    ruff.add("fix", True)  # noqa: FBT003
    ruff.add("show-fixes", True)  # noqa: FBT003
    ruff.add("indent-width", 4)
    ruff.add(
        "exclude",
        ["venv", ".venv", "env", ".env", "node_modules", "__pycache__"],
    )

    lint.add("fixable", ["ALL"])
    lint.add("select", settings["ruff_lint_rules_select"])
    lint.add("ignore", settings["ruff_lint_rules_ignore"])

    per_file_ignores.add("tests/**/*.py", ["ANN201", "S101"])

    format_.add("quote-style", "double")
    format_.add("indent-style", "space")
    format_.add("line-ending", "lf")

    mccabe.add("max-complexity", 12)
    isort.add(
        "known-first-party",
        [settings["main_package_name"]],
    )

    lint.add("per-file-ignores", per_file_ignores)
    lint.add("isort", isort)
    lint.add("mccabe", mccabe)
    ruff.add("lint", lint)
    ruff.add("format", format_)
    return ruff


def tool_pyright_toml(version: str, settings: dict[Any, Any]) -> Table:
    # Add to a tool() object
    pyright = table()

    pyright.add(
        comment(
            "============================\n# Tipagem (Pyright)\n# ============="
            "==============="
        )
    )
    pyright.add("typeCheckingMode", "strict")
    pyright.add("pythonVersion", f"{version}")
    pyright.add("include", [settings["main_source_code_folder"], "tests"])
    pyright.add(
        "exclude",
        [
            "**/venv",
            "**/.venv",
            "**/env",
            "**/.env",
            "**/node_modules",
            "**/__pycache__",
            "**/.*",
        ],
    )

    pyright.add("venv", ".venv")
    pyright.add("venvPath", ".")
    pyright.add(
        "executionEnvironments", [{"root": settings["main_source_code_folder"]}]
    )

    return pyright


def tool_pytest_toml(settings: dict[Any, Any]) -> Table:
    # Add to a tool() object
    pytest = table()
    ini_options = table()

    ini_options.add("addopts", "-s --color=yes --tb=short")
    ini_options.add("pythonpath", [settings["main_source_code_folder"]])
    ini_options.add("testpaths", ["tests"])

    pytest.add("ini_options", ini_options)

    return pytest


def build_system() -> Table:
    build_system = table()
    build_system.add(
        comment("============================\n# Build\n# ============================")
    )
    build_system.add("requires", ["hatchling"])  # type: ignore
    build_system.add("build-backend", "hatchling.build")

    return build_system


def hatchling(settings: dict[str, str]) -> Table:
    hatch = table()
    build = table()
    targets = table()
    wheel = table()

    # O Hatchling espera uma lista de caminhos no argumento packages
    packages_array = [
        f"{settings['main_source_code_folder']}/{settings['main_package_name']}",
    ]

    wheel.add("packages", packages_array)
    targets.add("wheel", wheel)
    build.add("targets", targets)
    hatch.add("build", build)

    return hatch


def create_toml(
    version: str, project_name: str, *, settings: dict[str, str]
) -> TOMLDocument:
    toml = document()

    toml.add(comment("============================"))
    toml.add(comment("Projeto"))
    toml.add(
        comment(
            "Referência: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"
        )
    )
    toml.add(comment("\n"))
    toml.add(comment("Instale o pacote: python-dotenv"))
    toml.add(comment("Mostrei como no README.md"))
    toml.add(comment("\n"))
    toml.add(
        comment(
            "Os pontos de atenção estão comentados próximo das chaves, aqui só coloquei um"  # noqa: E501
        )
    )
    toml.add(comment("lembrete"))
    toml.add(comment("\n"))
    toml.add(
        comment(
            "Atenção: As versões do Python devem ser consistentes entre:\n# \
                - project.requires-python\n#    \
                - tool.ruff.target-version\n#   \
                - tool.pyright.pythonVersion"
        )
    )
    toml.add(comment("\n"))
    toml.add(
        comment(
            "Atenção: O nome do pacote principal deve ser consistente entre:\n#\
                - project.scripts\n#\
                - tool.ruff.lint.isort.known-first-party\n#\
                - A pasta dentro de 'src/'"
        )
    )
    toml.add(comment("\n"))
    toml.add(
        comment(
            "Thanks = 'https://www.otaviomiranda.com.br/'\n#"
            " Thanks to Otávio Miranda for providing this template file"
        )
    )
    toml.add(comment("============================"))

    toml.add("project", project_toml(project_name, version, settings=settings))

    tool = table()

    tool.add("ruff", tool_ruff_toml(version, settings))
    tool.add("pyright", tool_pyright_toml(version, settings=settings))
    tool.add("pytest", tool_pytest_toml(settings=settings))
    tool.add("hatch", hatchling(settings=settings))

    toml.add("tool", tool)

    toml.add("build-system", build_system())
    return toml
