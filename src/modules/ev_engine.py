"""Module 1: EV Engine & Risk Management

Computes Expected Value for every trade setup, enforces R:R ratios,
and sizes positions according to risk management rules.
"""

import logging
from typing import Optional, Dict
from pydantic import BaseModel
import math

from src.utils.validators import TradeRiskProfile

logger = logging.getLogger(__name__)


class EVEngine:
    """Expected Value Engine with dynamic risk sizing."""
    
    def __init__(
        self,
        account_size_usd: float,
        max_risk_per_trade_pct: float = 2.0,
        min_rr_ratio: float = 1.5,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.0004,
        slippage_buffer_pct: float = 0.05,
    ):
        """
        Initialize EV Engine.
        
        Args:
            account_size_usd: Total trading capital
            max_risk_per_trade_pct: Max loss as % of account (1-2%)
            min_rr_ratio: Minimum reward:risk ratio (1.5 or 2.0)
            maker_fee: Exchange maker fee (decimal)
            taker_fee: Exchange taker fee (decimal)
            slippage_buffer_pct: Buffer for slippage (0.05 = 5 bps)
        """
        self.account_size = account_size_usd
        self.max_risk_pct = max_risk_per_trade_pct
        self.min_rr_ratio = min_rr_ratio
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage_buffer = slippage_buffer_pct / 100.0
        
        logger.info(
            "EV Engine initialized",
            account_size=account_size_usd,
            max_risk_pct=max_risk_per_trade_pct,
            min_rr_ratio=min_rr_ratio,
        )
    
    def calculate_risk_profile(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        entry_price: float,
        stop_loss_price: float,
        take_profit_price: float,
        win_probability: float = 0.55,
        current_balance: Optional[float] = None,
        atr: float = 0.0,
    ) -> Optional[TradeRiskProfile]:
        """
        Calculate complete risk profile for a trade setup.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            side: "BUY" or "SELL"
            entry_price: Entry price
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
            win_probability: Expected win probability (0.0-1.0)
            current_balance: Current account balance (defaults to account_size)
            atr: Average True Range (used for validation)
        
        Returns:
            TradeRiskProfile if valid, None if rejected
        """
        current_balance = current_balance or self.account_size
        
        # Validate price levels
        if side == "BUY":
            if stop_loss_price >= entry_price:
                logger.error("Invalid BUY setup: SL >= Entry")
                return None
            if take_profit_price <= entry_price:
                logger.error("Invalid BUY setup: TP <= Entry")
                return None
        else:  # SELL
            if stop_loss_price <= entry_price:
                logger.error("Invalid SELL setup: SL <= Entry")
                return None
            if take_profit_price >= entry_price:
                logger.error("Invalid SELL setup: TP >= Entry")
                return None
        
        # Calculate raw risk & reward distances
        if side == "BUY":
            risk_distance = entry_price - stop_loss_price
            reward_distance = take_profit_price - entry_price
        else:
            risk_distance = stop_loss_price - entry_price
            reward_distance = entry_price - take_profit_price
        
        # Apply slippage buffer
        risk_distance_adjusted = risk_distance * (1.0 + self.slippage_buffer)
        reward_distance_adjusted = reward_distance * (1.0 - self.slippage_buffer)
        
        # Calculate R:R ratio
        rr_ratio = reward_distance_adjusted / risk_distance_adjusted if risk_distance_adjusted > 0 else 0
        
        # Reject if R:R too low
        if rr_ratio < self.min_rr_ratio:
            logger.warning(
                f"Trade rejected: R:R ratio {rr_ratio:.2f} < {self.min_rr_ratio}",
                symbol=symbol,
                entry=entry_price,
                sl=stop_loss_price,
                tp=take_profit_price,
            )
            return None
        
        # Determine position size based on max risk
        max_risk_usd = current_balance * (self.max_risk_pct / 100.0)
        
        # Risk per contract unit
        risk_per_unit = risk_distance_adjusted
        position_size = max_risk_usd / risk_per_unit if risk_per_unit > 0 else 0
        
        # Calculate actual risk and reward amounts (in USD)
        risk_amount = position_size * risk_per_unit
        reward_amount = position_size * reward_distance_adjusted
        
        # Account for taker fees on entry
        fee_cost_entry = (position_size * entry_price) * self.taker_fee
        fee_cost_exit = (position_size * entry_price) * self.taker_fee  # Rough estimate
        total_fee_cost = fee_cost_entry + fee_cost_exit
        
        # Calculate expected value
        loss_probability = 1.0 - win_probability
        expected_value = (win_probability * reward_amount) - (loss_probability * risk_amount) - total_fee_cost
        fee_adjusted_ev = expected_value
        
        # Only accept if EV is positive
        if fee_adjusted_ev <= 0:
            logger.warning(
                f"Trade rejected: Negative EV {fee_adjusted_ev:.2f}",
                symbol=symbol,
                win_prob=win_probability,
            )
            return None
        
        # Calculate risk as % of account
        risk_pct_of_account = (risk_amount / current_balance) * 100.0
        
        # Build risk profile
        risk_profile = TradeRiskProfile(
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            position_size=position_size,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            rr_ratio=rr_ratio,
            expected_value=expected_value,
            win_probability=win_probability,
            fee_adjusted_ev=fee_adjusted_ev,
            atr=atr,
            risk_pct_of_account=risk_pct_of_account,
        )
        
        logger.info(
            "Risk profile calculated",
            symbol=symbol,
            side=side,
            entry=entry_price,
            sl=stop_loss_price,
            tp=take_profit_price,
            position_size=f"{position_size:.4f}",
            rr_ratio=f"{rr_ratio:.2f}",
            ev=f"{fee_adjusted_ev:.2f}",
        )
        
        return risk_profile
    
    def calculate_position_size(
        self,
        risk_amount_usd: float,
        risk_distance: float,
    ) -> float:
        """Calculate position size in base currency given risk amount and distance."""
        if risk_distance <= 0:
            return 0.0
        return risk_amount_usd / risk_distance
    
    def calculate_kelly_fraction(
        self,
        win_probability: float,
        rr_ratio: float,
        kelly_multiplier: float = 0.25,
    ) -> float:
        """
        Calculate Kelly Criterion position size (with dampening).
        
        Kelly % = (p * b - q) / b
        where p = win %, q = loss %, b = odds (rr_ratio)
        
        Typically use 0.25 * Kelly to avoid over-leverage.
        """
        loss_prob = 1.0 - win_probability
        
        if rr_ratio <= 0:
            return 0.0
        
        kelly_pct = (win_probability * rr_ratio - loss_prob) / rr_ratio
        kelly_pct = max(0.0, min(kelly_pct, 1.0))  # Clamp to [0, 1]
        
        # Apply dampening
        position_fraction = kelly_pct * kelly_multiplier
        
        return position_fraction
