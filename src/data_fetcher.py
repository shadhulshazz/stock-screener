"""
Phase 1: Data Fetcher
Collects OHLCV, OI, PCR, and Delivery data from free sources
"""

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetch market data from free sources"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.nse_base_url = "https://www.nseindia.com"

    def fetch_ohlcv(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        """
        Fetch OHLCV data using yfinance
        Args:
            symbol: Stock symbol (e.g., 'INFY.NS' for NSE)
            period: Data period ('1mo', '3mo', '6mo', '1y')
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
            data = yf.download(ticker, period=period, progress=False)

            if data.empty:
                logger.warning(f"No data fetched for {symbol}")
                return pd.DataFrame()

            return data
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_delivery_data(self, symbol: str) -> Optional[float]:
        """
        Fetch delivery percentage from NSE
        Args:
            symbol: Stock symbol
        Returns:
            Delivery percentage (0-100)
        """
        try:
            url = f"{self.nse_base_url}/api/reports/content/equityDeliveryBasketGen.html"
            params = {
                "symbol": symbol.replace(".NS", ""),
                "fromDate": (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y"),
                "toDate": datetime.now().strftime("%d-%b-%Y"),
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            if data and len(data) > 0:
                # Extract delivery percentage from NSE API response
                delivery_pct = float(data[0].get("deliverypct", 0))
                return delivery_pct

            return None
        except Exception as e:
            logger.warning(f"Error fetching delivery data for {symbol}: {e}")
            return None

    def fetch_oi_pcr(self, symbol: str) -> Dict[str, float]:
        """
        Fetch Open Interest and Put-Call Ratio from NSE
        Args:
            symbol: Stock symbol
        Returns:
            Dict with 'oi' and 'pcr' values
        """
        try:
            url = f"{self.nse_base_url}/api/reports/content/optionsChainOI.html"
            params = {
                "symbol": symbol.replace(".NS", ""),
                "expiryDate": "",
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            if data and "data" in data:
                total_put_oi = sum(
                    d["totalOI"]
                    for d in data["data"]
                    if d.get("ce_oi") == 0 and d.get("pe_oi") > 0
                )
                total_call_oi = sum(
                    d["totalOI"]
                    for d in data["data"]
                    if d.get("ce_oi") > 0 and d.get("pe_oi") == 0
                )

                pcr = (
                    total_put_oi / total_call_oi if total_call_oi > 0 else 0
                )

                return {"oi": sum(d["totalOI"] for d in data["data"]), "pcr": pcr}

            return {"oi": 0, "pcr": 0}
        except Exception as e:
            logger.warning(f"Error fetching OI/PCR for {symbol}: {e}")
            return {"oi": 0, "pcr": 0}

    def fetch_fii_data(self) -> Dict[str, float]:
        """
        Fetch latest FII data from NSE
        Returns:
            Dict with FII buy/sell values
        """
        try:
            url = f"{self.nse_base_url}/api/reports/content/fiiTrading.html"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            if data and len(data) > 0:
                latest = data[0]
                return {
                    "fii_buy": float(latest.get("fii_buy_value", 0)),
                    "fii_sell": float(latest.get("fii_sell_value", 0)),
                    "fii_net": float(latest.get("fii_net_buy", 0)),
                }

            return {"fii_buy": 0, "fii_sell": 0, "fii_net": 0}
        except Exception as e:
            logger.warning(f"Error fetching FII data: {e}")
            return {"fii_buy": 0, "fii_sell": 0, "fii_net": 0}

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        Args:
            symbol: Stock symbol
        Returns:
            Current price or None
        """
        try:
            ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
            data = yf.download(ticker, period="1d", progress=False)

            if not data.empty:
                return float(data["Close"].iloc[-1])

            return None
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None

    def get_support_resistance(
        self, data: pd.DataFrame, lookback: int = 20
    ) -> Dict[str, float]:
        """
        Calculate support and resistance levels from recent swings
        Args:
            data: OHLCV DataFrame
            lookback: Number of periods to lookback
        Returns:
            Dict with 'support' and 'resistance' values
        """
        if data.empty or len(data) < lookback:
            return {"support": 0, "resistance": 0}

        recent = data.tail(lookback)
        support = float(recent["Low"].min())
        resistance = float(recent["High"].max())

        return {"support": support, "resistance": resistance}
