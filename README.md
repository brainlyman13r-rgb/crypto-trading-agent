# Adaptive AI-Driven Cryptocurrency Trading Agent

**Elite Quantitative Trading System** combining algorithmic rigor, LLM-based market synthesis, and long-term historical memory for sustainable retail trading edge.

## 🧠 System Philosophy

This is NOT a simple indicator script or unguided AI model. It's a **Hybrid Multi-Agent System** that:
- ✅ Bases all trades on Positive Expected Value (EV)
- ✅ Dynamically adapts to market regimes (Bull, Bear, Sideways, Squeeze)
- ✅ Leverages multi-timeframe technical confluence
- ✅ Incorporates LLM-driven macro sentiment analysis
- ✅ Maintains historical trade memory with self-reflection
- ✅ Enforces non-negotiable hard risk guardrails
- ✅ Generates human-readable trade justifications before execution

---

## 📦 Core Modules

### Module 1: EV Engine & Risk Management
Positive Expected Value calculator with dynamic risk-to-reward adjustment (min 1:2 R:R).

### Module 2: Market Regime Classifier
Automatic detection of Strong Bull, Bear, Sideways, or Squeeze/Breakout conditions.

### Module 3: Quantitative Signal Generation
Multi-timeframe technical analysis (RSI, MA Envelopes, Volume, Funding Rates, Liquidations).

### Module 4: LLM Research & Sentiment Synthesizer
Structured macro bias scoring (-1.0 to +1.0) from news, announcements, and social sentiment.

### Module 5: Historical Memory & Self-Reflection
Vector database (ChromaDB/SQLite) storing and learning from past trades.

### Module 6: Human-Readable Explanation Engine
Pre-trade justification with technical triggers, macro bias, memory insights, and exact risk params.

### Module 7: Hard Risk Guardrails
Max 1–2% per-trade risk, ATR-based stops, 5% daily circuit breaker, paper-trading support.

---

## 📂 Project Structure

```
crypto-trading-agent/
├── README.md
├── ARCHITECTURE.md                          # System architecture & data flow
├── DEPLOYMENT.md                            # Step-by-step testnet setup
├── requirements.txt                         # Python dependencies
├── config/
│   ├── settings.yaml                        # API keys, market params, risk settings
│   └── market_regimes.yaml                  # Regime thresholds
├── src/
│   ├── __init__.py
│   ├── main.py                              # Entry point
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── ev_engine.py                     # Module 1: EV & Risk Management
│   │   ├── regime_classifier.py             # Module 2: Market Regime Detection
│   │   ├── signal_generator.py              # Module 3: Quantitative Signals
│   │   ├── llm_sentiment.py                 # Module 4: LLM & Sentiment
│   │   ├── memory_system.py                 # Module 5: Historical Memory
│   │   ├── explanation_engine.py            # Module 6: Human-Readable Explanations
│   │   └── risk_guardrails.py               # Module 7: Risk Guardrails
│   ├── integrations/
│   │   ├── exchange_adapter.py              # CCXT abstraction layer
│   │   └── llm_adapter.py                   # OpenAI/Claude/Local LLM adapter
│   ├── data/
│   │   ├── candles.py                       # Fetch & manage OHLCV data
│   │   └── market_data.py                   # News, sentiment, macro data
│   └── utils/
│       ├── logger.py                        # Structured logging
│       └── validators.py                    # Pydantic models & validation
├── tests/
│   ├── test_ev_engine.py
│   ├── test_regime_classifier.py
│   ├── test_signal_generator.py
│   └── test_memory_system.py
├── memory/
│   ├── trades.db                            # SQLite trade history
│   └── reflections.json                     # Post-trade analysis logs
├── logs/
│   └── trading_agent.log                    # Execution logs
└── examples/
    ├── backtest_example.py                  # Backtesting script
    ├── paper_trade_example.py               # Dry-run/testnet mode
    └── decision_log_output.txt              # Example trade justification
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Settings
Edit `config/settings.yaml` with your API keys and trading parameters:
```yaml
exchange: "binance"  # or "bybit", "blofin"
mode: "testnet"      # or "paper", "live"
max_account_risk_pct: 2.0
min_rr_ratio: 2.0
```

### 3. Run Paper Trading
```bash
python src/main.py --mode paper --backtest-window 90
```

### 4. View Trade Explanations
Check `logs/trading_agent.log` for detailed pre-trade justifications.

---

## 📊 Example Trade Decision Log

See `examples/decision_log_output.txt` for a real-world example of:
- Technical trigger summary
- Macro bias score
- Historical memory lookup results
- Exact risk/reward calculations
- EV confirmation

---

## 📖 Documentation

- **ARCHITECTURE.md**: System design, data flow diagrams, module interactions
- **DEPLOYMENT.md**: Step-by-step testnet setup and backtesting guide

---

## ⚠️ Risk Disclaimer

This trading system is for educational and research purposes. Past performance does not guarantee future results. Trade with caution and only use capital you can afford to lose.

---

## 📝 License

MIT License
