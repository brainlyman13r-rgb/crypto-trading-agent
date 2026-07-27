"""Main Trading Agent Orchestrator

Coordinates all 7 modules into a unified trading decision pipeline.
"""

import logging
import pandas as pd
from typing import Optional
from datetime import datetime

from src.modules.ev_engine import EVEngine
from src.modules.regime_classifier import MarketRegimeClassifier
from src.modules.signal_generator import SignalGenerator
from src.modules.llm_sentiment import LLMSentimentSynthesizer, OpenAIAdapter
from src.modules.memory_system import HistoricalMemory
from src.modules.explanation_engine import ExplanationEngine
from src.modules.risk_guardrails import RiskGuardrails
from src.integrations.exchange_adapter import ExchangeAdapter
from src.utils.validators import PreTradeAnalysis
from src.utils.logger import setup_logging, get_logger

logger = logging.getLogger(__name__)


class TradingAgent:
    """Elite Quantitative Trading Agent - All 7 modules orchestrated."""
    
    def __init__(
        self,
        account_balance: float = 10000.0,
        exchange: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        openai_key: Optional[str] = None,
        sandbox: bool = True,
    ):
        """
        Initialize Trading Agent.
        
        Args:
            account_balance: Starting capital
            exchange: Exchange name ("binance", "bybit", "blofin")
            api_key: Exchange API key
            api_secret: Exchange API secret
            openai_key: OpenAI API key for LLM sentiment
            sandbox: Use testnet mode
        """
        # Initialize logger
        setup_logging(log_dir="logs", level="INFO")
        
        # Initialize all 7 modules
        self.ev_engine = EVEngine(
            account_size_usd=account_balance,
            max_risk_per_trade_pct=2.0,
            min_rr_ratio=1.5,
        )
        
        self.regime_classifier = MarketRegimeClassifier()
        self.signal_generator = SignalGenerator()
        
        llm_adapter = OpenAIAdapter(api_key=openai_key) if openai_key else None
        self.sentiment_synthesizer = LLMSentimentSynthesizer(llm_adapter=llm_adapter)
        
        self.memory = HistoricalMemory()
        self.explanation_engine = ExplanationEngine()
        
        self.risk_guardrails = RiskGuardrails(
            account_balance=account_balance,
            max_daily_drawdown_pct=5.0,
            max_per_trade_risk_pct=2.0,
        )
        
        self.exchange = ExchangeAdapter(
            exchange_name=exchange,
            api_key=api_key,
            api_secret=api_secret,
            sandbox=sandbox,
        )
        
        logger.info(
            "Trading Agent initialized",
            balance=account_balance,
            exchange=exchange,
            sandbox=sandbox,
        )
    
    def analyze_and_execute(
        self,
        symbol: str,
        news_headlines: Optional[list] = None,
        macro_events: Optional[list] = None,
        social_sentiment: Optional[dict] = None,
        paper_mode: bool = True,
    ) -> Optional[PreTradeAnalysis]:
        """
        Complete pre-trade analysis pipeline.
        
        Args:
            symbol: Trading pair
            news_headlines: Recent news headlines
            macro_events: Macro calendar events
            social_sentiment: Social sentiment dict
            paper_mode: Simulate order (don't execute)
        
        Returns:
            PreTradeAnalysis with full justification
        """
        
        # Step 1: Fetch market data
        logger.info(f"Analyzing {symbol}...")
        candles_15m = self.exchange.fetch_ohlcv(symbol, "15m", limit=100)
        candles_1h = self.exchange.fetch_ohlcv(symbol, "1h", limit=100)
        candles_4h = self.exchange.fetch_ohlcv(symbol, "4h", limit=100)
        
        if not all([candles_15m, candles_1h, candles_4h]):
            logger.error("Failed to fetch candle data")
            return None
        
        # Convert to DataFrames
        df_15m = self._candles_to_df(candles_15m)
        df_1h = self._candles_to_df(candles_1h)
        df_4h = self._candles_to_df(candles_4h)
        
        # Step 2: Module 2 - Market Regime Classification
        regime = self.regime_classifier.classify(df_4h)
        if not regime:
            logger.error("Regime classification failed")
            return None
        
        # Step 3: Module 3 - Signal Generation
        signal = self.signal_generator.generate_signal(df_15m, df_1h, df_4h)
        if not signal:
            logger.error("Signal generation failed")
            return None
        
        # Step 4: Module 4 - LLM Sentiment Synthesis
        sentiment = self.sentiment_synthesizer.synthesize(
            news_headlines=news_headlines or [],
            macro_events=macro_events or [],
            social_sentiment=social_sentiment or {},
        )
        
        # Step 5: Module 5 - Memory Lookup
        memory = self.memory.query_similar_setups(
            symbol=symbol,
            entry_regime=regime.regime,
            technical_triggers=signal.triggers,
        )
        
        # Step 6: Module 1 - EV Calculation & Risk Sizing
        current_price = df_15m['close'].iloc[-1]
        atr = df_4h['atr'].iloc[-1] if 'atr' in df_4h.columns else 0.0
        
        # Determine entry/SL/TP based on signal
        if signal.direction == "LONG":
            entry_price = current_price
            stop_loss_price = entry_price - (atr * 1.5)
            take_profit_price = entry_price + (atr * 3.0)
            win_prob = 0.55 + (sentiment.bias_score * 0.1)  # Boost by sentiment
        else:
            entry_price = current_price
            stop_loss_price = entry_price + (atr * 1.5)
            take_profit_price = entry_price - (atr * 3.0)
            win_prob = 0.50 - (sentiment.bias_score * 0.1)
        
        win_prob = max(0.3, min(0.7, win_prob))  # Clamp to reasonable range
        
        risk_profile = self.ev_engine.calculate_risk_profile(
            symbol=symbol,
            side="BUY" if signal.direction == "LONG" else "SELL",
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            win_probability=win_prob,
            atr=atr,
        )
        
        if not risk_profile:
            logger.warning("Risk profile rejected (low EV or R:R)")
            risk_profile = None  # Allow analysis to continue for review
        
        # Step 7: Module 7 - Risk Guardrails Check
        guardrails = self.risk_guardrails.check_pre_trade_guardrails(
            symbol=symbol,
            trade_risk_pct=risk_profile.risk_pct_of_account if risk_profile else 0.0,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            atr=atr,
        )
        
        # Step 8: Module 6 - Generate Explanation
        justification = self.explanation_engine.generate_explanation(
            symbol=symbol,
            regime=regime,
            signal=signal,
            sentiment=sentiment,
            risk_profile=risk_profile,
            memory=memory,
        )
        
        # Determine overall pass
        overall_pass = (
            guardrails.passed
            and risk_profile is not None
            and justification.final_recommendation == "EXECUTE"
        )
        
        # Build PreTradeAnalysis
        analysis = PreTradeAnalysis(
            timestamp=datetime.utcnow(),
            symbol=symbol,
            market_regime=regime,
            technical_signal=signal,
            macro_sentiment=sentiment,
            memory_insight=memory,
            risk_profile=risk_profile,
            risk_guardrails=guardrails,
            justification=justification,
            overall_pass=overall_pass,
        )
        
        # Log full justification
        self._log_trade_justification(analysis)
        
        # Execute trade if approved (paper or live)
        if overall_pass and not paper_mode:
            self._execute_trade(analysis)
        
        return analysis
    
    def _candles_to_df(self, candles: list) -> pd.DataFrame:
        """Convert CCXT candles to DataFrame."""
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def _log_trade_justification(self, analysis: PreTradeAnalysis):
        """Log complete trade justification to file and console."""
        justification = analysis.justification
        
        log_message = f"""
╔════════════════════════════════════════════════════════════════════╗
║ TRADE ANALYSIS REPORT - {justification.title}
║ {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
╚════════════════════════════════════════════════════════════════════╝

📊 TECHNICAL ANALYSIS:
{justification.technical_summary}

🌍 MACRO CONTEXT:
{justification.macro_context}

🧠 HISTORICAL MEMORY:
{justification.memory_insights}

💰 RISK/REWARD SETUP:
{justification.risk_reward_summary}

📈 EXPECTED VALUE CALCULATION:
{justification.ev_calculation_summary}

🔗 REASONING CHAIN:
" + "\n".join(justification.reasoning_chain) + f"""

✅ RECOMMENDATION: {justification.final_recommendation}
   Overall Confidence: {justification.confidence_overall:.0%}

╚════════════════════════════════════════════════════════════════════╝
        """
        
        logger.info(log_message)
        print(log_message)
    
    def _execute_trade(self, analysis: PreTradeAnalysis):
        """Execute trade on exchange."""
        logger.info(f"Executing trade: {analysis.justification.title}")
        # Implementation would go here
    
    def get_status(self) -> dict:
        """Get current trading system status."""
        return {
            "guardrails_status": self.risk_guardrails.get_status(),
            "memory_stats": self.memory.get_statistics(),
        }
