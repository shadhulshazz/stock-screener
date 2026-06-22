"""
Utility functions
"""

import os
import logging
from datetime import datetime
from pytz import timezone

# Setup logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("screener.log"),
        ],
    )
    
    return logging.getLogger(__name__)


def is_market_open() -> bool:
    """Check if NSE market is currently open"""
    ist = timezone("Asia/Kolkata")
    now = datetime.now(ist)
    
    # Market hours: 9:15 AM to 3:30 PM on weekdays
    if now.weekday() >= 4:  # Friday = 4, Saturday = 5, Sunday = 6
        return False
    
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def format_currency(value: float) -> str:
    """Format value as Indian currency"""
    return f"₹{value:,.2f}"


def load_watchlist(filepath: str) -> list:
    """Load watchlist from file"""
    try:
        with open(filepath, 'r') as f:
            symbols = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return symbols
    except FileNotFoundError:
        logging.error(f"Watchlist file not found: {filepath}")
        return []


def get_nifty_100_stocks() -> list:
    """Get NIFTY 100 stock symbols"""
    nifty_100 = [
        "RELIANCE", "INFY", "HDFC", "ICICIBANK", "TCS", "HDFCBANK",
        "SBIN", "MARUTI", "BAJAJFINSV", "HINDUNILVR", "ASIANPAINT",
        "SUNPHARMA", "BHARTIARTL", "WIPRO", "KOTAKBANK", "ITC",
        "AXISBANK", "BAJAJELECTRICALS", "NTPC", "POWERGRID", "TATASTEEL",
        "LT", "TATAMOTORS", "TECHM", "LUPIN", "DMART", "BRITANNIA",
        "NESTLEIND", "BAJAJFINSV", "DIVISLAB", "DRREDDY", "HEROMOTOCORP",
        "JSWSTEEL", "INDIGO", "ONGC", "EICHERMOT", "HINDALCO",
        "SESHAREHOLD", "CIPLA", "GRASIM", "HCLTECH", "TITAN",
        "BIOCON", "TCS", "TORNTPHARM", "UPL", "MCDOWELL",
        "BAJAJ-AUTO", "BPCL", "M&M", "CHOLAFINSV", "IDEA",
        "IDFCBANK", "ADANIPORTS", "ADANIGREEN", "ADANIPOWER", "AUROPHARMA",
        "AWL", "BEL", "BERGEPAINT", "BSEL", "CANBK",
        "CDSL", "COFORGE", "COLPAL", "CRE", "CRUISE",
        "ESCORTS", "EXIDEIND", "FCL", "FRETAIL", "GAIL",
        "GODREJ", "HAVELLS", "HGINFRA", "HMCL", "HONAUT",
        "HUBTOWN", "INFIBEAM", "INTELLECT", "IOL", "IPCALAB",
        "JBMA", "JINDALSTEL", "JUBLFOOD", "KALYANKJIL", "KPITTECH",
        "LAXMIMACH", "LT", "LTIM", "MANAPPURAM", "MARICO",
        "MCL", "MINDTREE", "MIRC", "MNBLUE", "MNCOM",
        "MOIL", "MOTILALOFSL", "MSWC", "MTNL", "NATIONALNEWS",
    ]
    return nifty_100


def sample_watchlist(symbols: list, size: int = 75) -> list:
    """Sample stocks from NIFTY 100 for watchlist"""
    import random
    if len(symbols) <= size:
        return symbols
    return random.sample(symbols, size)
