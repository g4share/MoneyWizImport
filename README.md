# Import Bank Statements into MoneyWiz

Generate OFX files from bank statements so they can be imported into [MoneyWiz](https://wiz.money).

---

## What it does
- Combine multiple statement extracts into a single OFX file per month.
- Supported inputs:
  - ZIP archives emailed by Victoria Bank
  - ZIP archives emailed by Moldova AgroindBank
  - PDF statements exported from the **maibank** mobile app
- Output: OFX files ready for manual import into MoneyWiz.

To add support for other banks/formats, implement the needed converter/resolver pair, wire them into `RawConverterManager`/`ResolverManager`, and add the matching config entries.
- Converters create an intermediate ZIP with a consistent name.
- Resolvers parse its contents (HTML/PDF) based on the bank (e.g., Victoria Bank, MAIB).

## Requirements
- Python ≥ 3.13
- [Poetry](https://python-poetry.org/)

Install prerequisites via Homebrew (optional helper):
```bash
brew update
brew install python@3.13 poetry
```

## Environment
- Copy `env-template.sh` to `env.sh` and fill in statement ZIP passwords.
- Load it before running the CLIs:
  ```bash
  source ./env.sh
  ```

## Configuration
Split per workflow:
- `prepare-statement` uses `statements.raw` + `prepared_dir`.
- `generate-ofx` uses `prepared_dir` + `ofx_dir` + `providers` + `payees_mapping` + `offline_accounts`.

### Example `config.yaml`
```yaml
statements:
  # Destination for normalized ZIPs created by `prepare-statement`
  prepared_dir: "./statements/prepared"
  
  # Destination for OFX files created by `generate-ofx`
  ofx_dir: "./ofx"

  raw:
    # Repeat/adjust this block per bank/format you want to support
    - input_dir: "./statements/raw"

      # Regex that matches incoming statement archives under input_dir
      pattern: "^Extras din contul de card.*\\.zip$"

      # Selects the converter via label (RawConverterManager)
      label: "VB"

      # Naming pattern for the normalized archive; 
      # Placeholders resolved by the converter/resolver
      rename_template: "VB_{year}-{month}_{iban}.zip"

      # Password can come from env vars
      zip_password: ${VB_ZIP_PASSWORD}

providers:
  # Repeat/adjust this block per bank/provider
  - name: "Victoria Bank"  # Provider name written to OFX file; also used if no label is set

    # Optional; used to pick the resolver if you need a shorter alias than `name`
    label: "VB"

    # Regex that matches normalized ZIP names under prepared_dir
    filter: "^VB_(?P<year>\\d{4})-(?P<month>\\d{2})_(?P<iban>.+)\\.zip$"

    # Password applied when unzipping during OFX generation
    zip_password: ${VB_ZIP_PASSWORD}
    accounts:
      # Maps IBAN to friendly account names written to OFX file
      - name: "Secret *1111"
        iban: "MD1111111111111111111111"

# For accounts without statements: if a non-fee transaction description matches any regex below,
# the transfer is mirrored (opposite sign) into this offline account so MoneyWiz can see both sides of the transfer
# (e.g., Revolut top-ups, cash withdrawals, other banks without exported statements).
offline_accounts:
  - name: Revolut
    match:
      - REVOLUT
  - name: Wallet
    match:
      - ATM VICTORIABANK
  - name: OTP Bank Neos
    match:
      - MOBIAS NEOS

# Associates payees based on transaction description (regex search)
# Regex (re.search) → payee name; first match wins. Example: ITUNES|APPLE\.COM matches both substrings.
payees_mapping:
  - match: help\.max\.com
    name: HBO Max
  - match: ITUNES|APPLE\.COM
    name: Apple Services
```

## Quality checks
- Run tests: `poetry run pytest`
- Compile bytecode: `poetry run python -m compileall src`
- Lint: `poetry run ruff check .`

## CLI commands
- Prepare statements (renames/normalizes raw archives):
  ```bash
  poetry run prepare-statement --config=src/moneywizimport/config.yaml --logging=INFO
  ```
  | Param       | Default                          | Description                                              |
  |-------------|----------------------------------|----------------------------------------------------------|
  | `--config`  | `src/moneywizimport/config.yaml` | Path to the YAML configuration file.                     |
  | `--logging` | `INFO`                           | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`). |

- Generate OFX files:
  ```bash
  poetry run generate-ofx --config=src/moneywizimport/config.yaml --group=2025-02 --log-unmatched-payees --logging=INFO
  ```
  | Param                    | Default                          | Description                                                        |
  |--------------------------|----------------------------------|--------------------------------------------------------------------|
  | `--config`               | `src/moneywizimport/config.yaml` | Path to the YAML configuration file.                               |
  | `--group`                | _all groups_                     | Process only a specific statement group (e.g., `2025-02`).         |
  | `--log-unmatched-payees` | `false`                          | If set, logs descriptions for transactions without a mapped payee. |
  | `--logging`              | `INFO`                           | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`).           |

## Usage
- Step 1: copy statement files into `statements/raw`. Current files (as `tree statements/raw`):
  ```
  statements/raw
    ├── Extras din contul de card.zip
    ├── Extras din contul de card-2.zip
    ├── Statement_for_2025-02-01_2025-02-28.pdf
    ├── Statement_for_2025-03-01_2025-03-31.pdf
    ├── ClientReport.zip
    └── ClientReport-2.zip
  ```
- Step 2: prepare statements (normalizes/renames into `statements/prepared`):
  ```bash
  source ./env.sh && poetry run prepare-statement --logging=INFO
  ```
  Result: processed files appear in `statements/prepared` (created if missing), e.g.:
  ```
  statements/prepared
    ├── VB_2025-02_MD1111111111111111111111.zip
    ├── VB_2025-02_MD2222222222222222222222.zip
    ├── MAIB_2025-02_MD3333333333333333333333.zip
    ├── MAIB_2025-03_MD3333333333333333333333.zip
    └── MAIB_2025-04_MD3333333333333333333333.zip
  ```
- Step 3.1 (optional): verify new payees and collect unmatched entries
  ```bash
  source ./env.sh && poetry run generate-ofx --group=2025-02 --log-unmatched-payees
  ```
  Console log example (unmatched payees):
  ```
  2025-12-09 16:14:44,431 [INFO] moneywizimport.logger.unmatched_payee_logger: Unmatched payee: MOLDOVA GAZ
  2025-12-09 16:14:44,431 [INFO] moneywizimport.logger.unmatched_payee_logger: Unmatched payee: MOLDTELECOM INTERN
  2025-12-09 16:14:44,431 [INFO] moneywizimport.logger.unmatched_payee_logger: Unmatched payee: MOLDTELECOM TELEFO
  2025-12-09 16:14:44,431 [INFO] moneywizimport.logger.unmatched_payee_logger: Unmatched payee: ORACLE IRELAND
  2025-12-09 16:14:44,431 [INFO] moneywizimport.logger.unmatched_payee_logger: Unmatched payee: ORANGE
  ```
- Step 3.2 (optional): add new payees to `payees_mapping`:
  ```yaml
  payees_mapping:
    - match: MOLDOVA GAZ
      name: Moldova Gaz
    - match: MOLDTELECOM INTERN
      name: Internet
    - match: MOLDTELECOM TELEFO
      name: Telefon
    - match: ORACLE IRELAND
      name: Oracle Cloud
    - match: ORANGE
      name: Orange, Telefon
  ```
- Step 4: generate OFX for the target group:
  ```bash
  source ./env.sh && poetry run generate-ofx --group=2025-02
  ```
  OFX is created under `ofx/`, e.g.:
  ```
  ofx
    └── 2025-02.ofx
  ```
- Step 5: import the generated OFX file into MoneyWiz.

---

© MoneyWiz is a registered trademark of **SILVERWIZ LLC**.  
This project is not affiliated with or endorsed by SILVERWIZ LLC.
