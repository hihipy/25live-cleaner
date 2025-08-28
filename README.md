# 25Live Cleaner



Hello there! If you've ever spent hours trying to make sense of 25Live’s daily Excel exports, you’re in the right place. This automated Python utility was built to take that tedious, error-prone work off your plate so you can get back to what matters: discovering insights from your space utilization data.

This script transforms raw, human-readable 25Live reports into a complete, documented, and analysis-ready package with just a few clicks.

------



## The Challenge: Why Are 25Live Exports So Hard to Work With?



Anyone who has worked with 25Live reports knows the real work begins *after* the data is exported. The raw files are a great starting point, but they come with hidden challenges that can take hours of manual work to overcome:

- **Fragmented Events:** Overnight and multi-day events are split across multiple rows, using `cont` (continued) instead of real timestamps, which breaks any time-based analysis.
- **Inconsistent Data:** Text formatting, especially for locations and organizations, can be inconsistent, leading to errors in grouping and aggregation.
- **Duplicate Rows:** Exporting schedules for overlapping periods or from different views often results in redundant data that can skew utilization metrics.
- **Lack of Documentation:** The raw file provides no context, making it hard to trust the data or reproduce your cleaning process later.

This manual cleaning is not only time-consuming but also prone to human error, potentially compromising the integrity of your entire analysis.

------



## The Solution: Your Automated Data Assistant



This Python script provides a robust, one-click solution to these challenges. It acts as an intelligent pipeline that ingests one or more raw 25Live Excel files and automatically produces a professional-grade analysis package.

The pipeline handles all the tedious "data janitor" work, allowing you to move directly from data collection to valuable analysis.



### **Why a Standalone Python Script?**



The choice of a standalone script was deliberate to make the process as simple and accessible as possible.

- **Simplicity and Speed:** There's no complex environment to manage. You can run the script by double-clicking it or with a single command. It's designed to do one job efficiently and repeatably.
- **User-Friendly GUI:** The script uses simple, familiar pop-up windows for file selection, so no interaction with the code is necessary. It's a "black box" that just works.
- **Accessibility:** It doesn't require any specific software like Jupyter or Anaconda. Anyone with a basic Python installation can run it immediately.

------



## Key Features & Benefits



- ✨ **User-Friendly GUI:** Simple pop-up windows guide you to select your input files.
- 🤖 **Automated `cont` Handling:** Intelligently interprets and converts `cont` tokens into proper, continuous time intervals.
- 🧠 **Smart Interval Stitching:** Merges adjacent or overnight event fragments into a single, seamless record.
- 📂 **All-in-One Audit Trail:** Generates a single, machine-readable JSON file that documents every transformation, ensuring full reproducibility.

------



## Getting Started: Your 5-Minute Guide





### **First, You'll Need Python**



If you don't already have it, you'll need to install **Python 3.10** or newer. You can download it from the official [Python website](https://www.python.org/).



### **Now, Let's Run the Cleaner**



1. Prepare Your Environment:

   Open your terminal or command prompt, navigate to the project folder, and run the following commands to create a virtual environment and install the required packages.

   **On macOS / Linux:**

   Bash

   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pandas numpy openpyxl
   ```

   **On Windows:**

   PowerShell

   ```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install pandas numpy openpyxl
   ```

2. Run the Pipeline:

   With your virtual environment active, run the script from your terminal:

   Bash

   ```
   python 25live_cleaner.py
   ```

3. Select Your Input File(s):

   A window will pop up. Navigate to and select the raw 25Live Excel file(s) (.xlsx) you want to process.

4. Review Your Analysis Package!

   That's it! Navigate to your computer's Downloads folder to find your complete set of analysis-ready files.

------



## The Final Product: What's in the Box? 📦



The pipeline produces a complete package of files to support every stage of your analysis.

| File Name                          | What It Is & Why You Need It                                 |
| ---------------------------------- | ------------------------------------------------------------ |
| **`25Live_cleaned_\*.csv`**        | **Your Clean Dataset.** The file to load into your analysis software (R, Python, Tableau, etc.). Contains clean data with standardized ISO 8601 datetimes. |
| **`25Live_cleaned_\*_audit.json`** | **Your Data's Receipt.** A complete, machine-readable log of the entire cleaning process, including file hashes and transformation stats for full transparency and reproducibility. |

------



## License



25Live Cleaner © 2025 – Distributed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).