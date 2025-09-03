# MoneyWizImport Contribution Rules

This file applies to the entire repository.
Use it together with `CODEX.md`, which explains the repo layout and workflows at a high level.

## Development workflow
- Use Python 3.13 or newer and install dependencies with `poetry install` before running any commands.
- Keep the codebase type hinted and prefer standard library logging utilities over print statements.
- Preserve existing logging semantics—raise the logging level only when strictly necessary.
- When you touch configuration or template files, describe the runtime effect in the commit message or PR description.

## Testing requirements
- After making changes, run:
  - `poetry run pytest` (even if it reports "no tests collected")
  - `poetry run python -m compileall src` (for CLI-related work)
  - `poetry run ruff check .`
- Prefer parametrized tests and group tests by functionality (not by file under test).
- Include the exact commands and their results in your final report.

## Git & documentation
- Keep commits focused; do not mix unrelated refactors with functional changes.
- Update README or docs when behaviour, inputs, or outputs change.
- Prefer Markdown tables or bullet lists for new documentation so they render clearly.
