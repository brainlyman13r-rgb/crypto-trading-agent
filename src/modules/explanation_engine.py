"""Module 6: Human-Readable Explanation Engine

Synthesizes all module outputs into coherent trade justifications.
"""

import logging
from typing import Optional, List
from datetime import datetime

from src.utils.validators import (
    TradeJustification,
    MarketRegimeOutput,
    TradeSignal,
    MacroSentiment,
    TradeRiskProfile,
    MemoryInsight,
)

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """Generates human-readable trade justifications."""
    
    def __init__(self):
        logger.info("Explanation Engine initialized")
    
    def generate_explanation(
        self,
        symbol: str,
        regime: MarketRegimeOutput,
        signal: TradeSignal,
        sentiment: MacroSentiment,
        risk_profile: Optional[TradeRiskProfile] = None,
        memory: Optional[MemoryInsight] = None,
    ) -> Optional[TradeJustification]:
        """
        Generate comprehensive trade justification.
        
        Args:
            symbol: Trading pair
            regime: Market regime classification
            signal: Technical signal
            sentiment: Macro sentiment
            risk_profile: Risk/reward calculations
            memory: Historical memory insights
        
        Returns:
            TradeJustification with explanation and recommendation
        """
        
        # Generate technical summary
        technical_summary = self._generate_technical_summary(signal, regime)
        
        # Generate macro context
        macro_context = self._generate_macro_context(sentiment)
        
        # Generate memory insights narrative
        memory_insights = self._generate_memory_narrative(memory)
        
        # Generate risk/reward summary
        risk_reward_summary = ""
        if risk_profile:
            risk_reward_summary = self._generate_risk_summary(risk_profile)
        
        # Generate EV calculation summary
        ev_calculation_summary = ""
        if risk_profile:
            ev_calculation_summary = self._generate_ev_summary(risk_profile)
        
        # Determine final recommendation
        recommendation, overall_confidence = self._calculate_recommendation(
            signal, sentiment, risk_profile, memory
        )
        
        # Generate title
        title = self._generate_title(symbol, signal, sentiment)
        
        # Build reasoning chain
        reasoning_chain = [
            f"1. Market Regime: {regime.regime} (confidence: {regime.confidence:.0%})",
            f"2. Technical Signal: {signal.direction} (confidence: {signal.confidence:.0%})",
            f"3. Macro Bias: {'+' if sentiment.bias_score > 0 else ''}{sentiment.bias_score:.2f} ({sentiment.confidence:.0%})",
        ]
        
        if memory:
            reasoning_chain.append(f"4. Historical Success Rate: {memory.success_rate:.0%} ({memory.similar_trades_count} similar trades)")
        
        if risk_profile:
            reasoning_chain.append(f"5. Risk/Reward Ratio: 1:{risk_profile.rr_ratio:.2f}")
            reasoning_chain.append(f"6. Expected Value: ${risk_profile.fee_adjusted_ev:.2f}")
        
        if memory and memory.risk_flag:
            reasoning_chain.append(f"⚠️ Risk Warning: {memory.risk_flag}")
        
        justification = TradeJustification(
            title=title,
            timestamp=datetime.utcnow(),
            technical_summary=technical_summary,
            macro_context=macro_context,
            memory_insights=memory_insights,
            risk_reward_summary=risk_reward_summary,
            ev_calculation_summary=ev_calculation_summary,
            final_recommendation=recommendation,
            reasoning_chain=reasoning_chain,
            confidence_overall=overall_confidence,
        )
        
        logger.info(
            "Trade justification generated",
            symbol=symbol,
            recommendation=recommendation,
            confidence=f"{overall_confidence:.0%}",
        )
        
        return justification
    
    def _generate_technical_summary(self, signal: TradeSignal, regime: MarketRegimeOutput) -> str:
        """Generate technical analysis summary."""
        direction_text = "bullish" if signal.direction == "LONG" else "bearish" if signal.direction == "SHORT" else "neutral"
        
        summary = f"Multi-timeframe {direction_text} confluence: "
        
        tf_status = [f"{tf}={direction}" for tf, direction in signal.timeframe_confluence.items()]
        summary += ", ".join(tf_status)
        
        summary += f". Key triggers: {', '.join(signal.triggers[:3])}. "
        summary += f"Market regime: {regime.regime} with {regime.volatility_level} volatility."
        
        return summary
    
    def _generate_macro_context(self, sentiment: MacroSentiment) -> str:
        """Generate macro sentiment narrative."""
        bias_descriptor = (
            "Extremely bullish" if sentiment.bias_score > 0.6 else
            "Moderately bullish" if sentiment.bias_score > 0.3 else
            "Slightly bullish" if sentiment.bias_score > 0.0 else
            "Neutral" if sentiment.bias_score == 0.0 else
            "Slightly bearish" if sentiment.bias_score > -0.3 else
            "Moderately bearish" if sentiment.bias_score > -0.6 else
            "Extremely bearish"
        )
        
        context = f"Macro bias: {bias_descriptor} ({sentiment.bias_score:+.2f}, confidence: {sentiment.confidence:.0%}). "
        
        if sentiment.key_events:
            context += f"Key drivers: {', '.join(sentiment.key_events[:2])}. "
        
        context += f"Sentiment reasoning: {sentiment.reasoning}"
        
        return context
    
    def _generate_memory_narrative(self, memory: Optional[MemoryInsight]) -> str:
        """Generate historical memory narrative."""
        if not memory or memory.similar_trades_count == 0:
            return "No significant historical precedent available."
        
        narrative = f"Historical analysis: {memory.similar_trades_count} similar setups found over past 90 days. "
        narrative += f"Success rate: {memory.success_rate:.0%}. "
        narrative += f"Average holding time: {memory.avg_holding_time_hours:.1f}h. "
        
        if memory.avg_win_r_multiple:
            narrative += f"Average win: {memory.avg_win_r_multiple:.2f}R, "
        if memory.avg_loss_r_multiple:
            narrative += f"average loss: {memory.avg_loss_r_multiple:.2f}R. "
        
        if memory.lessons:
            narrative += f"Key lessons: {', '.join(memory.lessons[:2])}. "
        
        if memory.risk_flag:
            narrative += f"⚠️ WARNING: {memory.risk_flag}"
        
        return narrative
    
    def _generate_risk_summary(self, risk_profile: TradeRiskProfile) -> str:
        """Generate risk/reward summary."""
        summary = f"""
Entry: ${risk_profile.entry_price:.2f} | Stop: ${risk_profile.stop_loss_price:.2f} | Target: ${risk_profile.take_profit_price:.2f}
Position Size: {risk_profile.position_size:.4f} | Risk: ${risk_profile.risk_amount:.2f} | Reward: ${risk_profile.reward_amount:.2f}
R:R Ratio: 1:{risk_profile.rr_ratio:.2f} | Account Risk: {risk_profile.risk_pct_of_account:.2f}%
        """.strip()
        return summary
    
    def _generate_ev_summary(self, risk_profile: TradeRiskProfile) -> str:
        """Generate EV calculation summary."""
        summary = f"""
Win Probability: {risk_profile.win_probability:.0%} | Loss Probability: {1 - risk_profile.win_probability:.0%}
Expected Gain per Win: ${risk_profile.reward_amount:.2f}
Expected Loss per Loss: ${risk_profile.risk_amount:.2f}
Calculation: ({risk_profile.win_probability:.0%} × ${risk_profile.reward_amount:.2f}) - ({1 - risk_profile.win_probability:.0%} × ${risk_profile.risk_amount:.2f}) = ${risk_profile.fee_adjusted_ev:.2f} EV (after fees)
        """.strip()
        return summary
    
    def _generate_title(self, symbol: str, signal: TradeSignal, sentiment: MacroSentiment) -> str:
        """Generate concise trade title."""
        direction = "LONG" if signal.direction == "LONG" else "SHORT" if signal.direction == "SHORT" else "WAIT"
        
        # Extract primary trigger
        primary_trigger = signal.triggers[0].replace("_", " ").title() if signal.triggers else "Setup"
        
        # Add sentiment tone
        macro_tone = "+ Bullish Macro" if sentiment.bias_score > 0.3 else "- Bearish Macro" if sentiment.bias_score < -0.3 else ""
        
        title = f"{symbol} {direction}: {primary_trigger}"
        if macro_tone:
            title += f" {macro_tone}"
        
        return title
    
    def _calculate_recommendation(self, signal: TradeSignal, sentiment: MacroSentiment, risk_profile: Optional[TradeRiskProfile], memory: Optional[MemoryInsight]) -> tuple:
        """Calculate final recommendation and confidence."""
        
        recommendation = "WAIT"  # Default conservative
        confidence = 0.0
        
        # Base recommendation on signal direction and strength
        if signal.direction != "NEUTRAL":
            recommendation = "EXECUTE" if signal.direction == "LONG" or signal.direction == "SHORT" else "WAIT"
        else:
            recommendation = "WAIT"
        
        # Calculate composite confidence
        components = []
        
        # Signal confidence (weight: 0.35)
        components.append(("signal", signal.confidence, 0.35))
        
        # Sentiment alignment (weight: 0.20)
        sentiment_alignment = 0.5
        if signal.direction == "LONG" and sentiment.bias_score > 0.2:
            sentiment_alignment = 0.8
        elif signal.direction == "SHORT" and sentiment.bias_score < -0.2:
            sentiment_alignment = 0.8
        components.append(("sentiment", sentiment_alignment, 0.20))
        
        # Risk/reward EV (weight: 0.25)
        if risk_profile:
            if risk_profile.fee_adjusted_ev > 0 and risk_profile.rr_ratio >= 1.5:
                ev_confidence = min(0.9, 0.5 + (risk_profile.fee_adjusted_ev / 100.0))
            else:
                ev_confidence = 0.3
            components.append(("ev", ev_confidence, 0.25))
        
        # Memory historical success (weight: 0.20)
        if memory and memory.similar_trades_count > 0:
            memory_confidence = memory.success_rate
            if memory.risk_flag:
                memory_confidence *= 0.5  # Reduce confidence if risk flag present
            components.append(("memory", memory_confidence, 0.20))
        
        # Calculate weighted confidence
        total_weight = sum(w for _, _, w in components)
        weighted_confidence = sum(c * w for _, c, w in components) / total_weight if total_weight > 0 else 0.0
        
        # Adjust recommendation based on confidence
        if recommendation == "EXECUTE" and weighted_confidence < 0.55:
            recommendation = "WAIT"
        elif recommendation == "WAIT" and weighted_confidence > 0.70 and signal.confidence > 0.75:
            recommendation = "EXECUTE"
        
        return recommendation, weighted_confidence
