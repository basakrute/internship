# CLAUDE.md - AI Assistant Guide for This Repository

## Project Overview

This is a **Python-based energy market data analysis** project focused on fetching and analyzing electricity market data from **EPIAS (Energy Exchange Istanbul)** Transparency Platform. The project uses the `eptr2` library to access Turkey's electricity market data, including PTF (Piyasa Takas Fiyati / Market Clearing Price) from the day-ahead market.

## Repository Structure

```
internship/
├── CLAUDE.md              # This file - AI assistant guide
├── README.md              # Project description
├── .gitignore             # Python-specific ignore rules
├── requirements.txt       # Python dependencies
├── ptf_fetcher.py         # Main script: fetches PTF data from EPIAS
└── ptf_multi_year.csv     # Generated output (not committed, gitignored)
```

## Tech Stack

- **Language:** Python 3.9+
- **Key Library:** [eptr2](https://github.com/Tideseed/eptr2) - EPIAS Transparency Platform v2.0 API wrapper
- **Data Processing:** pandas, matplotlib
- **Package Manager:** pip

## Setup & Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Credentials / Authentication

**IMPORTANT:** This project uses interactive credential input (via `input()` / `getpass`). Users are prompted for their EPIAS username and password at runtime. Credentials are **never** stored in files, environment variables, or committed to the repository.

Users must register at [EPIAS Transparency Platform](https://seffaflik.epias.com.tr/) to get credentials.

## Running the Project

```bash
python ptf_fetcher.py
```

The script will:
1. Prompt for EPIAS username and password
2. Fetch PTF (Market Clearing Price) data year-by-year from EPIAS
3. Save combined data to `ptf_multi_year.csv`
4. Display basic statistics and data summary

## Key Conventions

### Code Style
- Python scripts use standard PEP 8 conventions
- Turkish comments are used alongside English function/variable names
- Data column names may be in Turkish (from EPIAS API responses)

### Data Handling
- Date ranges are fetched year-by-year to avoid API timeouts
- The `eptr2` library returns pandas DataFrames
- Output CSVs are generated in the project root directory

### Security
- **Never** commit credentials or `.env` files
- **Never** hardcode usernames or passwords
- Always use interactive input (`getpass`) for sensitive data
- The `.gitignore` already excludes `.env`, `.envrc`, and common secret files

### Dependencies
- All dependencies are listed in `requirements.txt`
- Use `pip install -r requirements.txt` to install
- The `eptr2[allextras]` package includes pandas and extra utilities

## eptr2 API Quick Reference

```python
from eptr2 import EPTR2

# Initialize with credentials
eptr = EPTR2(username="user@example.com", password="password")

# Fetch Market Clearing Price (PTF)
df = eptr.call("mcp", start_date="2024-01-01", end_date="2024-12-31")
# Alias: eptr.call("ptf", ...)

# List all available API calls (213+ endpoints)
eptr.get_available_calls()
eptr.get_available_calls(include_aliases=True)
```

## Git Workflow

- **Main branch:** `master`
- Feature branches use the `claude/` prefix
- Commit messages should be clear and descriptive
- Do not commit generated data files (CSVs) or credentials

## Common Issues

- **eptr2 not installed:** Run `pip install "eptr2[allextras]"`
- **Authentication errors:** Verify EPIAS credentials at https://seffaflik.epias.com.tr/
- **No data returned:** Check date ranges and API endpoint names. Use `eptr.get_available_calls()` to verify available endpoints
- **API rate limiting:** The eptr2 library supports TGT recycling to minimize authentication calls
