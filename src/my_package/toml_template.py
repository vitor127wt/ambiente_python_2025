from tomlkit import TOMLDocument, array, comment, document, inline_table, table


def create_toml(
    version: str,
    project_name: str,
    *,
    settings: dict[str, str],
) -> TOMLDocument:
    toml = document()
    toml.add(
        comment(
            """============================\n# Projeto\n# Referência: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/\n# \n# Instale o pacote: python-dotenv\n# Mostrei como no README.md\n# \n# Os pontos de atenção estão comentados próximo das chaves, aqui só coloquei um\n# lembrete.\n# \n# Atenção: As versões do Python devem ser consistentes entre:\n#     - project.requires-python\n#     - tool.ruff.target-version\n#     - tool.pyright.pythonVersion\n# \n# Atenção: O nome do pacote principal deve ser consistente entre:\n#     - project.scripts\n#     - tool.ruff.lint.isort.known-first-party\n#     - A pasta dentro de 'src/'\n# \n# Thanks = "https://www.otaviomiranda.com.br/"\n# Thanks to Otávio Miranda for providing this template file\n# ============================"""
        )
    )

    project = table()

    project.add("name", project_name)
    project.add("version", "0.0.1")
    project.add("description", project_name)
    project.add("readme", "README.md")
    project.add("authors", [{"name": f"{settings['name']}", "email": f"{settings['email']}"}])
    project.add("requires-python", f">={version}")
    project.add("dependencies", [])

    toml.add("project", project)

    project_urls = table()

    project_urls.add("Repository", f"https://github.com/{settings['git_user']}/{project_name}")

    toml.add("project.urls", project_urls)

    project_scripts = table()
    toml.add("project.scripts", project_scripts)

    toml.add(
        comment(
            f'''Define os comandos de console. A chave ('{project_name}') é o comando.\n# O valor aponta para 'nome_do_pacote.nome_do_modulo:nome_da_funcao'.\n# Ex: 'my_package.main:run' -> src/my_package/main.py (e a função run lá dentro).\n# Lembre-se de sincronizar o nome do pacote com 'known-first-party' do Ruff.\n# {project_name} = "{settings["main_package_name"]}.my_module:function"'''
        )
    )

    toml.add(comment("""============================\n# Lint e formatação (Ruff)\n# ============================"""))
    tool_ruff = table()
    tool_ruff.add("line-length", 80)
    tool_ruff.add("target-version", f"py{version.replace('.', '')[:3]}")
    tool_ruff.add("fix", True)
    tool_ruff.add("show-fixes", True)
    tool_ruff.add("indent-width", 4)
    tool_ruff.add("exclude", array(f"{['venv', '.venv', 'env', '.env', 'node_modules', '__pycache__']}"))

    toml.add("tool.ruff", tool_ruff)

    if not settings["ruff_lint_rules_select"]:
        ruff_rules_lint_select = f"{
            [
                'ASYNC',
                'A',
                'ANN',
                'B',
                'BLE',
                'C4',
                'C90',
                'COM',
                'E',
                'EM',
                'ERA',
                'EXE',
                'F',
                'FBT',
                'FIX',
                'I',
                'ICN',
                'ISC',
                'Q',
                'RET',
                'RSE',
                'S',
                'SIM',
                'SLF',
                'T10',
                'T20',
                'TC',
                'TD',
                'TRY',
                'UP',
                'W',
                'YTT',
                'RUF',
                'N',
            ]
        }"
    else:
        ruff_rules_lint_select = settings["ruff_lint_rules_select"]
    tool_ruff_lint = table()
    tool_ruff_lint.add("select", ruff_rules_lint_select)
    tool_ruff_lint.add("ignore", settings["ruff_lint_rules_ignore"])
    toml.add("tool.ruff.lint", tool_ruff_lint)

    tool_ruff_lint_per_file_ignores = table()
    tool_ruff_lint_per_file_ignores.add("tests/**/*.py", array(f"{['ANN201', 'S101']}"))

    toml.add("tool.ruff.lint.per-file-ignores", tool_ruff_lint_per_file_ignores)

    tool_ruff_format = table()

    tool_ruff_format.add("quote-style", "double")
    tool_ruff_format.add("indent-style", "space")
    tool_ruff_format.add("line-ending", "cr-lf")

    toml.add("tool.ruff.format", tool_ruff_format)

    tool_ruff_lint_isort = table()

    toml.add(
        comment(
            """Ensina ao Ruff qual é o pacote principal do seu projeto.\n# Deve ser o mesmo nome da pasta dentro de 'src/'."""
        )
    )
    tool_ruff_lint_isort.add("known-first-party", array(f"{['my_package']}"))

    toml.add("tool.ruff.lint.isort", tool_ruff_lint_isort)

    toml.add(comment("""============================\n# Tipagem (Pyright)\n# ============================"""))
    tool_pyright = table()

    tool_pyright.add("typeCheckingMode", "strict")
    tool_pyright.add("pythonVersion", f"{version}")
    tool_pyright.add("include", array(f"{['src', 'tests']}"))
    tool_pyright.add(
        "exclude",
        array(
            f"{
                [
                    '**/venv',
                    '**/.venv',
                    '**/env',
                    '**/.env',
                    '**/node_modules',
                    '**/__pycache__',
                    '**/.*',
                ]
            }"
        ),
    )
    tool_pyright.add("venv", ".venv")
    tool_pyright.add("venvPath", ".")
    tool_pyright.add("executionEnvironments", r'[{ root = "src" }]')

    toml.add("tool.pyright", tool_pyright)
    toml.add(comment("""============================\n# Testes (Pytest)\n# ============================ """))
    tool_pytest_ini_options = table()

    tool_pytest_ini_options.add("addopts", "-s --color=yes --tb=short")
    tool_pytest_ini_options.add("pythonpath", array(f"{['src']}"))
    tool_pytest_ini_options.add("testpath", array(f"{['tests']}"))

    toml.add("tool.pytest.ini_options", tool_pytest_ini_options)

    toml.add(comment("""============================\n# Build e Setuptools\n# ============================"""))
    build_system = table()

    build_system.add("requires", array(f"{['setuptools', 'wheel']}"))
    build_system.add("build-backend", "setuptools.build_meta")

    toml.add("build-system", build_system)

    tool_setuptools_packages_find = table()

    tool_setuptools_packages_find.add("where", array(f"{['src']}"))

    toml.add(
        comment(
            """Informa ao setuptools para encontrar os pacotes dentro da pasta 'src'.\n# Essencial para a estrutura de layout com 'src/'."""
        )
    )
    toml.add("tool.setuptools.packages.find", tool_setuptools_packages_find)

    tool_setuptools = table()

    tool_setuptools.add("package-dir", inline_table().append("", "src"))

    toml.add("tool.setuptools", tool_setuptools)

    return toml
