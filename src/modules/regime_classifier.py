"""Module 2: Market Regime Classifier

Dynamically detects current market states and adjusts trading strategy accordingly.
"""

import logging
from typing import Optional, List
import pandas as pd
import numpy as np
from src.utils.validators import MarketRegimeOutput

logger = logging.getLogger(__name__)


class MarketRegimeClassifier:
    """Identifies market regimes: Bull, Bear, Sideways, Squeeze/Breakout."""
    
    def __init__(
        self,
        fast_ma_period: int = 20,
        slow_ma_period: int = 50,
        rsi_period: int = 14,
        atr_period: int = 14,
        volatility_threshold_low: float = 0.01,
        volatility_threshold_high: float = 0.03,
    ):
        """
        Initialize Market Regime Classifier.
        
        Args:
            fast_ma_period: Short-term moving average period
            slow_ma_period: Long-term moving average period
            rsi_period: RSI calculation period
            atr_period: ATR calculation period
            volatility_threshold_low: Threshold for low volatility
            volatility_threshold_high: Threshold for high volatility
        """
        self.fast_ma_period = fast_ma_period
        self.slow_ma_period = slow_ma_period
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.vol_low = volatility_threshold_low
        self.vol_high = volatility_threshold_high
        
        logger.info("Market Regime Classifier initialized")
    
    def classify(
        self,
        candles_df: pd.DataFrame,
    ) -> Optional[MarketRegimeOutput]:
        """
        Classify current market regime.
        
        Args:
            candles_df: DataFrame with columns [open, high, low, close, volume]
        
        Returns:
            MarketRegimeOutput with regime classification
        """
        if len(candles_df) < self.slow_ma_period:
            logger.warning("Insufficient candle data for regime classification")
            return None
        
        df = candles_df.copy()
        
        # Calculate moving averages
        df['ma_fast'] = df['close'].rolling(self.fast_ma_period).mean()
        df['ma_slow'] = df['close'].rolling(self.slow_ma_period).mean()
        
        # Calculate ATR (volatility measure)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            )
        )
        df['atr'] = df['tr'].rolling(self.atr_period).mean()
        
        # Calculate volatility as ATR / close
        df['volatility'] = df['atr'] / df['close']
        
        # Get current values
        current_close = df['close'].iloc[-1]
        current_ma_fast = df['ma_fast'].iloc[-1]
        current_ma_slow = df['ma_slow'].iloc[-1]
        current_atr = df['atr'].iloc[-1]
        current_volatility = df['volatility'].iloc[-1]
        
        # Determine trend direction
        trend_up = current_ma_fast > current_ma_slow
        price_above_fast = current_close > current_ma_fast
        price_above_slow = current_close > current_ma_slow
        
        # Calculate trend strength (slope of fast MA)
        ma_fast_slope = (df['ma_fast'].iloc[-1] - df['ma_fast'].iloc[-10]) / 10 if len(df) > 10 else 0
        trend_strength = abs(ma_fast_slope) / current_close if current_close > 0 else 0
        
        # Classify volatility regime
        if current_volatility < self.vol_low:
            volatility_level = "low"
        elif current_volatility > self.vol_high:
            volatility_level = "extreme"
        elif current_volatility > self.vol_low * 2.5:
            volatility_level = "high"
        else:
            volatility_level = "medium"
        
        # Detect key levels (support/resistance)
        key_levels = {
            "ma_fast": current_ma_fast,
            "ma_slow": current_ma_slow,
            "52w_high": df['high'].rolling(252).max().iloc[-1],
            "52w_low": df['low'].rolling(252).min().iloc[-1],
        }
        
        # Classify regime
        if trend_up and price_above_fast and price_above_slow:
            if trend_strength > 0.002:  # Strong trend
                regime = "strong_bull"
                confidence = min(0.95, 0.5 + trend_strength * 100)
            else:
                regime = "bull"
                confidence = 0.75
        elif not trend_up and not price_above_fast and not price_above_slow:
            regime = "bear"
            confidence = 0.75
        elif not trend_up and volatility_level in ["low", "medium"]:
            regime = "sideways"
            confidence = 0.60
        elif volatility_level == "extreme" or (current_volatility > self.vol_high and current_atr > df['atr'].rolling(50).mean().iloc[-1] * 1.5):
            regime = "squeeze_breakout"
            confidence = 0.70
        else:
            regime = "sideways"
            confidence = 0.65
        
        output = MarketRegimeOutput(
            regime=regime,
            confidence=confidence,
            volatility_level=volatility_level,
            key_levels=key_levels,
            description=self._regime_description(regime, current_volatility, trend_strength),
        )
        
        logger.info(
            "Market regime classified",
            regime=regime,
            confidence=f"{confidence:.2f}",
            volatility=volatility_level,
            price=current_close,
        )
        
        return output
    
    def _regime_description(self, regime: str, volatility: float, trend_strength: float) -> str:
        """Generate human-readable regime description."""
        descriptions = {
            "strong_bull": "Strong uptrend with momentum and healthy pullbacks",
            "bull": "Uptrend with bullish structure and rising support",
            "bear": "Downtrend with breakdown of support levels",
            "sideways": "Range-bound market consolidation; breakout potential",
            "squeeze_breakout": "High volatility; potential breakout imminent",
        }
        return descriptions.get(regime, "Unknown regime")
