# LocalAI CLI Sprint 1 Automation & Usage

## Automated Sprint 1 Checklist

To automate the Sprint 1 checklist, run the following PowerShell script from the project root:

```powershell
./sprint1_automation.ps1
```

This script will:

- Install dependencies (using Poetry or pip)
- Run all unit tests with pytest
- Run a manual smoke test:
  - `python main.py init demo-svc`
  - `python main.py run demo-svc --watch`
  - Edits `workspace/demo-svc/src/app.js` to trigger auto-restart

> **Note:**
>
> - Ensure you have Python 3.11, Poetry (if using pyproject.toml), and pip installed.
> - The script requires PowerShell (pwsh.exe) on Windows.

## Manual Run Command Syntax

- **Initialize a service:**
  ```powershell
  python main.py init <service-name>
  ```
- **Run a service with file watching:**
  ```powershell
  python main.py run <service-name> --watch
  ```

### Requirements

- `watchdog` (Python, for file watching)
- `nodemon` (optional, for Node.js projects)
- `pytest` (for running tests)

Install Python dependencies with:

```powershell
pip install -r requirements.txt
```

Or, if using Poetry:

```powershell
poetry install
```

---

For more details, see the script `sprint1_automation.ps1` in the project root.
