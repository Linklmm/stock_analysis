# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chinese Stock Market AI Analysis System - A quantitative analysis platform built with Streamlit for web interface, supporting real-time market data, technical analysis, and trading simulation.

## Development Commands

### Running the Application
```bash
# Start the web application
python app.py

# Or specify custom port
python app.py --port 8502

# Or directly with streamlit
streamlit run src/web/app.py
```

### Database Setup
```bash
# Initialize MySQL database (create database and tables)
python scripts/init_database.py

# Verify database status
python scripts/init_database.py --verify

# Initialize trade calendar only (requires Tushare token)
python scripts/init_database.py --init-calendar
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_module.py

# Run with coverage
pytest --cov=src tests/
```

## Environment Setup

1. Copy `.env.example` to `.env` and configure:
   - `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` - MySQL connection
   - `TUSHARE_TOKEN` - Optional, for Tushare data source (requires API permissions)
   - Data is fetched from AkShare by default (no token required)

2. Ensure MySQL is running before initializing the database.

## Architecture

```
src/
├── core/           # Core utilities, exceptions, logging
├── data/           # Data layer
│   ├── database.py     # SQLAlchemy models and DatabaseManager
│   ├── realtime.py     # Market data fetching (AkShare/Tushare)
│   └── providers/      # Data provider implementations
├── analysis/       # Analysis modules
│   ├── technical/      # Technical indicators (MA, MACD, RSI, KDJ, Bollinger, etc.)
│   ├── prediction/     # Trend prediction models
│   ├── factors/        # Factor analysis
│   ├── backtest/       # Backtesting framework
│   └── risk/           # Risk metrics and portfolio analysis
├── models/         # ML model definitions (LightGBM, MLP, Transformer)
├── optimization/   # Portfolio optimization
├── trading/        # Trading simulation (account, order, position, broker)
└── web/            # Streamlit web application
    ├── app.py          # Main application entry
    ├── components/     # Reusable UI components (charts, tables)
    └── pages/          # Page modules
```

## Key Data Flow

1. **Data Fetching**: `src/data/realtime.py` - AkShare is primary, Tushare is backup
2. **Caching**: Data is automatically cached in MySQL. On subsequent requests, cached data is returned if available.
3. **Stock Code Format**: TS code format (e.g., `000001.SZ`, `600519.SH`). Use `normalize_stock_code()` from `src/core/utils.py` to convert user input.

## Database Models (src/data/database.py)

- `StockDaily` - Stock daily market data
- `IndexDaily` - Index daily market data
- `StockBasic` - Stock basic information
- `TradeCalendar` - Trading calendar
- `Watchlist` - User's watchlist (self-selected stocks)

Access via global `db_manager` instance.

## Important Patterns

### Logger Import
```python
from src.core.utils import logger
```

### Stock Code Normalization
```python
from src.core.utils import normalize_stock_code
code = normalize_stock_code("000001")  # Returns "000001.SZ"
```

### MySQL NaN Handling
MySQL doesn't accept NaN values. Convert before saving:
```python
df = df.where(pd.notna(df), None)
```

### Column Name Compatibility
Database returns `vol` column, some code expects `volume`. Handle both:
```python
if 'vol' in df.columns and 'volume' not in df.columns:
    df['volume'] = df['vol']
```

## Web UI (Streamlit)

- Main entry: `src/web/app.py`
- Pages are loaded via `st.switch_page()` for multi-page navigation
- Session state is used extensively for caching data and user selections
- Watchlist is managed via sidebar and quick-select buttons on main page

## Configuration

All configuration is centralized in `config/settings.py`:
- `DATABASE_CONFIG` - MySQL connection settings
- `DATA_SOURCES` - Data source priority (qlib > tushare > akshare)
- `MODELS` - ML model configurations
- `TRADING_CONFIG` - Trading simulation settings
- `TECHNICAL_INDICATORS` - Default parameters for indicators