.PHONY: install clean

install:
	poetry install

activate-message:
	@echo "Poetry installed dependencies and created a venv at .venv"
	@echo ""
	@echo "Activate the venv:"
	@echo "  Bash / WSL / Git-Bash:    source .venv/bin/activate"
	@echo "  Windows PowerShell:       .\\.venv\\Scripts\\Activate.ps1"
	@echo "  Windows cmd.exe:          .\\.venv\\Scripts\\activate.bat"

clean:
	@command -v poetry >/dev/null 2>&1 && poetry env remove --path 2>/dev/null || true
	@rm -rf .venv