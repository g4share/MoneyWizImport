# MoneyWizImport – Repository Guide for Agents

This file is for day-to-day navigation and context. For contribution rules (tooling, testing, logging, etc.), see `AGENTS.md` which is enforced across the repository.

## Purpose
MoneyWizImport transforms password-protected bank statement archives into MoneyWiz-friendly OFX files. It offers two CLI entry points: one to prepare and rename raw statements (`prepare-statement`) and one to generate OFX exports (`generate-ofx`).

## Key Directories
- `src/moneywizimport/`: Core package containing CLI entry points, orchestration logic, helper utilities, and domain models.
  - `core/statement.py`: High-level workflow for preparing archives and emitting OFX content.
  - `core/ofx_generator.py`: Renders OFX XML via Jinja2 templates stored under `src/moneywizimport/templates/ofx/`.
  - `helpers/`: Filesystem, configuration, HTML parsing, and archive utilities used across the pipeline.
  - `model/`: Typed data structures for providers, statements, OFX payloads, and configuration schemas.
- `ofx/`: Output folder (ignored in VCS) where generated OFX files are written.
- `statements/raw`: Drop incoming archives/PDFs here; `prepare-statement` renames and moves them.
- `statements/prepared`: Normalised archives produced by `prepare-statement`.
- `docs/`: Additional project documentation and assets.

## Configuration Flow
1. The YAML config (e.g., `src/moneywizimport/config.yaml`) specifies providers, statement patterns, rename templates, and payee mappings.
2. `ConfigHelper` loads the config, resolves directories, and compiles regex patterns.
3. `prepare-statement` copies matching archives into a prepared directory, renaming them using metadata extracted from the HTML inside each archive.
4. `generate-ofx` groups prepared statements by provider/account/month, parses transactions and balances from the HTML, applies payee/category rules, and renders OFX files.

## Implementation Notes
- HTML parsing relies on lxml XPaths defined in `helpers/html_helper.py`.
- Archives are handled through `pyzipper` to support password-protected ZIP files.
- Offline account handling in `core.statement.add_offline_transactions` mirrors transfer transactions so MoneyWiz can reconcile linked accounts.
- Logging is centralised via `logging_setup.setup_logging` to keep CLI output consistent.

## Testing & Tooling
- Tests live under `tests/`; run `poetry run pytest`.
- Use `poetry run python -m compileall src` to catch syntax regressions quickly.
- Lint with `poetry run ruff check .` (see AGENTS.md for required commands after changes).
- Templates can be rendered with `generate-ofx`; ensure Jinja2 loaders work both from the repo root and when the package is installed.

## Getting Started
1. `poetry install`
2. `source env-template.sh` or your local `env.sh` (loads ZIP/PDF passwords)
3. `poetry run prepare-statement --config=src/moneywizimport/config.yaml --logging=INFO`
4. `poetry run generate-ofx --config=src/moneywizimport/config.yaml --group=2025-02 --log-unmatched-payees --logging=INFO`

These steps will populate `statements/prepared` and `ofx/` with outputs you can inspect while developing.
