"""Module 3: Quantitative Signal Generator

Multi-timeframe technical analysis with confluence detection.
Geneates LONG/SHORT/NEUTRAL signals based on RSI, MA envelopes, volume, funding rates, and liquidation clusters.
"""

import logging
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from src.utils.validators import TradeSignal

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Multi-timeframe technical signal generator."""
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        ma_fast_period: int = 9,
        ma_slow_period: int = 21,
        volume_sma_period: int = 20,
        liquidation_window_candles: int = 5,
    ):
        """
        Initialize Signal Generator.
        
        Args:
            rsi_period: RSI calculation period
            rsi_oversold: RSI threshold for oversold (bullish)
            rsi_overbought: RSI threshold for overbought (bearish)
            ma_fast_period: Fast moving average period
            ma_slow_period: Slow moving average period
            volume_sma_period: Volume SMA for comparison
            liquidation_window_candles: Candles to look back for liquidation clusters
        """
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.ma_fast = ma_fast_period
        self.ma_slow = ma_slow_period
        self.vol_sma = volume_sma_period
        self.liq_window = liquidation_window_candles
        
        logger.info("Signal Generator initialized")
    
    def generate_signal(
        self,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_4h: pd.DataFrame,
        funding_rate: Optional[float] = None,
        open_interest: Optional[float] = None,
        liquidation_data: Optional[Dict] = None,
    ) -> Optional[TradeSignal]:
        """
        Generate multi-timeframe trading signal.
        
        Args:
            candles_15m: 15m OHLCV data
            candles_1h: 1h OHLCV data
            candles_4h: 4h OHLCV data
            funding_rate: Current perpetual funding rate
            open_interest: Current open interest
            liquidation_data: Dict with liquidation cascade info
        
        Returns:
            TradeSignal with direction, confidence, and triggers
        """
        
        # Generate signals on each timeframe
        signal_15m = self._analyze_timeframe(candles_15m, "15m")
        signal_1h = self._analyze_timeframe(candles_1h, "1h")
        signal_4h = self._analyze_timeframe(candles_4h, "4h")
        
        if not all([signal_15m, signal_1h, signal_4h]):
            logger.warning("Insufficient data for signal generation")
            return None
        
        # Aggregate signals
        timeframe_confluence = {
            "15m": signal_15m["direction"],
            "1h": signal_1h["direction"],
            "4h": signal_4h["direction"],
        }
        
        # Count votes
        long_votes = sum(1 for v in timeframe_confluence.values() if v == "LONG")
        short_votes = sum(1 for v in timeframe_confluence.values() if v == "SHORT")
        neutral_votes = sum(1 for v in timeframe_confluence.values() if v == "NEUTRAL")
        
        # Determine primary direction (require at least 2/3 confluence)
        if long_votes >= 2:
            direction = "LONG"
            base_confidence = 0.5 + (long_votes * 0.15)
        elif short_votes >= 2:
            direction = "SHORT"
            base_confidence = 0.5 + (short_votes * 0.15)
        else:
            direction = "NEUTRAL"
            base_confidence = 0.4
        
        # Collect all triggers
        all_triggers = []
        all_triggers.extend(signal_15m.get("triggers", []))
        all_triggers.extend(signal_1h.get("triggers", []))
        all_triggers.extend(signal_4h.get("triggers", []))
        
        # Add macro signal triggers (funding, liquidations)
        macro_triggers = self._check_macro_signals(
            funding_rate, open_interest, liquidation_data
        )
        all_triggers.extend(macro_triggers)
        
        # Boost confidence if macro aligns
        macro_boost = len(macro_triggers) * 0.05
        final_confidence = min(0.95, base_confidence + macro_boost)
        
        # Calculate strength score (-1.0 to 1.0)
        strength_score = (long_votes - short_votes) / 3.0
        
        signal = TradeSignal(
            direction=direction,
            confidence=final_confidence,
            triggers=list(set(all_triggers)),  # Remove duplicates
            timeframe_confluence=timeframe_confluence,
            strength_score=strength_score,
            description=self._generate_signal_description(direction, timeframe_confluence, all_triggers),
        )
        
        logger.info(
            "Signal generated",
            direction=direction,
            confidence=f"{final_confidence:.2f}",
            timeframe_confluence=timeframe_confluence,
            triggers_count=len(signal.triggers),
        )
        
        return signal
    
    def _analyze_timeframe(self, candles_df: pd.DataFrame, timeframe: str) -> Optional[Dict]:
        """Analyze single timeframe and return signal info."""
        if len(candles_df) < max(self.rsi_period, self.ma_slow):
            logger.warning(f"Insufficient data for {timeframe} analysis")
            return None
        
        df = candles_df.copy()
        
        # Calculate RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # Calculate moving averages
        df['ma_fast'] = df['close'].rolling(self.ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(self.ma_slow).mean()
        
        # Calculate volume indicators
        df['vol_sma'] = df['volume'].rolling(self.vol_sma).mean()
        
        # Get current values
        current_close = df['close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        current_ma_fast = df['ma_fast'].iloc[-1]
        current_ma_slow = df['ma_slow'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        current_vol_sma = df['vol_sma'].iloc[-1]
        
        triggers = []
        
        # RSI signals
        if current_rsi < self.rsi_oversold:
            triggers.append(f"rsi_oversold_{timeframe}")
        elif current_rsi > self.rsi_overbought:
            triggers.append(f"rsi_overbought_{timeframe}")
        
        # MA crossover signals
        if len(df) > 1:
            prev_ma_fast = df['ma_fast'].iloc[-2]
            prev_ma_slow = df['ma_slow'].iloc[-2]
            
            if prev_ma_fast <= prev_ma_slow and current_ma_fast > current_ma_slow:
                triggers.append(f"ma_bullish_cross_{timeframe}")
            elif prev_ma_fast >= prev_ma_slow and current_ma_fast < current_ma_slow:
                triggers.append(f"ma_bearish_cross_{timeframe}")
        
        # Volume signals
        if current_volume > current_vol_sma * 1.5:
            triggers.append(f"volume_surge_{timeframe}")
        
        # Determine direction
        long_signals = sum(1 for t in triggers if "oversold" in t or "bullish" in t)
        short_signals = sum(1 for t in triggers if "overbought" in t or "bearish" in t)
        
        if long_signals > short_signals and current_ma_fast > current_ma_slow:
            direction = "LONG"
        elif short_signals > long_signals and current_ma_fast < current_ma_slow:
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return {
            "direction": direction,
            "triggers": triggers,
            "rsi": current_rsi,
            "ma_fast": current_ma_fast,
            "ma_slow": current_ma_slow,
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _check_macro_signals(
        self,
        funding_rate: Optional[float],
        open_interest: Optional[float],
        liquidation_data: Optional[Dict],
    ) -> List[str]:
        """Check macro signals: funding rates, open interest, liquidations."""
        triggers = []
        
        if funding_rate is not None:
            if funding_rate < -0.0005:  # Negative = bearish sentiment
                triggers.append("funding_rate_negative")
            elif funding_rate > 0.0005:  # Positive = bullish sentiment
                triggers.append("funding_rate_positive")
        
        if open_interest is not None:
            # Rising OI can indicate momentum (placeholder logic)
            triggers.append("open_interest_elevated")
        
        if liquidation_data:
            long_liq = liquidation_data.get("long_liquidations", 0)
            short_liq = liquidation_data.get("short_liquidations", 0)
            
            if long_liq > short_liq * 2:
                triggers.append("liquidation_cluster_short")
            elif short_liq > long_liq * 2:
                triggers.append("liquidation_cluster_long")
        
        return triggers
    
    def _generate_signal_description(self, direction: str, timeframe_confluence: Dict, triggers: List[str]) -> str:
        """Generate human-readable signal description."""
        if direction == "LONG":
            return f"Bullish confluence: {', '.join([k for k, v in timeframe_confluence.items() if v == 'LONG'])}"
        elif direction == "SHORT":
            return f"Bearish confluence: {', '.join([k for k, v in timeframe_confluence.items() if v == 'SHORT'])}"
        else:
            return "No strong multi-timeframe confluence; awaiting confirmation"
