"""Adaptive AI-Driven Cryptocurrency Trading Agent"""

__version__ = "1.0.0"
__author__ = "Elite Quantitative Trading Systems"

from src.modules.ev_engine import EVEngine
from src.modules.regime_classifier import MarketRegimeClassifier
from src.modules.signal_generator import SignalGenerator
from src.modules.llm_sentiment import LLMSentimentSynthesizer
from src.modules.memory_system import HistoricalMemory
from src.modules.explanation_engine import ExplanationEngine
from src.modules.risk_guardrails import RiskGuardrails

__all__ = [
    "EVEngine",
    "MarketRegimeClassifier",
    "SignalGenerator",
    "LLMSentimentSynthesizer",
    "HistoricalMemory",
    "ExplanationEngine",
    "RiskGuardrails",
]
