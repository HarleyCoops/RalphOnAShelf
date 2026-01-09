# Repository Guidelines

## Project Structure & Module Organization
- `main.py` is the primary entry point for running the agent locally.
- `pyproject.toml` defines dependencies and tool configs (pytest, ruff, mypy).
- `README.md` explains the project goals and example usage.
- `CLAUDE.md` contains agent-specific workflow notes and commands.
- When adding reusable code, place packages under `src/` and tests under `tests/`
  to align with the build and pytest settings.

## Build, Test, and Development Commands
- `pip install -e .` installs runtime dependencies for local development.
- `pip install -e ".[dev]"` adds linting, type checking, and test tools.
- `python main.py` runs the agent entry point.
- `pytest` runs the full test suite; use `pytest -m "not integration"` to skip
  integration tests.
- `ruff check .` lints, `ruff format .` formats, and `mypy src` type-checks.

## Coding Style & Naming Conventions
- Python 3.11+; use 4-space indentation and keep lines under 100 characters.
- Follow standard naming: `snake_case` for functions/vars, `PascalCase` for
  classes, and lowercase module names.
- MCP tool names follow `mcp__<server-name>__<tool-name>` (see `CLAUDE.md`).

## Testing Guidelines
- Tests use `pytest` with `pytest-asyncio` (`asyncio_mode = auto`).
- Prefer `test_*.py` files with `test_*` functions; place fast tests in
  `tests/unit` and longer-running ones in `tests/integration`.
- Mark integration tests with `@pytest.mark.integration`.

## Commit & Pull Request Guidelines
- Git history is minimal and uses short, lowercase summaries (e.g., `quick push`);
  keep commit messages brief and descriptive.
- PRs should include a clear summary, the tests run (or “not run” with reason),
  and any configuration or dependency changes.

## Configuration & Secrets
- Set `ANTHROPIC_API_KEY` and `E2B_API_KEY` in a local `.env` file or your shell.
- Never commit secrets; if you add `.env.example`, keep it non-sensitive.
