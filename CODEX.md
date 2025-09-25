# MoneyWizImport – Repository Guide for Agents

## Purpose
MoneyWizImport transforms password-protected bank statement archives into MoneyWiz-friendly OFX files. It offers two CLI entry points: one to prepare and rename raw statements (`prepare-statement`) and one to generate OFX exports (`generate-ofx`).

## Key Directories
- `src/moneywizimport/`: Core package containing CLI entry points, orchestration logic, helper utilities, and domain models.
  - `core/statement.py`: High-level workflow for preparing archives and emitting OFX content.
  - `core/ofx_generator.py`: Renders OFX XML via Jinja2 templates stored under `src/templates/ofx/`.
  - `helpers/`: Filesystem, configuration, HTML parsing, and archive utilities used across the pipeline.
  - `model/`: Typed data structures for providers, statements, OFX payloads, and configuration schemas.
- `demo/`: Sample raw and prepared statement directories used by the demo configuration.
- `ofx/`: Output folder (ignored in VCS) where generated OFX files are written.
- `statements/`: Example bank statements packaged as ZIPs for experimentation.
- `docs/`: Additional project documentation and assets.

## Configuration Flow
1. The YAML config (e.g., `src/moneywizimport/config-demo.yaml`) specifies providers, statement patterns, rename templates, and category/payee mappings.
2. `ConfigHelper` loads the config, resolves directories, and compiles regex patterns.
3. `prepare-statement` copies matching archives into a prepared directory, renaming them using metadata extracted from the HTML inside each archive.
4. `generate-ofx` groups prepared statements by provider/account/month, parses transactions and balances from the HTML, applies payee/category rules, and renders OFX files.

## Implementation Notes
- HTML parsing relies on lxml XPaths defined in `helpers/html_helper.py`.
- Archives are handled through `pyzipper` to support password-protected ZIP files.
- Offline account handling in `core.statement.add_offline_transactions` mirrors transfer transactions so MoneyWiz can reconcile linked accounts.
- Logging is centralised via `logging_setup.setup_logging` to keep CLI output consistent.
- Previous review flagged that `generate_reports` currently filters on a single hard-coded month and should iterate every group; keep an eye on this when modifying that function.

## Testing & Tooling
- No automated tests ship with the repository yet, but `poetry run pytest` is configured and should succeed (even with zero tests).
- Use `poetry run python -m compileall src` to catch syntax regressions quickly.
- Templates can be rendered with `generate-ofx`; ensure Jinja2 loaders work both from the repo root and when the package is installed.

## Getting Started
1. `poetry install`
2. `source env-demo.sh` (loads demo ZIP passwords)
3. `poetry run prepare-statement --config=src/moneywizimport/config-demo.yaml --logging=DEBUG`
4. `poetry run generate-ofx --config=src/moneywizimport/config-demo.yaml --logging=DEBUG`

These steps will populate `demo/prepared` and `ofx/` with sample outputs you can inspect while developing.
