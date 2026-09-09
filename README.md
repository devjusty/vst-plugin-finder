# VST Plugin Finder

This repository contains Windows scripts for discovering installed VST plugins and enriching the resulting CSV with plugin metadata.

## Features

- Scans common system, DAW-specific, and user plugin directories for VST2 (`.dll`) and VST3 (`.vst3`) files.
- Reports plugin type, name, path, and file size.
- Optionally uses the OpenAI API to add plugin type, developer, and notes to the CSV.
- Supports resumable, batched enrichment with progress files.

## Requirements

- Windows PowerShell
- Python 3
- `uv` for running the Python scripts with dependencies
- An OpenAI API key for enrichment

The Python scripts use `pandas`, `openai`, and `python-dotenv`.

## Setup

Create a local environment file from the example and add a newly issued API key:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set `OPENAI_API_KEY` in `.env`. The file is ignored by Git and must never be committed.

## Usage

Scan the computer for installed plugins:

```powershell
powershell -ExecutionPolicy Bypass -File .\Find-VSTPlugins.ps1
```

The scanner writes `VST_Plugins_List.csv` to the current user's Desktop.

For recommended resumable enrichment, run:

```powershell
uv run --with pandas --with openai --with python-dotenv .\UpdatePluginsCSV.py
```

This reads `VST_Plugins_List.csv`, saves item-level progress to `VST_Plugins_List_Progress.csv`, and writes the completed data to `VST_Plugins_List_Enriched.csv`.

`UpdatePlugins.py` is an older, non-resumable enrichment script. Use it only when its one-pass behavior is intentional.

## Security

Never commit `.env` or API keys. Rotate any key previously exposed in repository history. Review generated CSV files before sharing because plugin paths can contain personal or machine-specific information.
