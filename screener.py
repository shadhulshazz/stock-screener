#!/usr/bin/env python3
"""
Main Stock Screener Orchestrator
Coordinates data fetching, filtering, AI analysis, and output
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import argparse

from src.data_fetcher import DataFetcher
from src.technical_filters import TechnicalFilters, FilterCriteria
from src.ai_engine import AIEngine
from src.output_handler import OutputHandler
from src.utils import setup_logging, get_nifty_100_stocks, sample_watchlist, is_market_open

# Load environment variables
load_dotenv()

logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))


class StockScreener:
    """Main screening orchestrator"""

    def __init__(self):
        self.fetcher = DataFetcher()
        self.filters = TechnicalFilters(
            criteria=FilterCriteria(
                atr_min=float(os.getenv("ATR_MIN", 8)),
                atr_max=float(os.getenv("ATR_MAX", 25)),
                rsi_min=float(os.getenv("RSI_MIN", 35)),
                rsi_max=float(os.getenv("RSI_MAX", 55)),
                volume_ratio_min=float(os.getenv("VOLUME_RATIO_MIN", 1.5)),
                delivery_min=float(os.getenv("DELIVERY_PERCENT_MIN", 45)),
                price_range_percent=float(os.getenv("PRICE_RANGE_PERCENT", 2)),
            )
        )
        self.ai_engine = AIEngine(provider=os.getenv("AI_PROVIDER", "claude"))
        self.output = OutputHandler()
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 75))

    def prepare_watchlist(self, symbols: list = None) -> list:
        """Get or prepare watchlist of stocks to screen"""
        if symbols:
            return symbols

        # Load from environment or use default NIFTY 100
        watchlist_size = int(os.getenv("WATCHLIST_SIZE", 75))
        nifty_100 = get_nifty_100_stocks()
        return sample_watchlist(nifty_100, watchlist_size)

    def fetch_stock_data(self, symbol: str) -> dict:
        """Fetch all required data for a stock"""
        try:
            # Fetch OHLCV
            ohlcv_data = self.fetcher.fetch_ohlcv(symbol, period="3mo")
            if ohlcv_data.empty:
                logger.warning(f"No OHLCV data for {symbol}")
                return None

            # Get current price
            current_price = self.fetcher.get_current_price(symbol)
            if not current_price:
                logger.warning(f"Could not get current price for {symbol}")
                return None

            # Get support/resistance
            sr_levels = self.fetcher.get_support_resistance(ohlcv_data)

            # Get delivery %
            delivery = self.fetcher.fetch_delivery_data(symbol) or 0

            return {
                "symbol": symbol.replace(".NS", ""),
                "data": ohlcv_data,
                "price": current_price,
                "delivery": delivery,
                "support": sr_levels["support"],
                "resistance": sr_levels["resistance"],
            }
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def screen(self, watchlist: list = None) -> dict:
        """Execute complete screening pipeline"""
        logger.info("=" * 60)
        logger.info("STARTING STOCK SCREENING")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        watchlist = self.prepare_watchlist(watchlist)
        logger.info(f"Screening {len(watchlist)} stocks")

        # Fetch data for all stocks
        stocks_data = []
        for symbol in watchlist:
            data = self.fetch_stock_data(symbol)
            if data:
                stocks_data.append(data)

        logger.info(f"Successfully fetched data for {len(stocks_data)} stocks")

        # Apply technical filters
        filter_results = self.filters.batch_screen(stocks_data)
        passed_filters = [r for r in filter_results if r.passed_filters]

        logger.info(f"Stocks passed technical filters: {len(passed_filters)}")

        # Generate AI signals for filtered stocks
        ai_signals = []
        for result in passed_filters:
            # Build stock data dict for AI
            stock_data = {
                "symbol": result.symbol,
                "price": result.price,
                "rsi": result.rsi,
                "atr": result.atr,
                "macd": 0,  # Could add MACD calculation
                "macd_signal": 0,
                "macd_histogram": 0,
                "support": result.support,
                "resistance": result.resistance,
                "volume_ratio": result.volume_ratio,
                "delivery_pct": result.delivery_pct,
            }

            signal = self.ai_engine.generate_signal(stock_data)
            if signal:
                ai_signals.append(signal)

        logger.info(f"Generated AI signals: {len(ai_signals)}")

        # Filter by confidence threshold
        high_confidence = [
            s for s in ai_signals if s.confidence >= self.confidence_threshold
        ]
        logger.info(
            f"High confidence signals (>={self.confidence_threshold}%): {len(high_confidence)}"
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "watchlist_count": len(watchlist),
            "data_fetched": len(stocks_data),
            "passed_filters": len(passed_filters),
            "ai_signals": len(ai_signals),
            "high_confidence_signals": high_confidence,
            "all_signals": ai_signals,
        }

    async def send_results(self, results: dict) -> bool:
        """Send results via Telegram and log to Sheets"""
        try:
            high_conf = results["high_confidence_signals"]

            if high_conf:
                logger.info(f"Sending {len(high_conf)} alerts via Telegram")
                await self.output.send_screening_results(high_conf)
            else:
                logger.info("No high-confidence signals, sending info alert")
                await self.output.send_screening_results([])

            # Log to Sheets
            self.output.log_to_sheets(results["all_signals"])

            # Log to JSON
            self.output.log_to_json(results["all_signals"])

            return True
        except Exception as e:
            logger.error(f"Error sending results: {e}")
            return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Stock Screener")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with limited stocks",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Comma-separated symbols to screen (e.g., INFY,TCS,RELIANCE)",
    )
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Don't send results (useful for testing)",
    )

    args = parser.parse_args()

    screener = StockScreener()

    # Prepare watchlist
    watchlist = None
    if args.symbols:
        watchlist = [s.strip() for s in args.symbols.split(",")]
    elif args.test:
        watchlist = ["INFY", "TCS", "RELIANCE", "HDFC", "ICICIBANK"]

    # Execute screening
    results = screener.screen(watchlist)

    # Log results
    logger.info(f"\n{'=' * 60}")
    logger.info(f"SCREENING COMPLETE")
    logger.info(f"Scanned: {results['data_fetched']} stocks")
    logger.info(f"Passed filters: {results['passed_filters']} stocks")
    logger.info(f"AI Signals: {results['ai_signals']}")
    logger.info(
        f"High Confidence (>={screener.confidence_threshold}%): {len(results['high_confidence_signals'])}"
    )
    logger.info(f"{'=' * 60}\n")

    # Send results
    if not args.no_send:
        await screener.send_results(results)
        logger.info("Results sent successfully")
    else:
        logger.info("Skipping result sending (--no-send flag)")


if __name__ == "__main__":
    asyncio.run(main())