# MoneyWizImport Contribution Rules

This file applies to the entire repository.

## Development workflow
- Use Python 3.13 or newer and install dependencies with `poetry install` before running any commands.
- Keep the codebase type hinted and prefer standard library logging utilities over print statements.
- Preserve existing logging semantics—raise the logging level only when strictly necessary.
- When you touch configuration or template files, describe the runtime effect in the commit message or PR description.

## Testing requirements
- After making changes, run `poetry run pytest` (even if it reports "no tests collected") to ensure the test runner still succeeds.
- For CLI-related work, also run `poetry run python -m compileall src` to catch syntax errors early.
- Include the exact commands and their results in your final report.

## Git & documentation
- Keep commits focused; do not mix unrelated refactors with functional changes.
- Update README or docs when behaviour, inputs, or outputs change.
- Prefer Markdown tables or bullet lists for new documentation so they render clearly.
