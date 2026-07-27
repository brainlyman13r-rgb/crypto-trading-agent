"""Pydantic models and validators for the trading system."""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ==================== Market Regime ====================
class MarketRegimeOutput(BaseModel):
    """Output from Market Regime Classifier (Module 2)."""
    regime: Literal["strong_bull", "bull", "bear", "sideways", "squeeze_breakout"]
    confidence: float = Field(ge=0.0, le=1.0)
    volatility_level: Literal["low", "medium", "high", "extreme"]
    key_levels: Dict[str, float] = {}
    description: str = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "regime": "strong_bull",
                "confidence": 0.85,
                "volatility_level": "medium",
                "key_levels": {"resistance": 45000, "support": 42000},
                "description": "Strong uptrend with healthy pullbacks"
            }
        }
    }


# ==================== Technical Signals ====================
class TradeSignal(BaseModel):
    """Output from Signal Generator (Module 3)."""
    direction: Literal["LONG", "SHORT", "NEUTRAL"]
    confidence: float = Field(ge=0.0, le=1.0)
    triggers: List[str] = []
    timeframe_confluence: Dict[str, str] = {}
    strength_score: float = Field(ge=-1.0, le=1.0)
    description: str = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "direction": "LONG",
                "confidence": 0.78,
                "triggers": ["rsi_oversold_15m", "ma_bullish_cross_1h", "vol_breakout"],
                "timeframe_confluence": {"15m": "LONG", "1h": "LONG", "4h": "NEUTRAL"},
                "strength_score": 0.72,
                "description": "Multi-timeframe bullish confluence"
            }
        }
    }


# ==================== LLM Sentiment ====================
class MacroSentiment(BaseModel):
    """Output from LLM Sentiment Synthesizer (Module 4)."""
    bias_score: float = Field(ge=-1.0, le=1.0)
    key_events: List[str] = []
    sentiment_sources: Dict[str, float] = {}
    reasoning: str = ""
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "bias_score": 0.65,
                "key_events": ["Fed pivot signal", "Positive inflation data"],
                "sentiment_sources": {"news": 0.72, "social": 0.58, "macro": 0.68},
                "reasoning": "Recent Fed comments suggest dovish pivot, supportive for risk assets",
                "confidence": 0.75
            }
        }
    }


# ==================== Historical Memory ====================
class MemoryInsight(BaseModel):
    """Output from Historical Memory System (Module 5)."""
    similar_trades_count: int
    success_rate: float = Field(ge=0.0, le=1.0)
    lessons: List[str] = []
    risk_flag: Optional[str] = None
    avg_holding_time_hours: Optional[float] = None
    avg_win_r_multiple: Optional[float] = None
    avg_loss_r_multiple: Optional[float] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "similar_trades_count": 12,
                "success_rate": 0.67,
                "lessons": [
                    "Similar setups work best in early US session",
                    "Avoid entries within 2 hours of major news releases"
                ],
                "risk_flag": None,
                "avg_holding_time_hours": 4.5,
                "avg_win_r_multiple": 2.1,
                "avg_loss_r_multiple": 1.0
            }
        }
    }


# ==================== Risk Profile ====================
class TradeRiskProfile(BaseModel):
    """Output from EV Engine (Module 1)."""
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    position_size: float
    risk_amount: float
    reward_amount: float
    rr_ratio: float = Field(ge=0.5, le=10.0)
    expected_value: float
    win_probability: float = Field(ge=0.0, le=1.0)
    fee_adjusted_ev: float
    atr: float
    risk_pct_of_account: float = Field(ge=0.0, le=5.0)

    @field_validator('rr_ratio')
    @classmethod
    def validate_rr_ratio(cls, v):
        if v < 1.0:
            raise ValueError(f"R:R ratio must be >= 1.0, got {v}")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "entry_price": 44500.0,
                "stop_loss_price": 43200.0,
                "take_profit_price": 46000.0,
                "position_size": 0.05,
                "risk_amount": 65.0,
                "reward_amount": 150.0,
                "rr_ratio": 2.31,
                "expected_value": 47.5,
                "win_probability": 0.58,
                "fee_adjusted_ev": 43.2,
                "atr": 850.0,
                "risk_pct_of_account": 1.3
            }
        }
    }


# ==================== Trade Justification ====================
class TradeJustification(BaseModel):
    """Output from Explanation Engine (Module 6)."""
    title: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    technical_summary: str
    macro_context: str
    memory_insights: str
    risk_reward_summary: str
    ev_calculation_summary: str
    final_recommendation: Literal["EXECUTE", "WAIT", "REJECT"]
    reasoning_chain: List[str] = []
    confidence_overall: float = Field(ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "BTC LONG: Fed pivot + RSI oversold + 4h resistance hold",
                "technical_summary": "RSI(14) at 28 on 15m (oversold), bullish MA cross on 1h, price holding above 4h support",
                "macro_context": "Macro bias score +0.68 (dovish Fed signals). Positive sentiment from news aggregates.",
                "memory_insights": "12 similar setups in past 90d: 67% win rate. Avg hold: 4.5h. Best outcomes in US session.",
                "risk_reward_summary": "Entry 44500 | SL 43200 | TP 46000 | R:R 2.31:1 | Position size 0.05 BTC | Risk 1.3% account",
                "ev_calculation_summary": "Win% 58% | Avg Win $150 | Avg Loss $65 | EV = 0.58*150 - 0.42*65 = $43.2/trade (after fees)",
                "final_recommendation": "EXECUTE",
                "confidence_overall": 0.76
            }
        }
    }


# ==================== Risk Guardrails ====================
class RiskGuardrailsOutput(BaseModel):
    """Output from Risk Guardrails Checker (Module 7)."""
    passed: bool
    checks_performed: Dict[str, bool]
    violations: List[str] = []
    warnings: List[str] = []
    current_drawdown_pct: float
    daily_loss_usd: float
    account_balance: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "passed": True,
                "checks_performed": {
                    "daily_drawdown_check": True,
                    "per_trade_risk_check": True,
                    "atr_stop_distance_check": True,
                    "circuit_breaker_check": True
                },
                "violations": [],
                "warnings": ["Daily loss is 3.2%, approaching 5% circuit breaker"],
                "current_drawdown_pct": 3.2,
                "daily_loss_usd": 320.0,
                "account_balance": 10000.0
            }
        }
    }


# ==================== Complete Trade Execution Package ====================
class PreTradeAnalysis(BaseModel):
    """Complete package of all pre-trade analysis outputs."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str
    market_regime: MarketRegimeOutput
    technical_signal: TradeSignal
    macro_sentiment: MacroSentiment
    memory_insight: Optional[MemoryInsight] = None
    risk_profile: Optional[TradeRiskProfile] = None
    risk_guardrails: RiskGuardrailsOutput
    justification: TradeJustification
    overall_pass: bool


# ==================== Trade Execution ====================
class TradeExecution(BaseModel):
    """Record of a trade that was executed."""
    trade_id: str
    timestamp_entry: datetime
    symbol: str
    side: Literal["BUY", "SELL"]
    entry_price: float
    position_size: float
    stop_loss_price: float
    take_profit_price: float
    rr_ratio: float
    expected_value: float
    order_ids: Dict[str, str]
    status: Literal["OPEN", "PARTIAL", "CLOSED"]


# ==================== Trade Closure & Reflection ====================
class TradeReflection(BaseModel):
    """Post-trade reflection and lessons learned."""
    trade_id: str
    timestamp_entry: datetime
    timestamp_exit: datetime
    symbol: str
    side: Literal["BUY", "SELL"]
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    pnl_pct: float
    r_multiple: float
    holding_time_hours: float
    outcome: Literal["WIN", "LOSS", "BREAKEVEN"]
    
    # Reflection Analysis
    entry_regime: str
    exit_regime: str
    technical_triggers_fired: List[str]
    why_won_or_lost: str  # LLM-generated explanation
    key_lessons: List[str]
    regime_change_during_hold: bool
