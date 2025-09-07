# Import Bank Statements into MoneyWiz

## Description
This tool creates CSV files from bank statements, which can then be manually imported into the [MoneyWiz](https://wiz.money) personal finance application.

MoneyWiz is a powerful personal finance app developed by SILVERWIZ LLC, available on macOS and iOS, that helps you manage accounts, budgets, transactions, and more—with features like bank syncing, automatic categorization, reports, and cloud sync via SYNCbits.  
([Wikipedia](https://en.wikipedia.org/wiki/MoneyWiz))

---

## Installation (macOS)

### 1. Update Homebrew
```bash
brew update && brew upgrade
```

### 2. Install Python
```bash
brew install python
```

Check installation:
```bash
python3 --version
```

### 3. Install Poetry
```bash
brew install poetry
```

Verify installation:
```bash
poetry --version
```

### 4. Install dependencies
From inside the project folder (where `pyproject.toml` is):
```bash
poetry install
```

This will create a virtual environment and install all required dependencies.

---

## Usage
Run the tool with Poetry:
```bash
poetry run prepare-statement
```

```bash
poetry run generate-ofx
```
---

© MoneyWiz is a registered trademark of **SILVERWIZ LLC**.  
This project is not affiliated with or endorsed by SILVERWIZ LLC.