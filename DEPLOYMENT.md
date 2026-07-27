# Deployment & Testing Guide

## 📋 Prerequisites

### 1. Python Environment
```bash
python --version  # Requires Python 3.9+
pip install --upgrade pip
```

### 2. Clone Repository
```bash
git clone https://github.com/brainlyman13r-rgb/crypto-trading-agent.git
cd crypto-trading-agent
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration Setup

### 1. Create `.env` file
```bash
cp .env.example .env  # Or create manually
```

### 2. Edit `config/settings.yaml`
```yaml
# Exchange Configuration
exchange: "binance"  # or "bybit", "blofin"
mode: "testnet"      # or "paper", "live"

# API Keys (set in .env, NOT in this file)
api_key: "${EXCHANGE_API_KEY}"
api_secret: "${EXCHANGE_API_SECRET}"

# LLM Configuration
llm_provider: "openai"  # or "anthropic"
llm_api_key: "${OPENAI_API_KEY}"

# Trading Parameters
trading:
  symbols: ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
  timeframes: ["15m", "1h", "4h"]
  max_account_risk_pct: 2.0
  min_rr_ratio: 1.5
  
# Risk Management
risk:
  max_daily_drawdown_pct: 5.0
  max_per_trade_risk_pct: 2.0
  max_open_positions: 3
  position_timeout_hours: 48
```

### 3. Set Environment Variables
```bash
export EXCHANGE_API_KEY="your_api_key"
export EXCHANGE_API_SECRET="your_api_secret"
export OPENAI_API_KEY="your_openai_key"  # Optional
```

---

## 🧪 Testing in Testnet (Recommended First Step)

### 1. Binance Testnet Setup

**Create Testnet Account:**
- Go to https://testnet.binance.vision
- Create account (separate from main Binance)
- Generate API keys for testnet

**Update Configuration:**
```yaml
exchange: "binance"
mode: "testnet"
api_key: "your_testnet_key"
api_secret: "your_testnet_secret"
```

### 2. Bybit Testnet Setup

**Create Testnet Account:**
- Go to https://testnet.bybit.com
- Create account
- Generate API keys

**Update Configuration:**
```yaml
exchange: "bybit"
mode: "testnet"
```

### 3. Run Testnet Agent
```bash
python -c "
from src.main import TradingAgent

agent = TradingAgent(
    account_balance=10000.0,
    exchange='binance',
    api_key='your_testnet_key',
    api_secret='your_testnet_secret',
    sandbox=True,
)

# Run analysis
analysis = agent.analyze_and_execute(
    symbol='BTC/USDT',
    paper_mode=True,  # Dry-run, don't execute
)

print(f'Recommendation: {analysis.justification.final_recommendation}')
print(f'Confidence: {analysis.justification.confidence_overall:.0%}')
"
```

---

## 📊 Paper Trading (Dry-Run Mode)

Simulates trading without real capital:

```bash
python examples/paper_trade_example.py --symbols BTC/USDT ETH/USDT --duration 7d
```

**Output:**
- Simulated P&L
- Trade statistics (win rate, R-multiples, drawdown)
- Memory reflections from each trade
- Historical performance analysis

---

## 🔍 Backtesting

### 1. Run Backtest on Historical Data
```bash
python examples/backtest_example.py \
  --symbol BTC/USDT \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --initial-capital 10000
```

**Output:**
- Total return %
- Sharpe ratio
- Max drawdown
- Win rate
- Trade-by-trade log

### 2. Optimize Parameters
```bash
python examples/optimize_parameters.py \
  --param-grid max_account_risk_pct 1 2 3 \
  --param-grid min_rr_ratio 1.5 2.0 2.5
```

---

## 🚀 Live Trading (Use with Caution)

### Prerequisites:
1. **Complete all testing above**
2. **Start with small capital** (e.g., $100-500)
3. **Monitor closely for first week**
4. **Have emergency stop plan ready**

### 1. Update Configuration
```yaml
mode: "live"
exchange: "binance"
api_key: "your_live_key"
api_secret: "your_live_secret"
```

### 2. Start Live Agent
```bash
python -c "
from src.main import TradingAgent

agent = TradingAgent(
    account_balance=500.0,  # Start small
    exchange='binance',
    api_key='your_live_key',
    api_secret='your_live_secret',
    sandbox=False,  # LIVE MODE
)

# Continuous monitoring loop
while True:
    analysis = agent.analyze_and_execute(
        symbol='BTC/USDT',
        paper_mode=False,  # Execute real orders
    )
    
    # Sleep and check again
    import time
    time.sleep(300)  # Check every 5 minutes
"
```

### 3. Monitor System

**Check Logs:**
```bash
tail -f logs/trading_agent_*.log
```

**View Account Status:**
```bash
python -c "
from src.main import TradingAgent
agent = TradingAgent(...)
status = agent.get_status()
print(status)
"
```

---

## 🛑 Emergency Controls

### 1. Kill Switch
```bash
# Edit config
mode: "halt"  # Stops all trading
```

### 2. Manual Position Close
```bash
python -c "
from src.integrations.exchange_adapter import ExchangeAdapter

exchange = ExchangeAdapter(...)
exchange.cancel_order(order_id='...', symbol='BTC/USDT')
"
```

---

## 📈 Performance Metrics

### Key Statistics
```bash
python -c "
from src.modules.memory_system import HistoricalMemory

memory = HistoricalMemory()
stats = memory.get_statistics(days_back=30)

print(f"Win Rate: {stats['win_rate']:.1%}")
print(f"Total P&L: ${stats['total_pnl']:.2f}")
print(f"Avg R-Multiple: {stats['avg_r_multiple']:.2f}R")
print(f"Avg Holding Time: {stats['avg_holding_hours']:.1f}h")
"
```

---

## 🐛 Troubleshooting

### Issue: "No module named ccxt"
```bash
pip install ccxt
```

### Issue: "API key invalid"
- Verify keys in `.env`
- Check testnet vs. live keys
- Ensure IP whitelist is configured (if required by exchange)

### Issue: "Insufficient balance for order"
- Check account balance with `fetch_balance()`
- Verify position sizing calculations
- Review risk guardrails

### Issue: "ChromaDB not available"
```bash
pip install chromadb
```

---

## 📞 Support

- **Documentation**: See `ARCHITECTURE.md` for system design
- **Issues**: Create GitHub issue with logs and configuration
- **Discussion**: Start GitHub discussion for questions

---

## ⚖️ Disclaimer

This trading system is for **educational and research purposes only**. 
- Past performance does not guarantee future results.
- Crypto trading carries substantial risk of loss.
- Start with small capital and thorough testing.
- Always maintain emergency stop procedures.

**Trade responsibly.** 🎯
