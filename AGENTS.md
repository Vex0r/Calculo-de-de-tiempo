# Repository Guidelines

## Project Structure & Module Organization
- `src/fecha_contador/` holds the Python package with the CLI, TUI, models, storage, and business logic.
- `data/important_dates.json` stores persisted dates in a readable JSON format.
- `run_cli.py` and `run_ui.py` are entry points for the command-line and interactive console modes.

## Build, Test, and Development Commands
- `python run_ui.py` launches the interactive TUI.
- `python run_cli.py list` lists upcoming dates by default; add `--all` to include past dates.
- `python run_cli.py add --name "Event" --date "YYYY-MM-DD"` adds a new date.
- The CLI runs with Python 3.8+ only; the TUI requires `questionary` and `rich`.
  - Install TUI deps with: `python -m pip install questionary rich`

## Coding Style & Naming Conventions
- Use 4-space indentation and standard Python formatting.
- Prefer `snake_case` for functions, variables, and file names; keep module names short.
- Keep user-facing strings in Spanish to match existing CLI/TUI text.
- Inline comments are used sparingly to clarify intent; avoid redundant commentary.

## Testing Guidelines
- There is no test framework configured yet.
- When adding tests, place them under `tests/` using `test_*.py` naming.
- Run manual smoke checks by adding, listing, and removing a date in both CLI and TUI modes.

## Commit & Pull Request Guidelines
- Commit messages are plain Spanish sentences describing the change (no prefixes), e.g., "Se agrego la opcion de eliminar fecha".
- Keep commits focused and update README examples if command behavior changes.
- Pull requests should include: a short summary, steps to verify, and screenshots or GIFs for UI/TUI changes.

## Data & Configuration Notes
- The JSON data file contains user dates; avoid committing personal or sensitive data.
- The CLI stores data in `data/important_dates.json` relative to the directory where you run the command.
- If you change the JSON schema, document the migration in `README.md`.

## Roles & Responsibilities
- **Ingeniero de documentación (Documentación):** Actualiza `README.md` y `AGENTS.md` para reflejar nuevos comandos, flags o mejoras del flujo; incluye ejemplos de uso claros, pasos para reproducir cambios y mantén un tono instructivo. Verifica que las instrucciones en español sigan el estilo actual y añade una nota breve cuando un cambio necesita nuevos recursos (capturas, gifs) para demostrar la UX.
- **Gestor de Control de Versiones (Commits):** Maneja los commits de cada archivo al finalizar cada sesión. Su responsabilidad es revisar las mejoras e implementaciones realizadas en los archivos y generar los comandos `git add` y `git commit` correspondientes, asegurando que los mensajes de commit sigan las directrices de "Commit & Pull Request Guidelines" y describan con precisión el trabajo realizado.
