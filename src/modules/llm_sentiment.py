"""Module 4: LLM-Driven Market Sentiment Synthesizer

Ingests news, macro events, and social sentiment to produce structured macro bias scoring.
Supports OpenAI, Anthropic, or local LLM backends.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel

from src.utils.validators import MacroSentiment

logger = logging.getLogger(__name__)


class LLMAdapter:
    """Abstract LLM adapter for sentiment analysis."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        self.api_key = api_key
        self.model = model
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text and return score (-1.0 to 1.0)."""
        raise NotImplementedError
    
    def generate_macro_context(self, news_headlines: List[str], events: List[Dict]) -> str:
        """Generate macro context explanation."""
        raise NotImplementedError


class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT adapter for sentiment analysis."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        super().__init__(api_key, model)
        try:
            import openai
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            logger.warning("OpenAI library not installed; sentiment analysis will use heuristic fallback")
            self.client = None
    
    def analyze_sentiment(self, text: str) -> float:
        """Use GPT to analyze sentiment."""
        if not self.client:
            return self._heuristic_sentiment(text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a crypto market sentiment analyst. Respond with a single float between -1.0 (extreme bearish) and 1.0 (extreme bullish)."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the sentiment of this market news/event: {text}"
                    }
                ],
                max_tokens=10,
                temperature=0.3,
            )
            
            score_str = response.choices[0].message.content.strip()
            score = float(score_str)
            return max(-1.0, min(1.0, score))
        except Exception as e:
            logger.error(f"OpenAI API error: {e}; falling back to heuristic")
            return self._heuristic_sentiment(text)
    
    def _heuristic_sentiment(self, text: str) -> float:
        """Fallback heuristic sentiment analysis."""
        text_lower = text.lower()
        
        bullish_words = [
            "bull", "up", "rally", "surge", "profit", "recovery", "positive",
            "bullish", "strong", "gains", "breakout", "pump", "optimistic",
        ]
        bearish_words = [
            "bear", "down", "crash", "decline", "loss", "negative",
            "bearish", "weak", "sell-off", "dump", "pessimistic", "fear",
        ]
        
        bullish_score = sum(1 for word in bullish_words if word in text_lower)
        bearish_score = sum(1 for word in bearish_words if word in text_lower)
        
        total = bullish_score + bearish_score
        if total == 0:
            return 0.0
        
        sentiment = (bullish_score - bearish_score) / total
        return max(-1.0, min(1.0, sentiment))


class LLMSentimentSynthesizer:
    """Synthesizes market sentiment from multiple sources using LLM."""
    
    def __init__(self, llm_adapter: Optional[LLMAdapter] = None):
        """
        Initialize sentiment synthesizer.
        
        Args:
            llm_adapter: LLM backend (OpenAI, Anthropic, etc.)
                        If None, uses heuristic analysis only.
        """
        self.llm = llm_adapter or OpenAIAdapter(api_key="")
        logger.info("LLM Sentiment Synthesizer initialized")
    
    def synthesize(
        self,
        news_headlines: Optional[List[str]] = None,
        macro_events: Optional[List[Dict]] = None,
        social_sentiment: Optional[Dict[str, float]] = None,
        recent_price_action: Optional[Dict] = None,
    ) -> Optional[MacroSentiment]:
        """
        Synthesize complete macro sentiment.
        
        Args:
            news_headlines: List of recent news headlines
            macro_events: List of dicts with {"event": str, "time": datetime, "impact": "HIGH"/"MEDIUM"/"LOW"}
            social_sentiment: Dict with {"twitter": 0.6, "discord": 0.5, ...}
            recent_price_action: Dict with {"sma_slope": 0.01, "rsi": 45, ...}
        
        Returns:
            MacroSentiment with bias_score and reasoning
        """
        news_headlines = news_headlines or []
        macro_events = macro_events or []
        social_sentiment = social_sentiment or {}
        recent_price_action = recent_price_action or {}
        
        # Analyze news headlines
        news_scores = []
        key_events = []
        
        for headline in news_headlines:
            score = self.llm.analyze_sentiment(headline)
            news_scores.append(score)
            
            # Flag major moves
            if abs(score) > 0.7:
                key_events.append(headline)
        
        avg_news_sentiment = sum(news_scores) / len(news_scores) if news_scores else 0.0
        
        # Analyze macro calendar events
        event_scores = []
        for event in macro_events:
            event_text = f"{event.get('event', '')} (Impact: {event.get('impact', 'MEDIUM')})"
            score = self.llm.analyze_sentiment(event_text)
            event_scores.append(score)
            if event.get('impact') == 'HIGH':
                key_events.append(event.get('event', ''))
        
        avg_event_sentiment = sum(event_scores) / len(event_scores) if event_scores else 0.0
        
        # Aggregate social sentiment
        avg_social_sentiment = sum(social_sentiment.values()) / len(social_sentiment) if social_sentiment else 0.0
        
        # Incorporate recent price action
        price_action_score = 0.0
        if recent_price_action:
            if recent_price_action.get('sma_slope', 0) > 0.001:
                price_action_score += 0.3
            elif recent_price_action.get('sma_slope', 0) < -0.001:
                price_action_score -= 0.3
            
            rsi = recent_price_action.get('rsi', 50)
            if rsi < 30:
                price_action_score += 0.2  # Oversold = potential reversal up
            elif rsi > 70:
                price_action_score -= 0.2  # Overbought = potential reversal down
        
        # Weighted average of all sources
        weights = {
            'news': 0.35,
            'events': 0.25,
            'social': 0.25,
            'price': 0.15,
        }
        
        bias_score = (
            weights['news'] * avg_news_sentiment
            + weights['events'] * avg_event_sentiment
            + weights['social'] * avg_social_sentiment
            + weights['price'] * price_action_score
        )
        
        bias_score = max(-1.0, min(1.0, bias_score))
        
        # Calculate confidence (how much data we had)
        data_points = len(news_scores) + len(event_scores) + len(social_sentiment)
        confidence = min(1.0, 0.3 + (data_points / 50.0))  # Start at 0.3 baseline
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            bias_score,
            avg_news_sentiment,
            avg_event_sentiment,
            avg_social_sentiment,
            key_events,
        )
        
        output = MacroSentiment(
            bias_score=bias_score,
            key_events=key_events[:5],  # Top 5 events
            sentiment_sources={
                "news": avg_news_sentiment,
                "events": avg_event_sentiment,
                "social": avg_social_sentiment,
                "price_action": price_action_score,
            },
            reasoning=reasoning,
            confidence=confidence,
        )
        
        logger.info(
            "Macro sentiment synthesized",
            bias_score=f"{bias_score:.2f}",
            confidence=f"{confidence:.2f}",
            key_events_count=len(key_events),
        )
        
        return output
    
    def _generate_reasoning(self, bias: float, news: float, events: float, social: float, key_events: List[str]) -> str:
        """Generate human-readable reasoning for bias score."""
        if bias > 0.6:
            base = "Extremely bullish bias: Multiple tailwinds identified."
        elif bias > 0.3:
            base = "Moderately bullish bias: Mixed signals with upside bias."
        elif bias > 0.0:
            base = "Slightly bullish bias: Positive technical setup with cautious macro."
        elif bias > -0.3:
            base = "Slightly bearish bias: Headwinds emerging but support present."
        elif bias > -0.6:
            base = "Moderately bearish bias: Risk-off sentiment with weakness."
        else:
            base = "Extremely bearish bias: Multiple downside risks active."
        
        if key_events:
            base += f" Key drivers: {', '.join(key_events[:2])}."
        
        return base
