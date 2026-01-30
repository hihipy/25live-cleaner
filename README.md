# 25Live Cleaner

A Python utility that transforms raw 25Live Excel exports into clean, analysis-ready data. Handles fragmented events, inconsistent formatting, and duplicate rows automatically.

------

## The Challenge

Anyone who has worked with 25Live reports knows the real work begins *after* the data is exported. The raw files are a starting point, but they come with challenges that can take hours of manual work to overcome:

- **Fragmented Events:** Overnight and multi-day events are split across multiple rows, using `cont` (continued) instead of real timestamps, which breaks any time-based analysis.
- **Inconsistent Data:** Text formatting, especially for locations and organizations, can be inconsistent, leading to errors in grouping and aggregation.
- **Duplicate Rows:** Exporting schedules for overlapping periods or from different views often results in redundant data that can skew utilization metrics.
- **Lack of Documentation:** The raw file provides no context, making it hard to trust the data or reproduce your cleaning process later.

This manual cleaning is not only time-consuming but also prone to human error, potentially compromising the integrity of your analysis.

------

## The Solution

This Python script provides a one-click solution to these challenges. It ingests one or more raw 25Live Excel files and automatically produces a clean, documented output.

The script handles all the tedious "data janitor" work, allowing you to move directly from data collection to analysis.

### Why a Standalone Python Script?

The choice of a standalone script was deliberate to make the process simple and accessible.

- **Simplicity and Speed:** There's no complex environment to manage. You can run the script by double-clicking it or with a single command. It's designed to do one job efficiently and repeatably.
- **User-Friendly GUI:** The script uses simple, familiar pop-up windows for file selection, so no interaction with the code is necessary.
- **Accessibility:** It doesn't require any specific software like Jupyter or Anaconda. Anyone with a basic Python installation can run it immediately.

------

## Features

- **User-Friendly GUI:** Pop-up windows guide you to select your input files.
- **Automated `cont` Handling:** Interprets and converts `cont` tokens into proper, continuous time intervals.
- **Smart Interval Stitching:** Merges adjacent or overnight event fragments into a single, seamless record.
- **Audit Trail:** Generates a machine-readable JSON file that documents every transformation for full reproducibility.

------

## Getting Started

### You'll Need Python

If you don't already have it, install **Python 3.10** or newer from the official [Python website](https://www.python.org/).

### Running the Cleaner

1. **Prepare Your Environment:**

   Open your terminal or command prompt, navigate to the project folder, and run the following commands to create a virtual environment and install the required packages.

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

2. **Run the Script:**

   With your virtual environment active, run the script from your terminal:

   ```bash
   python 25live_cleaner.py
   ```

3. **Select Your Input File(s):**

   A window will pop up. Navigate to and select the raw 25Live Excel file(s) (.xlsx) you want to process.

4. **Review Your Output:**

   Navigate to your computer's Downloads folder to find your analysis-ready files.

------

## Output Files

The script produces a complete package of files to support your analysis.

| File Name                          | Description                                                  |
| ---------------------------------- | ------------------------------------------------------------ |
| `25Live_cleaned_*.csv`             | **Clean Dataset.** The file to load into your analysis software (R, Python, Tableau, etc.). Contains clean data with standardized ISO 8601 datetimes. |
| `25Live_cleaned_*_audit.json`      | **Audit Log.** A machine-readable log of the entire cleaning process, including file hashes and transformation stats for full transparency and reproducibility. |

------

## License

This project is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

You are free to:
- Use, share, and adapt this work
- Use it at your job

Under these terms:
- **Attribution** — Credit the original author
- **NonCommercial** — No selling or commercial products
- **ShareAlike** — Derivatives must use the same license
