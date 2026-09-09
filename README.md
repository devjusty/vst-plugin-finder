# VST Plugin Finder

This repository contains Windows scripts for discovering installed VST plugins and enriching the resulting CSV with plugin metadata.

## Features

- Scans common system, DAW-specific, and user plugin directories for VST2 (`.dll`) and VST3 (`.vst3`) files.
- Reports plugin type, name, path, and file size.
- Optionally uses the OpenAI API to add plugin type, developer, and notes to the CSV.
- Supports resumable, batched enrichment with progress files.

## Searched Directories

The scanner automatically looks in the following standard and DAW-specific locations:

**64-bit & 32-bit System Paths**
- `%ProgramFiles%\VSTPlugins`
- `%ProgramFiles%\Steinberg\VSTPlugins`
- `%ProgramFiles%\Common Files\VST2` (and `VST3`)
- `%ProgramFiles%\Common Files\Steinberg\VST2` (and `VST3`)
- *...and their corresponding `%ProgramFiles(x86)%` 32-bit variants.*

**DAW-specific Paths**
- **FL Studio:** `%ProgramFiles%\Image-Line\FL Studio\Plugins\VST` (and `VST3`)
- **Studio One:** `%ProgramFiles%\PreSonus\Studio One\VST` (and `VST3`)
- **Ableton Live:** `%ProgramFiles%\Ableton\Live\Plugins\VST2` (and `VST3`)

**User-specific Paths**
- `%USERPROFILE%\Documents\VST` (and `VST3`)
- `%USERPROFILE%\Documents\Audio\Plugins\VST` (and `VST3`)
- `%APPDATA%\VST` (and `VST3`)

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

### 1. Scan for Plugins

Run the PowerShell scanner to find your installed plugins. By default, it searches standard system and DAW directories and outputs a summary to the console.

```powershell
powershell -ExecutionPolicy Bypass -File .\Find-VSTPlugins.ps1
```

**Optional Parameters:**
- `-CustomPaths "C:\Path1", "D:\Path2"`: Add specific folders to the search.
- `-CustomPathsOnly`: Skip standard system directories and ONLY search your custom paths.
- `-OutputPath ".\MyPlugins.csv"`: Override the default save location.
- `-SkipVST2` / `-SkipVST3`: Skip scanning for a specific plugin format.

**Example with custom paths:**
```powershell
powershell -ExecutionPolicy Bypass -File .\Find-VSTPlugins.ps1 -CustomPaths "D:\MyVSTs" -CustomPathsOnly
```

**Expected Output:**
- A console summary of discovered VST2 and VST3 plugins.
- A CSV file written to your Desktop: `~\Desktop\VST_Plugins_List.csv` (unless `-OutputPath` is specified).

### 2. Enrich Plugin Data

To add metadata (such as developer, exact plugin type, and notes) using OpenAI, run the resumable Python enrichment script:

```powershell
uv run --with pandas --with openai --with python-dotenv .\UpdatePluginsCSV.py
```

**Expected Output:**
- Progress is logged to the console.
- `VST_Plugins_List_Progress.csv` is updated iteratively, meaning you can safely cancel and resume.
- Once complete, the final data is saved to `VST_Plugins_List_Enriched.csv`.

`UpdatePlugins.py` is an older, non-resumable enrichment script. Use it only when its one-pass behavior is intentional.

## Security

Never commit `.env` or API keys. Rotate any key previously exposed in repository history. Review generated CSV files before sharing because plugin paths can contain personal or machine-specific information.
