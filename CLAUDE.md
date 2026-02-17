# CLAUDE.md - AI Assistant Guide

## Project Overview

**PTF (Market Clearing Price) Analysis & Forecasting** for KocSistem Renewable Energy Solutions internship (IE400). Fetches Turkey's electricity day-ahead market data from EPIAS, performs duck curve analysis, and builds Prophet time-series forecasting models.

## Repository Structure

```
internship/
├── CLAUDE.md              # AI assistant guide
├── README.md              # Project description
├── .gitignore             # Python gitignore + *.csv
├── requirements.txt       # Python dependencies
├── ptf_fetcher.py         # Main script: fetch, analyze, forecast
└── (generated outputs)    # CSV + PNG files (gitignored)
```

## Tech Stack

- **Language:** Python 3.9+
- **Data Source:** [eptr2](https://github.com/Tideseed/eptr2) - EPIAS Transparency Platform v2.0 API
- **Analysis:** pandas, numpy, matplotlib
- **Forecasting:** Prophet (Facebook), scikit-learn
- **Package Manager:** pip

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python ptf_fetcher.py
```

The script prompts for EPIAS credentials interactively (never stored). It then:
1. Fetches PTF data year-by-year (2021-2026) from EPIAS
2. Generates duck curve visualizations (yearly, seasonal, weekday/weekend)
3. Computes arbitrage spread analysis
4. Prints yearly statistics table
5. Trains Prophet model (80/20 split) and reports MAE/RMSE/MAPE
6. Generates 30-day forecast

## Generated Output Files

| File | Description |
|---|---|
| `ptf_2021_2026.csv` | Raw hourly PTF data |
| `duck_curve_by_year.png` | Yearly duck curve comparison |
| `duck_curve_seasonal.png` | Seasonal duck curve (2025) |
| `duck_curve_weekday_weekend.png` | Weekday vs weekend pattern |
| `ptf_monthly_heatmap.png` | Monthly average PTF heatmap |
| `prophet_components.png` | Prophet trend + seasonality decomposition |
| `prophet_actual_vs_predicted.png` | Forecast accuracy (last 14 days) |
| `prophet_30day_forecast.png` | 30-day future forecast |

## Key Conventions

- **Credentials:** Interactive input only (`input()` + `getpass`). Never env vars, never `.env` files.
- **API endpoint:** Use `eptr.call("mcp", ...)` for PTF data. `"ptf"` is an alias for `"mcp"`.
- **Code style:** PEP 8. Turkish user-facing output, English code/variable names.
- **Plots:** Consistent theme via `setup_plot_style()`. All saved as PNG, then `plt.close()`.
- **Git:** Never commit CSVs, PNGs, or credentials. Main branch: `master`.

## eptr2 Quick Reference

```python
from eptr2 import EPTR2
eptr = EPTR2(username="email", password="pass")
df = eptr.call("mcp", start_date="2024-01-01", end_date="2024-12-31")
eptr.get_available_calls(include_aliases=True)  # 213+ endpoints
```
