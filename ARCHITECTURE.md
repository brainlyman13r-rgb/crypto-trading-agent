# System Architecture & Data Flow

## 🏗️ High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    MARKET DATA INGESTION LAYER                      
│                                                                     
│  [Exchange API]  [News Feed]  [Macro Events]  [Social Sentiment]   
│        ↓               ↓             ↓                ↓              
│   [CCXT Adapter]  [NewsAPI]  [Economic Calendar]  [Twitter/Discord] 
└──────────────────┬──────────────┬──────────────────┬──────────────┬─────────────┘
             │            │             │              │
             ↓            ↓             ↓              ↓
    ┌────────────────────────────────────────────────────────────────────────────┐
    │     DATA PROCESSING & FEATURE ENGINEERING             
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                        
    │  Module 2: Market Regime Classifier                   
    │  ├─ Trend Detection (SMA, EMA slopes)                 
    │  ├─ Volatility Measurement (ATR, Bollinger Bands)     
    │  └─ Output: Bull / Bear / Sideways / Squeeze          
    │                                                        
    │  Module 3: Signal Generator                           
    │  ├─ Multi-timeframe RSI (15m, 1h, 4h)                
    │  ├─ MA Envelope Confluence                            
    │  ├─ Volume Profile Analysis                           
    │  ├─ Funding Rates & Open Interest                     
    │  ├─ Liquidation Cluster Detection                     
    │  └─ Output: Long / Short / NEUTRAL signals            
    │                                                        
    │  Module 4: LLM Sentiment Synthesizer                  
    │  ├─ Parse market news & macro events                  
    │  ├─ Aggregate social sentiment                        
    │  ├─ Query LLM for context & bias                      
    │  └─ Output: Macro Bias Score (-1.0 to +1.0)           
    └──────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 ↓
    ┌────────────────────────────────────────────────────────────────────────────┐
    │        DECISION & VALIDATION LAYER                    
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                        
    │  Module 5: Historical Memory & Self-Reflection        
    │  ├─ Query vector DB (ChromaDB/SQLite)                 
    │  ├─ Retrieve similar past setups                      
    │  ├─ Check if recent similar trade failed              
    │  └─ Output: Memory Risk Score, Lessons Learned        
    │                                                        
    │  Module 1: EV Engine & Risk Management                
    │  ├─ Calculate Entry/Stop/Target prices                
    │  ├─ Compute R:R ratio (min 1:2)                       
    │  ├─ Account for fees & slippage                       
    │  ├─ Calculate Expected Value: EV = Pw*Wav - Pl*Lav   
    │  ├─ Determine position size (max 1-2% risk)           
    │  └─ Output: EV Score, Position Size, Risk Params      
    │                                                        
    │  Module 7: Hard Risk Guardrails                       
    │  ├─ Check daily drawdown < 5%                         
    │  ├─ Verify trade risk < 1-2% of account               
    │  ├─ Validate stop-loss distance (ATR-based)           
    │  └─ Output: PASS / REJECT decision                    
    └──────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 ↓
    ┌────────────────────────────────────────────────────────────────────────────┐
    │        EXPLANATION & EXECUTION LAYER                  
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                        
    │  Module 6: Human-Readable Explanation Engine          
    │  ├─ Synthesize all module outputs                     
    │  ├─ Generate trade justification narrative            
    │  ├─ Show technical triggers summary                   
    │  ├─ Include macro bias context                        
    │  ├─ List memory lessons applied                       
    │  ├─ Display exact risk/reward calcs                   
    │  └─ Output: Human-readable trade brief                
    │                                                        
    │  [Logger] → Trade Decision Log / Execution Summary    
    └──────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 ↓
    ┌────────────────────────────────────────────────────────────────────────────┐
    │          ORDER EXECUTION LAYER                        
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                        
    │  Paper Trading Mode (Dry-Run)                         
    │  ├─ Simulate order submission                         
    │  ├─ Track P&L in memory                               
    │  └─ Log for backtesting analysis                      
    │                                                        
    │  Live / Testnet Mode                                  
    │  ├─ Submit orders via CCXT Adapter                    
    │  ├─ Set stop-loss & take-profit                       
    │  └─ Monitor position in real-time                     
    └──────────────────┬──────────────────────────────────────────────────────────┘
                 │
                 ↓
    ┌────────────────────────────────────────────────────────────────────────────┐
    │          TRADE MONITORING & REFLECTION                
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                        
    │  Real-Time Position Monitoring                        
    │  ├─ Track order fills & partial fills                 
    │  ├─ Monitor stop-loss & take-profit triggers          
    │  └─ Update account drawdown metrics                   
    │                                                        
    │  Post-Trade Reflection (Module 5)                     
    │  ├─ Analyze why entry occurred                        
    │  ├─ Evaluate outcome (W/L, R-multiple)                
    │  ├─ Extract lessons & update memory                   
    │  ├─ Store in vector DB for future queries             
    │  └─ Feed back into decision engine                    
    └────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Timeline

### Pre-Trade (Entry Signal Processing)

1. **Market Data Collection** (Continuous)
   - Fetch OHLCV from exchange (15m, 1h, 4h)
   - Pull latest news headlines & macro calendar events
   - Aggregate social sentiment (Twitter, Discord)

2. **Market Regime Classification** (Every candle close)
   - Analyze trend direction & strength
   - Measure volatility regime
   - Output: `Current Regime = "Strong Bull" | "Bear" | "Sideways" | "Squeeze"`

3. **Technical Signal Generation** (Every candle close)
   - Compute RSI on 15m/1h/4h timeframes
   - Check MA envelope confluence
   - Scan for liquidation clusters
   - Output: `Signal = "LONG" | "SHORT" | "NEUTRAL"`

4. **LLM Sentiment Synthesis** (On news events)
   - Query LLM with latest market context
   - Parse pydantic-validated output
   - Output: `Macro_Bias_Score = ±0.75` (bullish) or `±-0.85` (bearish)

5. **Historical Memory Lookup** (Pre-entry)
   - Query ChromaDB for similar setups in past 90 days
   - Check if recent similar trades failed
   - Output: `Memory_Risk_Score`, `Applicable_Lessons`

6. **EV Calculation & Risk Sizing** (Pre-entry)
   - Determine entry, SL, TP prices
   - Compute R:R ratio (must be ≥1:2)
   - Calculate expected value
   - Size position for max 1-2% account risk
   - Output: `EV_Score`, `Position_Size`, `SL_Price`, `TP_Price`

7. **Risk Guardrails Check** (Pre-entry)
   - Verify daily drawdown < 5%
   - Confirm trade risk < max per-trade limit
   - Validate ATR-based stop-loss distance
   - Output: `APPROVED` or `REJECTED`

8. **Human-Readable Explanation** (Pre-entry)
   - Synthesize all module outputs into narrative
   - Generate trade justification
   - Log to console & file

9. **Order Execution**
   - Submit entry, SL, TP orders (or simulate in paper mode)
   - Update position tracker

### Post-Trade (Reflection & Learning)

1. **Position Monitoring** (Real-time)
   - Track order fills
   - Monitor SL/TP triggers
   - Update daily P&L & drawdown

2. **Trade Closure** (On SL or TP hit)
   - Record final P&L
   - Calculate win/loss and R-multiple outcome
   - Capture final market conditions

3. **Self-Reflection Analysis**
   - Why did we enter? (Which signals fired?)
   - Why did we win/lose? (Market conditions post-entry?)
   - Extract 2-3 key lessons
   - Store reflections in SQLite/JSON and vector DB

4. **Memory Update** (Post-reflection)
   - Embed trade metadata in ChromaDB
   - Tag with regime, signal type, outcome
   - Make searchable for future pre-entry memory lookups

---

## 📋 Module Output Contracts (Pydantic)

### Module 2: Market Regime
```python
class MarketRegimeOutput(BaseModel):
    regime: Literal["strong_bull", "bear", "sideways", "squeeze_breakout"]
    confidence: float  # 0.0 to 1.0
    volatility_level: Literal["low", "medium", "high", "extreme"]
    key_levels: Dict[str, float]  # support/resistance
```

### Module 3: Signal Generator
```python
class TradeSignal(BaseModel):
    direction: Literal["LONG", "SHORT", "NEUTRAL"]
    confidence: float  # 0.0 to 1.0
    triggers: List[str]  # ["rsi_oversold", "ma_bullish_cross", ...]
    timeframe_confluence: Dict[str, str]  # {"15m": "LONG", "1h": "LONG", ...}
```

### Module 4: LLM Sentiment
```python
class MacroSentiment(BaseModel):
    bias_score: float  # -1.0 (extreme bearish) to +1.0 (extreme bullish)
    key_events: List[str]
    sentiment_sources: Dict[str, float]  # {"news": 0.6, "social": 0.8, ...}
    reasoning: str
```

### Module 5: Memory
```python
class MemoryInsight(BaseModel):
    similar_trades_count: int
    success_rate: float  # 0.0 to 1.0
    lessons: List[str]
    risk_flag: Optional[str]  # None or "similar_setup_failed_recently"
```

### Module 1: EV Engine
```python
class TradeRiskProfile(BaseModel):
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    position_size: float  # In base currency
    risk_amount: float  # In USD
    reward_amount: float  # In USD
    rr_ratio: float  # Reward:Risk
    expected_value: float  # EV in USD
    win_probability: float  # Based on technical + sentiment
    fee_adjusted_ev: float  # After taker/maker fees
```

### Module 6: Explanation
```python
class TradeJustification(BaseModel):
    title: str  # "BTC LONG: Fed pivot + RSI oversold"
    technical_summary: str
    macro_context: str
    memory_insights: str
    risk_reward_summary: str
    ev_calculation_summary: str
    final_recommendation: Literal["EXECUTE", "WAIT", "REJECT"]
```

---

## 🔗 Integration Points

### Exchange Adapter (CCXT)
- `fetch_ohlcv(symbol, timeframe, limit=100)`
- `create_order(symbol, type, side, amount, price, params)`
- `fetch_balance()`, `fetch_positions()`, `fetch_order_status()`

### LLM Adapter
- `analyze_market_news(headlines: List[str]) → MacroSentiment`
- `generate_trade_explanation(all_signals, regime, memory) → TradeJustification`

### Memory System
- `store_trade_reflection(trade_id, reflection_data)`
- `query_similar_setups(regime, signal_type, limit=5) → List[MemoryInsight]`
- `get_success_rate_by_regime(regime) → float`

---

## ⚡ Performance Targets

- **Pre-trade Analysis Latency**: < 2 seconds (paper mode), < 5 seconds (live mode)
- **Memory Query Speed**: < 500ms (ChromaDB semantic search)
- **EV Calculation**: < 100ms
- **Order Execution**: < 1 second after decision approval
- **Daily Reflection**: < 10 minutes for 5-10 closed trades

---

## 🛡️ Fail-Safe Mechanisms

1. **Circuit Breaker**: If daily loss > 5%, halt all trading until next day
2. **Position Timeout**: Auto-close positions older than 48 hours (swing trading scope)
3. **Stale Data Guard**: Reject signals if candle data > 5 minutes old
4. **Memory Degradation**: If vector DB unavailable, fall back to technical-only mode
5. **LLM Fallback**: If LLM API down, use heuristic sentiment (neutral bias)
