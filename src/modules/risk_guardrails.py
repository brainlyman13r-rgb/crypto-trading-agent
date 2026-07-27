"""Module 7: Hard Risk Guardrails

Enforces non-negotiable risk limits and circuit breakers.
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from src.utils.validators import RiskGuardrailsOutput

logger = logging.getLogger(__name__)


class RiskGuardrails:
    """Enforces hard risk limits and circuit breakers."""
    
    def __init__(
        self,
        account_balance: float,
        max_daily_drawdown_pct: float = 5.0,
        max_per_trade_risk_pct: float = 2.0,
        min_atr_stop_distance: float = 0.001,  # 0.1% of price
        max_open_positions: int = 3,
        position_timeout_hours: int = 48,
    ):
        """
        Initialize Risk Guardrails.
        
        Args:
            account_balance: Current account balance
            max_daily_drawdown_pct: Maximum daily loss percentage
            max_per_trade_risk_pct: Maximum risk per trade
            min_atr_stop_distance: Minimum stop-loss distance (as fraction of price)
            max_open_positions: Maximum simultaneous open positions
            position_timeout_hours: Auto-close positions after this many hours
        """
        self.account_balance = account_balance
        self.max_daily_drawdown_pct = max_daily_drawdown_pct
        self.max_per_trade_risk_pct = max_per_trade_risk_pct
        self.min_atr_stop_distance = min_atr_stop_distance
        self.max_open_positions = max_open_positions
        self.position_timeout_hours = position_timeout_hours
        
        # State tracking
        self.daily_pnl = 0.0
        self.daily_start_balance = account_balance
        self.daily_start_time = datetime.now()
        self.open_positions = []
        
        logger.info(
            "Risk Guardrails initialized",
            max_daily_dd=max_daily_drawdown_pct,
            max_per_trade_risk=max_per_trade_risk_pct,
        )
    
    def check_pre_trade_guardrails(
        self,
        symbol: str,
        trade_risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
        atr: float,
    ) -> Optional[RiskGuardrailsOutput]:
        """
        Check all pre-trade guardrails before allowing order submission.
        
        Args:
            symbol: Trading pair
            trade_risk_pct: Risk as % of account
            entry_price: Entry price
            stop_loss_price: Stop loss price
            atr: Average True Range
        
        Returns:
            RiskGuardrailsOutput with pass/fail status
        """
        
        current_drawdown = self._calculate_current_drawdown()
        violations = []
        warnings = []
        checks_performed = {}
        
        # Check 1: Daily Drawdown Circuit Breaker
        checks_performed["daily_drawdown_check"] = True
        if current_drawdown > self.max_daily_drawdown_pct:
            violations.append(
                f"Daily drawdown {current_drawdown:.2f}% exceeds limit {self.max_daily_drawdown_pct:.2f}%. "
                "Circuit breaker ACTIVE: No new trades until reset."
            )
        elif current_drawdown > self.max_daily_drawdown_pct * 0.8:
            warnings.append(
                f"Daily drawdown {current_drawdown:.2f}% approaching circuit breaker limit. "
                f"Remaining: {self.max_daily_drawdown_pct - current_drawdown:.2f}%"
            )
        
        # Check 2: Per-Trade Risk Check
        checks_performed["per_trade_risk_check"] = True
        if trade_risk_pct > self.max_per_trade_risk_pct:
            violations.append(
                f"Trade risk {trade_risk_pct:.2f}% exceeds limit {self.max_per_trade_risk_pct:.2f}%"
            )
        elif trade_risk_pct > self.max_per_trade_risk_pct * 0.9:
            warnings.append(
                f"Trade risk {trade_risk_pct:.2f}% is at {(trade_risk_pct/self.max_per_trade_risk_pct):.0%} of limit"
            )
        
        # Check 3: ATR-Based Stop Distance
        checks_performed["atr_stop_distance_check"] = True
        stop_distance_pct = abs(entry_price - stop_loss_price) / entry_price
        min_stop_distance_pct = max(self.min_atr_stop_distance, atr / entry_price if atr > 0 else 0)
        
        if stop_distance_pct < min_stop_distance_pct:
            violations.append(
                f"Stop distance {stop_distance_pct:.4f} too close; minimum {min_stop_distance_pct:.4f} "
                f"(based on ATR {atr:.2f})"
            )
        
        # Check 4: Max Open Positions
        checks_performed["max_positions_check"] = True
        if len(self.open_positions) >= self.max_open_positions:
            violations.append(
                f"Maximum open positions ({self.max_open_positions}) reached. "
                f"Close a position before entering new trade."
            )
        
        # Check 5: Position Timeout (auto-close old positions)
        checks_performed["position_timeout_check"] = True
        self._check_position_timeouts()
        
        # Determine pass/fail
        passed = len(violations) == 0
        
        output = RiskGuardrailsOutput(
            passed=passed,
            checks_performed=checks_performed,
            violations=violations,
            warnings=warnings,
            current_drawdown_pct=current_drawdown,
            daily_loss_usd=abs(self.daily_pnl) if self.daily_pnl < 0 else 0.0,
            account_balance=self.account_balance,
        )
        
        log_level = "error" if not passed else "warning" if warnings else "info"
        getattr(logger, log_level)(
            "Pre-trade guardrails check",
            symbol=symbol,
            passed=passed,
            violations_count=len(violations),
            warnings_count=len(warnings),
        )
        
        return output
    
    def record_trade_open(self, trade_id: str, symbol: str, entry_time: datetime):
        """Record when a new position is opened."""
        self.open_positions.append({
            "trade_id": trade_id,
            "symbol": symbol,
            "entry_time": entry_time,
        })
        logger.info(f"Trade opened: {trade_id} ({symbol}). Total open: {len(self.open_positions)}")
    
    def record_trade_close(self, trade_id: str, pnl: float):
        """Record when a position is closed and update P&L."""
        self.open_positions = [p for p in self.open_positions if p["trade_id"] != trade_id]
        
        self.daily_pnl += pnl
        self.account_balance += pnl
        
        logger.info(
            f"Trade closed: {trade_id}. P&L: ${pnl:+.2f}. Daily P&L: ${self.daily_pnl:+.2f}"
        )
    
    def reset_daily_metrics(self):
        """Reset daily metrics (called at start of each trading day)."""
        self.daily_pnl = 0.0
        self.daily_start_balance = self.account_balance
        self.daily_start_time = datetime.now()
        logger.info("Daily metrics reset")
    
    def _calculate_current_drawdown(self) -> float:
        """Calculate current daily drawdown as percentage."""
        if self.daily_pnl >= 0:
            return 0.0
        
        drawdown_pct = (abs(self.daily_pnl) / self.daily_start_balance) * 100.0
        return drawdown_pct
    
    def _check_position_timeouts(self):
        """Auto-close positions that have exceeded timeout."""
        now = datetime.now()
        expired = []
        
        for pos in self.open_positions:
            elapsed = (now - pos["entry_time"]).total_seconds() / 3600  # Hours
            if elapsed > self.position_timeout_hours:
                expired.append(pos["trade_id"])
        
        if expired:
            logger.warning(
                f"Force-closing {len(expired)} positions due to timeout: {', '.join(expired)}"
            )
            self.open_positions = [p for p in self.open_positions if p["trade_id"] not in expired]
    
    def get_status(self) -> Dict:
        """Get current risk status."""
        return {
            "account_balance": self.account_balance,
            "daily_pnl": self.daily_pnl,
            "current_drawdown_pct": self._calculate_current_drawdown(),
            "open_positions_count": len(self.open_positions),
            "max_open_positions": self.max_open_positions,
            "circuit_breaker_active": self._calculate_current_drawdown() > self.max_daily_drawdown_pct,
        }
