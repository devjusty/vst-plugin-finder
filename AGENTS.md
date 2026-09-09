# Repository Guidelines

## Project Structure & Module Organization

This repository is a small, script-based Windows utility:

- `Find-VSTPlugins.ps1` scans common system and user plugin folders for VST2 (`.dll`) and VST3 (`.vst3`) files and exports a report.
- `UpdatePlugins.py` and `UpdatePluginsCSV.py` enrich `VST_Plugins_List.csv` with plugin type, developer, and notes using the OpenAI API. The latter supports resumable progress and batching.

There is currently no dedicated source, test, or asset directory.

## Build, Test, and Development Commands

Run the scanner from the repository root in PowerShell:

```powershell
 powershell -ExecutionPolicy Bypass -File .\Find-VSTPlugins.ps1
```

Run CSV enrichment after installing the required Python packages (`pandas`, `openai`, and `python-dotenv`) and creating `.env` from `.env.example`:

```powershell
uv run --with pandas --with openai --with python-dotenv .\UpdatePluginsCSV.py
```

There is no build step or automated test suite. Validate scanner changes with a controlled plugin directory or by reviewing the generated CSV and summary counts.

## Coding Style & Naming Conventions

Use four-space indentation, descriptive names, and comments only where they clarify behavior. Keep PowerShell variables and functions in approved PowerShell casing (`$searchPaths`, `Test-VSTPlugin`); use `snake_case` for Python functions and variables. Preserve CSV column names and output formats unless a change is intentional and documented.

## Testing Guidelines

No testing framework or coverage requirement is configured. For changes, run the affected script with representative input, verify exit behavior and output columns, and avoid committing machine-specific paths or generated results unintentionally.

## Commit & Pull Request Guidelines

Git history currently contains only an `initial commit`, so no established message convention is available. Use short imperative messages, for example `Improve VST3 discovery`. Pull requests should explain the behavior change, list validation commands and results, identify generated-file changes, and include sample output or screenshots when output formatting changes.

## Security & Configuration

Never commit API keys or other credentials. Copy `.env.example` to `.env`, set `OPENAI_API_KEY`, and keep `.env` untracked. Rotate any key that has been exposed in repository history before running enrichment. Treat plugin paths and generated CSV contents as local-machine data; inspect diffs for accidental personal information.
