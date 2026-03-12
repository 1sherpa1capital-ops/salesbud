# Plan: Refactoring SalesBud to use TOON format

The goal of this refactor is to transition the SalesBud CLI's machine-readable format from JSON to TOON (Token-Oriented Object Notation). TOON is optimized for AI agents, drastically reducing token usage while remaining easily parsable.

## 1. Dependency Updates
* Run `uv add toon-format` in the project root to install the TOON parser.
* Optionally install the subset required, e.g. `uv add "toon-format[openai]"` if needed.

## 2. Refactor Codebase (`src/salesbud/`)
* **`main.py`**:
  * Replace the `import json` statement with `import toon` (or from `toon_format` import `dumps`, depending on library specs).
  * Refactor all argparse arguments from `--json` to `--toon`. Ensure variable flags flip from `use_json` to `use_toon`.
  * Update the `print_json()` utility to `print_toon()`. This function will output data serialized via TOON rather than `json.dumps()`.
  * Update the `icp.json` handling at the top of the `scrape` and `workflow` commands to parse `icp.toon` using the TOON library `loads` or `decode` method.
* **`scripts/prod_check.py`**:
  * Any mocked tests checking for `--json` outputs will need their arguments updated.

## 3. Update Documentation
* **`AGENTS.md`**: Update all `--json` command references to `--toon`. Document the payload schema changes.
* **`docs/current/PRD.md`**: Update exit codes and machine-readable output schemas to TOON.
* **`docs/current/SPEC.md`**: Adjust CLI inputs/outputs and parsing instructions to denote TOON formatting.
* **`changelog.md`**: Add an implementation note on the shift from JSON to TOON to optimize LLM tooling and token consumption.
* **`task.md`**: Overwrite with corresponding checkboxes for these exact tasks.

## 4. Verification
* Test `uv run python -m salesbud status --toon` manually to observe the serialized TOON format.
* Check the parser logic correctly validates inputs with `--toon` enabled.
