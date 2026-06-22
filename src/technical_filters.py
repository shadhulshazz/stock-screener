"""
Phase 3: Technical Filters
Screening logic for ATR, RSI, Volume, Support/Resistance, Delivery
"""

import pandas as pd
import pandas_ta as ta
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """Container for filter parameters"""

    atr_min: float = 8
    atr_max: float = 25
    rsi_min: float = 35
    rsi_max: float = 55
    volume_ratio_min: float = 1.5
    delivery_min: float = 45
    price_range_percent: float = 2


@dataclass
class ScreeningResult:
    """Result of screening a single stock"""

    symbol: str
    price: float
    atr: float
    rsi: float
    volume_ratio: float
    delivery_pct: float
    support: float
    resistance: float
    near_support: bool
    near_resistance: bool
    passed_filters: bool
    filter_score: float

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "price": self.price,
            "atr": self.atr,
            "rsi": self.rsi,
            "volume_ratio": self.volume_ratio,
            "delivery_pct": self.delivery_pct,
            "support": self.support,
            "resistance": self.resistance,
            "near_support": self.near_support,
            "near_resistance": self.near_resistance,
            "passed_filters": self.passed_filters,
            "filter_score": self.filter_score,
        }


class TechnicalFilters:
    """Apply technical filters to stock data"""

    def __init__(self, criteria: Optional[FilterCriteria] = None):
        self.criteria = criteria or FilterCriteria()

    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if data.empty or len(data) < period:
            return 0

        try:
            atr = ta.atr(data["High"], data["Low"], data["Close"], length=period)
            return float(atr.iloc[-1]) if not atr.empty else 0
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0

    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if data.empty or len(data) < period:
            return 0

        try:
            rsi = ta.rsi(data["Close"], length=period)
            return float(rsi.iloc[-1]) if not rsi.empty else 0
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 0

    def calculate_macd(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate MACD indicator"""
        if data.empty or len(data) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}

        try:
            macd_result = ta.macd(data["Close"])
            if macd_result is not None and len(macd_result.columns) >= 3:
                return {
                    "macd": float(macd_result.iloc[-1, 0]),
                    "signal": float(macd_result.iloc[-1, 1]),
                    "histogram": float(macd_result.iloc[-1, 2]),
                }
            return {"macd": 0, "signal": 0, "histogram": 0}
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {"macd": 0, "signal": 0, "histogram": 0}

    def calculate_volume_ratio(self, data: pd.DataFrame, period: int = 20) -> float:
        """Calculate volume ratio (current vs 20-day average)"""
        if data.empty or len(data) < period:
            return 0

        try:
            current_volume = float(data["Volume"].iloc[-1])
            avg_volume = float(data["Volume"].tail(period).mean())

            if avg_volume == 0:
                return 0

            return current_volume / avg_volume
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {e}")
            return 0

    def check_support_resistance_proximity(
        self, price: float, support: float, resistance: float
    ) -> Dict[str, bool]:
        """Check if price is near support or resistance"""
        if support == 0 or resistance == 0:
            return {"near_support": False, "near_resistance": False}

        support_range = support * (1 + self.criteria.price_range_percent / 100)
        resistance_range = resistance * (1 - self.criteria.price_range_percent / 100)

        return {
            "near_support": support <= price <= support_range,
            "near_resistance": resistance_range <= price <= resistance,
        }

    def screen_stock(
        self,
        symbol: str,
        data: pd.DataFrame,
        current_price: float,
        delivery_pct: float,
        support: float,
        resistance: float,
    ) -> ScreeningResult:
        """
        Apply all filters to a stock
        Returns: ScreeningResult with pass/fail status
        """

        # Calculate indicators
        atr = self.calculate_atr(data)
        rsi = self.calculate_rsi(data)
        volume_ratio = self.calculate_volume_ratio(data)
        proximity = self.check_support_resistance_proximity(
            current_price, support, resistance
        )

        # Check each filter
        atr_pass = self.criteria.atr_min <= atr <= self.criteria.atr_max
        rsi_pass = self.criteria.rsi_min <= rsi <= self.criteria.rsi_max
        volume_pass = volume_ratio >= self.criteria.volume_ratio_min
        delivery_pass = delivery_pct >= self.criteria.delivery_min
        proximity_pass = proximity["near_support"] or proximity["near_resistance"]

        # Overall pass: All hard filters must pass
        passed_filters = atr_pass and rsi_pass and volume_pass and delivery_pass and proximity_pass

        # Calculate filter score (0-100)
        score = 0
        score += 20 if atr_pass else 0
        score += 20 if rsi_pass else 0
        score += 20 if volume_pass else 0
        score += 20 if delivery_pass else 0
        score += 20 if proximity_pass else 0

        return ScreeningResult(
            symbol=symbol,
            price=current_price,
            atr=atr,
            rsi=rsi,
            volume_ratio=volume_ratio,
            delivery_pct=delivery_pct,
            support=support,
            resistance=resistance,
            near_support=proximity["near_support"],
            near_resistance=proximity["near_resistance"],
            passed_filters=passed_filters,
            filter_score=score,
        )

    def batch_screen(
        self, stocks_data: List[Dict]
    ) -> List[ScreeningResult]:
        """
        Screen multiple stocks
        Args:
            stocks_data: List of dicts with keys: symbol, data, price, delivery, support, resistance
        Returns:
            List of ScreeningResult objects
        """
        results = []

        for stock in stocks_data:
            try:
                result = self.screen_stock(
                    symbol=stock["symbol"],
                    data=stock["data"],
                    current_price=stock["price"],
                    delivery_pct=stock["delivery"],
                    support=stock["support"],
                    resistance=stock["resistance"],
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error screening {stock['symbol']}: {e}")
                continue

        # Sort by filter score descending
        results.sort(key=lambda x: x.filter_score, reverse=True)

        return results
