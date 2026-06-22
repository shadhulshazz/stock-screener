"""
Phase 4: AI Engine
Claude/Groq API integration for signal quality assessment
"""

import os
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers"""

    CLAUDE = "claude"
    GROQ = "groq"


@dataclass
class AISignal:
    """AI-generated trading signal"""

    symbol: str
    direction: str  # "up", "down", "neutral"
    target: float
    stop_loss: float
    confidence: float  # 0-100
    reason: str
    timeframe: str  # "5d", "7d", etc.

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "target": self.target,
            "stop_loss": self.stop_loss,
            "confidence": self.confidence,
            "reason": self.reason,
            "timeframe": self.timeframe,
        }


class AIEngine:
    """Generate trading signals using AI"""

    def __init__(self, provider: str = "claude"):
        self.provider = AIProvider(provider.lower())
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate AI client"""
        if self.provider == AIProvider.CLAUDE:
            try:
                from anthropic import Anthropic

                api_key = os.getenv("CLAUDE_API_KEY")
                if not api_key:
                    raise ValueError("CLAUDE_API_KEY not set in environment")
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                logger.error("anthropic library not installed")
                self.client = None
        elif self.provider == AIProvider.GROQ:
            try:
                from groq import Groq

                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY not set in environment")
                self.client = Groq(api_key=api_key)
            except ImportError:
                logger.error("groq library not installed")
                self.client = None

    def _build_prompt(self, stock_data: Dict) -> str:
        """Build the AI prompt from stock technical data"""

        prompt = f"""You are an expert technical analyst specializing in swing trading on NSE (India).

Analyze this stock snapshot and determine if it will move ±5-10 INR within 5 trading days.

STOCK DATA:
- Symbol: {stock_data['symbol']}
- Current Price: ₹{stock_data['price']:.2f}
- RSI (14): {stock_data['rsi']:.2f}
- MACD: {stock_data['macd']:.2f}
- MACD Signal: {stock_data['macd_signal']:.2f}
- MACD Histogram: {stock_data['macd_histogram']:.2f}
- ATR (14): ₹{stock_data['atr']:.2f}
- Support Level: ₹{stock_data['support']:.2f}
- Resistance Level: ₹{stock_data['resistance']:.2f}
- Volume Ratio (vs 20-day avg): {stock_data['volume_ratio']:.2f}x
- Delivery %: {stock_data['delivery_pct']:.2f}%
- Price vs Support: {((stock_data['price'] / stock_data['support'] - 1) * 100):.2f}%
- Price vs Resistance: {((stock_data['resistance'] / stock_data['price'] - 1) * 100):.2f}%

CONTEXT:
- Market condition: Neutral (swing trading)
- Time horizon: 5 trading days
- Target move: ±5-10 INR from current price

ANALYZE AND RESPOND with a JSON object (no markdown, just raw JSON):
{{
    "direction": "up" or "down" or "neutral",
    "target_price": <float>,
    "stop_loss": <float>,
    "confidence": <integer 0-100>,
    "reason": "<brief explanation of technical setup>"
}}

Be conservative. Only recommend UP/DOWN if confidence >= 70%.
Stop loss should protect against a 2x ATR loss.
Target should be realistic based on current volatility (ATR).
"""
        return prompt

    def generate_signal(self, stock_data: Dict) -> Optional[AISignal]:
        """
        Generate AI signal for a stock
        Args:
            stock_data: Dict with technical indicators
        Returns:
            AISignal object or None if error
        """

        if not self.client:
            logger.error("AI client not initialized")
            return None

        try:
            prompt = self._build_prompt(stock_data)

            if self.provider == AIProvider.CLAUDE:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = response.content[0].text

            elif self.provider == AIProvider.GROQ:
                response = self.client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = response.choices[0].message.content

            else:
                return None

            # Parse JSON response
            try:
                # Try to extract JSON from response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    signal_data = json.loads(json_str)
                else:
                    logger.error(f"Could not find JSON in response: {response_text}")
                    return None

                # Validate required fields
                required = ["direction", "target_price", "stop_loss", "confidence"]
                if not all(k in signal_data for k in required):
                    logger.error(f"Missing required fields in response: {signal_data}")
                    return None

                return AISignal(
                    symbol=stock_data["symbol"],
                    direction=signal_data["direction"],
                    target=float(signal_data["target_price"]),
                    stop_loss=float(signal_data["stop_loss"]),
                    confidence=float(signal_data["confidence"]),
                    reason=signal_data.get("reason", ""),
                    timeframe="5d",
                )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.debug(f"Response was: {response_text}")
                return None

        except Exception as e:
            logger.error(f"Error generating signal for {stock_data['symbol']}: {e}")
            return None

    def batch_generate_signals(
        self, stocks_data: list
    ) -> list:
        """
        Generate signals for multiple stocks
        Args:
            stocks_data: List of stock data dicts
        Returns:
            List of AISignal objects
        """
        signals = []

        for stock in stocks_data:
            signal = self.generate_signal(stock)
            if signal:
                signals.append(signal)

        return signals
