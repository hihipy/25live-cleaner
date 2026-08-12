# 25Live Cleaner

[![Link Check](https://github.com/hihipy/25live-cleaner/actions/workflows/links.yml/badge.svg)](https://github.com/hihipy/25live-cleaner/actions/workflows/links.yml)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

**Built with**

[![numpy](https://img.shields.io/badge/numpy-013243?style=flat&logo=numpy&logoColor=white)](https://numpy.org)
[![openpyxl](https://img.shields.io/badge/openpyxl-2E7D32?style=flat&logoColor=white)](https://openpyxl.readthedocs.io)
[![pandas](https://img.shields.io/badge/pandas-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)

A Python utility that turns raw 25Live Excel exports into clean, analysis-ready data. It handles fragmented events, inconsistent formatting, and duplicate rows automatically.

---

## The Problem

Anyone who has worked with 25Live reports knows the real work begins *after* the data is exported. The raw files are a starting point, but they come with a few recurring problems:

- **Fragmented events:** Overnight and multi-day events get split across multiple rows, using `cont` (continued) instead of real timestamps, which breaks any time-based analysis.
- **Inconsistent data:** Text formatting, especially for locations and organizations, is often inconsistent, which causes errors when grouping and aggregating.
- **Duplicate rows:** Exporting schedules for overlapping periods or from different views tends to produce redundant rows that skew utilization metrics.
- **No documentation:** The raw file gives you no context, so it's hard to trust the data or reproduce your cleaning steps later.

Doing this by hand takes time, and it's easy to introduce mistakes that compromise the analysis.

---

## The Solution

This script takes one or more raw 25Live Excel files and produces clean, documented output. It handles the tedious data-janitor work so you can go straight from collecting data to analyzing it.

### Why a Standalone Python Script?

A standalone script keeps things simple and accessible.

- **Simple and fast:** No environment to manage. Run it by double-clicking or with a single command. It does one job and does it repeatably.
- **Familiar GUI:** It uses standard pop-up windows for file selection, so you never have to touch the code.
- **Accessible:** No need for Jupyter, Anaconda, or anything special. A basic Python installation is enough.

---

## Features

- **Pop-up file selection:** Windows guide you to choose your input files.
- **Automated `cont` handling:** Interprets and converts `cont` tokens into proper, continuous time intervals.
- **Interval stitching:** Merges adjacent or overnight event fragments into a single record.
- **Audit trail:** Generates a machine-readable JSON file that documents every transformation, so the process is reproducible.

---

## Getting Started

### You'll Need Python

If you don't already have it, install **Python 3.10** or newer from the official [Python website](https://www.python.org/).

### Running the Cleaner

1. **Set up your environment:**

   Open your terminal or command prompt, navigate to the project folder, and run the following to create a virtual environment and install the required packages.

   **macOS / Linux:**

```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pandas numpy openpyxl
```

   **Windows:**

```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install pandas numpy openpyxl
```

2. **Run the script:**

   With your virtual environment active, run it from your terminal:

```bash
   python cleaner_25live.py
```

3. **Select your input file(s):**

   A window will pop up. Navigate to and select the raw 25Live Excel file(s) (.xlsx) you want to process.

4. **Review your output:**

   Check your Downloads folder for the finished files.

---

## Output Files

The script produces two files:

| File Name                          | Description                                                  |
| ---------------------------------- | ------------------------------------------------------------ |
| `25Live_cleaned_*.csv`             | The cleaned dataset to load into your analysis software (R, Python, Tableau, etc.). Contains standardized ISO 8601 datetimes. |
| `25Live_cleaned_*_audit.json`      | A machine-readable log of the cleaning process, including file hashes and transformation stats, so the run is transparent and reproducible. |

---

## License

This project is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

You are free to:
- Use, share, and adapt this work
- Use it at your job

Under these terms:
- **Attribution:** Credit the original author
- **NonCommercial:** No selling or commercial products
- **ShareAlike:** Derivatives must use the same license
