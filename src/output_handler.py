"""
Output Handler
Telegram alerts and Google Sheets logging
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class OutputHandler:
    """Send alerts and log results"""

    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.sheets_enabled = bool(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))

        if self.telegram_token and self.telegram_chat_id:
            self.bot = Bot(token=self.telegram_token)
        else:
            self.bot = None
            logger.warning("Telegram not configured")

    async def send_telegram_alert(
        self, title: str, content: str, parse_mode: str = "HTML"
    ) -> bool:
        """
        Send alert via Telegram
        Args:
            title: Message title
            content: Message content (supports HTML)
            parse_mode: Parse mode ('HTML' or 'Markdown')
        Returns:
            Success status
        """
        if not self.bot or not self.telegram_chat_id:
            logger.warning("Telegram not configured, skipping alert")
            return False

        try:
            message = f"<b>{title}</b>\n\n{content}"
            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            logger.info(f"Telegram alert sent: {title}")
            return True
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False

    def send_screening_results(self, signals: List) -> bool:
        """
        Send screening results summary via Telegram
        Args:
            signals: List of AISignal objects
        Returns:
            Success status
        """
        if not signals:
            return self._send_no_signals_alert()

        # Filter high-confidence signals
        high_confidence = [s for s in signals if s.confidence >= 70]

        if not high_confidence:
            return self._send_no_signals_alert()

        # Build message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        content = f"<b>🎯 Stock Screener Alert</b>\n<i>{timestamp} IST</i>\n\n"

        content += "<b>✅ High Confidence Signals:</b>\n\n"

        for i, signal in enumerate(high_confidence[:5], 1):
            content += (
                f"<b>{i}. {signal.symbol}</b> | "
                f"<i>{signal.direction.upper()}</i>\n"
            )
            content += (
                f"   Target: ₹{signal.target:.2f} | "
                f"SL: ₹{signal.stop_loss:.2f}\n"
            )
            content += f"   Confidence: <b>{signal.confidence:.0f}%</b>\n"
            content += f"   Reason: {signal.reason}\n\n"

        content += f"📊 Total scanned: {len(signals)}\n"
        content += f"⭐ High confidence: {len(high_confidence)}\n\n"

        content += (
            "<i>⚠️ Not financial advice. "
            "Backtest independently before trading.</i>"
        )

        return self._send_async_telegram(
            title="Stock Screener Results",
            content=content,
        )

    def _send_no_signals_alert(self) -> bool:
        """Send alert when no signals meet criteria"""
        return self._send_async_telegram(
            title="Stock Screener",
            content=(
                "📊 No high-confidence signals today.\n"
                f"Scan completed: {datetime.now().strftime('%H:%M')} IST\n\n"
                "<i>Wait for next screening cycle.</i>"
            ),
        )

    def _send_async_telegram(self, title: str, content: str) -> bool:
        """Wrapper for async telegram sending"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                task = asyncio.create_task(
                    self.send_telegram_alert(title, content)
                )
                return True
            else:
                # Run in new loop
                return asyncio.run(self.send_telegram_alert(title, content))
        except Exception as e:
            logger.error(f"Error in async telegram call: {e}")
            return False

    def log_to_sheets(self, signals: List, sheet_id: Optional[str] = None) -> bool:
        """
        Log signals to Google Sheets
        Args:
            signals: List of AISignal objects
            sheet_id: Google Sheet ID (uses env if not provided)
        Returns:
            Success status
        """
        if not self.sheets_enabled:
            logger.warning("Google Sheets not configured")
            return False

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            sheet_id = sheet_id or os.getenv("GOOGLE_SHEETS_ID")
            credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

            if not sheet_id or not credentials_path:
                logger.warning("Missing Google Sheets configuration")
                return False

            # Authenticate
            creds = Credentials.from_service_account_file(
                credentials_path,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )

            client = gspread.authorize(creds)
            sheet = client.open_by_key(sheet_id).sheet1

            # Append data
            timestamp = datetime.now().isoformat()

            for signal in signals:
                row = [
                    timestamp,
                    signal.symbol,
                    signal.direction,
                    signal.target,
                    signal.stop_loss,
                    signal.confidence,
                    signal.reason,
                ]
                sheet.append_row(row)

            logger.info(f"Logged {len(signals)} signals to Sheets")
            return True

        except ImportError:
            logger.warning("gspread not installed")
            return False
        except Exception as e:
            logger.error(f"Error logging to Sheets: {e}")
            return False

    def log_to_json(self, signals: List, filename: str = "signals.json") -> bool:
        """
        Log signals to JSON file
        Args:
            signals: List of AISignal objects
            filename: Output filename
        Returns:
            Success status
        """
        try:
            import json

            data = {
                "timestamp": datetime.now().isoformat(),
                "total_signals": len(signals),
                "signals": [s.to_dict() for s in signals],
            }

            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Logged {len(signals)} signals to {filename}")
            return True

        except Exception as e:
            logger.error(f"Error logging to JSON: {e}")
            return False

    def format_daily_summary(
        self, screened: int, passed: int, signals: List
    ) -> str:
        """
        Format a daily summary message
        Args:
            screened: Total stocks screened
            passed: Stocks that passed filters
            signals: AI-generated signals
        Returns:
            Formatted message
        """
        high_conf = [s for s in signals if s.confidence >= 75]

        summary = f"""
📊 <b>Daily Screening Summary</b>
━━━━━━━━━━━━━━━━
📈 Screened: {screened} stocks
✅ Passed filters: {passed} stocks
⭐ High confidence signals: {len(high_conf)}
⏱️ Timestamp: {datetime.now().strftime('%H:%M %Z')}
"""
        return summary.strip()
