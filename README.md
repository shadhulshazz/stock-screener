# Stock Screener - AI-Powered Swing Trading System

A free, production-ready stock screening system for ±5–10 INR weekly moves on NIFTY 100 stocks using technical analysis, AI intelligence, and serverless deployment.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW (8:45 AM)                │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Cloud Scheduler   │
                    │ Triggers job      │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────▼─────────────────────┐
        │       Google Cloud Run                     │
        │  (Python: screener.py)                     │
        └─────────────────────┬─────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
   ┌────▼─────┐  ┌──────────────┐  ┌─────────┐    │
   │ yfinance │  │ NSE Scraper  │  │ Zerodha │    │
   │(OHLCV)   │  │(OI/PCR/FII)  │  │ Kite    │    │
   └────┬─────┘  └──────┬───────┘  └────┬────┘    │
        │               │               │         │
        └───────────────┬───────────────┘         │
                        │                         │
                ┌───────▼────────┐               │
                │ Phase 3: Filter │               │
                │ (ATR, RSI, Vol) │               │
                └───────┬────────┘               │
                        │                        │
                ┌───────▼──────────┐            │
                │ Phase 4: AI Call │            │
                │ (Claude/Groq)    │            │
                └───────┬──────────┘            │
                        │                       │
        ┌───────────────┼───────────────┐      │
        │               │               │      │
   ┌────▼─────┐  ┌─────▼─────┐  ┌──────▼───┐ │
   │ Telegram  │  │ Sheets    │  │ Local    │ │
   │ Bot       │  │ Log       │  │ JSON     │ │
   └──────────┘  └───────────┘  └──────────┘ │
                                              │
└─────────────────────��────────────────────────┘
```

## Components

1. **Data Collection** — Free APIs (yfinance, NSE scraper, Zerodha Kite)
2. **Technical Filtering** — ATR, RSI, Volume, Support/Resistance, Delivery%
3. **AI Intelligence** — Claude API / Groq for signal quality
4. **Deployment** — Google Cloud Run + Cloud Scheduler (free tier)
5. **Output** — Telegram alerts + Google Sheets logging

## Quick Start

### 1. Prerequisites
- Python 3.9+
- Google Cloud Account (free tier sufficient)
- Telegram Bot Token
- Claude or Groq API Key
- (Optional) Zerodha Kite credentials

### 2. Installation

```bash
git clone https://github.com/shadhulshazz/stock-screener.git
cd stock-screener
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
# Edit .env with your API keys and watchlist
```

### 4. Local Testing

```bash
python screener.py --test --symbols "HYUNDAI,RELIANCE,INFY"
```

### 5. Deploy to Cloud Run

```bash
./deploy.sh
```

## Features

- ✅ Free data sources (no subscriptions)
- ✅ AI-powered signal filtering
- ✅ Serverless deployment (zero maintenance)
- ✅ Real-time Telegram alerts
- ✅ Historical logging & backtesting
- ✅ Cron-based scheduling
- ✅ Production-ready error handling

## Phase Breakdown

**Phase 1:** Free data sources ✓
**Phase 2:** Python tech stack ✓
**Phase 3:** Screening logic ✓
**Phase 4:** AI prompt & API calls ✓
**Phase 5:** Stock universe (50–80 NIFTY 100) ✓
**Phase 6:** Deployment on Cloud Run ✓

## Backtesting

```bash
python backtest.py --start 2025-01-01 --end 2026-06-22 --symbols watchlist.txt
```

## Expected Output (8:45 AM Daily)

```
🎯 STOCK SCREENER ALERT — 2026-06-22

✅ TOP 5 CANDIDATES (High Confidence):
1. HYUNDAI | ₹1940 | Target: ₹1948 | SL: ₹1925 | Confidence: 87%
2. INFY | ₹1480 | Target: ₹1490 | SL: ₹1465 | Confidence: 84%
...

📊 WATCHLIST SCANNED: 75 stocks
⏱️ EXECUTION TIME: 42 seconds
```

## Documentation

- [Setup Guide](./docs/setup.md)
- [API Configuration](./docs/api-config.md)
- [Backtesting Guide](./docs/backtesting.md)
- [Deployment](./docs/deployment.md)
- [Troubleshooting](./docs/troubleshooting.md)

## Project Structure

```
stock-screener/
├── README.md
├── requirements.txt
├── .env.example
├── screener.py                 # Main screening logic
├── backtest.py                 # Historical validation
├── deploy.sh                   # Cloud Run deployment
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py        # Phase 1: Data collection
│   ├── technical_filters.py   # Phase 3: Screening logic
│   ├── ai_engine.py           # Phase 4: AI intelligence
│   ├── output_handler.py      # Telegram + Sheets integration
│   └── utils.py               # Helper functions
├── config/
│   └── watchlist.txt          # 50-80 NIFTY 100 stocks
├── docs/
│   ├── setup.md
│   ├── api-config.md
│   ├── backtesting.md
│   ├── deployment.md
│   └── troubleshooting.md
├── tests/
│   ├── test_filters.py
│   ├── test_ai_engine.py
│   └── test_data_fetcher.py
└── .github/
    └── workflows/
        ├── test.yml
        └── deploy.yml
```

## Disclaimer

This tool is for educational and research purposes. Not financial advice. Past performance ≠ future results. Always validate signals independently before trading.

## License

MIT
