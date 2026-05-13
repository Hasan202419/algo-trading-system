# Hasan AI Algo Trading System 🤖📈

**Professional Adaptive Long-Only US Stock Trading System**

Kuchli adaptive logic bilan 5-minute bullish stock trading setups topuvchi, capital protection first filosofiyasi bilan qurilgan tizim.

## 🎯 Asosiy Maqsad

Bozor shartlariga moslashuvchi yuqori sifatli 5-minute bullish stock trading setuplarini topish va paper trading orqali test qilish.

## 📋 Asosiy Qoidalar

✅ **Nima qilshimiz mumkin:**
- Long-only pozitsiyalar (faqat sotib olish)
- NYSE, NASDAQ, AMEX common stocks
- Paper trading (default)
- Bracket orders (stop + target)
- 0.5% risk per trade
- Adaptive market regimes

❌ **Nima taqiqlandi:**
- Short selling
- Options
- Margin / Leverage
- OTC stocks
- Force trades

## 🏗️ Tizim Arxitekturasi

### 1. Market Regime Agent
Bozor holatini tahlil qiladi va klassifikatsiya qiladi:
- **BULL** - Sotish mumkin (breakout, trend continuation)
- **NEUTRAL** - Faqat pullback va VWAP reclaim
- **BEAR** - Sotish taqiqlandi
- **NEWS_LOCK** - Yangilik taqiqlandi

**Tahlil qiladi:**
- SPY narxi vs MA200/MA50
- VIX darajasi
- Market breadth
- Major news (CPI, FOMC, geopolitical)

### 2. Screener Agent
Har minutda high-quality kandidatlarni qidiradi:
```
✓ Average Volume > 1,000,000
✓ Dollar Volume > $50,000,000
✓ RVOL (Relative Volume) > 1.5x
✓ Today Change: 0% - 10%
✓ Not already up > 20%
✓ Tight Spread (< $0.05)
✓ Strong Catalyst
✓ ORTEX Squeeze Potential
```

### 3. Signal Agent
5-minute technical analysis:
- Price > VWAP
- Price > EMA9 > EMA20
- RSI 52-72
- ADX > 18-20
- Higher Low, VWAP Reclaim, or Breakout
- Buy > Sell pressure
- No parabolic candles

### 4. Score Engine
Probabilistic 100-ball scoring:
- Volume Score: 0-20
- Trend Score: 0-20
- Structure Score: 0-20
- Momentum Score: 0-20
- Market Score: 0-10
- Catalyst Score: 0-10

**Decision:**
- Score >= 70: **BUY**
- Score 60-69: **WATCH**
- Score < 60: **REJECT**

### 5. Hard Gate Rules
Kesilmas qoidalar (score bilan o'zgartirib bo'lmaydi):
```
❌ Volume < 1M yoki Dollar < $50M
❌ Price < VWAP
❌ Price < EMA20
❌ Risk/Reward < 1:2
❌ No clear stop loss
❌ Market panic
❌ NEWS_LOCK active
❌ Parabolic chase
```

### 6. Risk Manager
Position sizing va risk control:
```
Risk per Trade:       0.5% of account
Daily Max Loss:       2% of account
Min Risk/Reward:      1:2
Stop Loss:            Clear support/structure
Partial Take Profit:  +2%
Main Target:          1:2 R/R
Move Stop:            Breakeven after +1R
```

### 7. Exit Rules
Automatik exit triggerlar:
- Take profit hit
- Stop loss hit
- Close < EMA9 for 2 candles
- Loses VWAP
- Structure breaks
- Sell pressure + price < EMA9
- Market regime turns bad
- Session near close

### 8. Execution Engine
Alpaca API orqali:
- Bracket orders (buy + stop + target)
- Paper trading default
- Order management
- Live trading (disabled by default)

### 9. Learning Agent
Har kuni analiz qiladi:
- Setup performance tracking
- Fake breakout detection
- Market regime analysis
- Parameter recommendations
- Win rate, profit factor, drawdown

## 📊 Entry Setup Turlari

### A. VWAP Reclaim
Narxi pullback dan keyin VWAP dan sakrab chiqadi.
```
Entry: VWAP dan yuqorida
Stop: VWAP dan pastda
Target: +2% partial, +2R main
```

### B. Higher Low Pullback
Narxi support yaqinida yuqoriroq low qiladi.
```
Entry: Higher low break
Stop: Previous low dan pastda
Target: +2% partial, +2R main
```

### C. Resistance Breakout
Narxi intraday/daily resistansni buza chiqadi.
```
Entry: Resistance break
Stop: Resistance dan pastda
Target: +2% partial, +2R main
```

### D. Trend Continuation
Faqat BULL bozorida mavjudoti trend davomlanadi.
```
Entry: Higher high, EMA alignment
Stop: Recent support
Target: +2% partial, +2R main
```

## 📈 Market Regime Rules

### BULL Regime
```yaml
Allow Breakout:           TRUE
Allow Trend Continuation: TRUE
Allow Pullback:           TRUE
Allow VWAP Reclaim:       TRUE
Max New Trades:           5
Aggressiveness:           HIGH
```

### NEUTRAL Regime
```yaml
Allow Breakout:           FALSE
Allow Trend Continuation: FALSE
Allow Pullback:           TRUE
Allow VWAP Reclaim:       TRUE
Max New Trades:           2
Aggressiveness:           LOW
```

### BEAR Regime
```yaml
Allow Breakout:           FALSE
Allow Trend Continuation: FALSE
Allow Pullback:           FALSE
Allow VWAP Reclaim:       FALSE
Max New Trades:           0
Aggressiveness:           NONE
```

### NEWS_LOCK Regime
```yaml
All New Trades:           REJECTED
Manage Existing:          YES
Wait for Clarity:         YES
```

## 🚀 Boshlash

### 1. Setup
```bash
# Clone repo
git clone https://github.com/Hasan202419/algo-trading-system.git
cd algo-trading-system

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
```bash
# Copy environment template
cp .env.example .env

# Edit .env va API kalitlarni kiriting:
# ALPACA_API_KEY=...
# ALPACA_SECRET_KEY=...
# POLYGON_API_KEY=...
```

### 3. Paper Trading
```bash
# Real-time monitoring
python main.py --mode=paper

# Dashboard (alohida terminal)
python monitor.py

# Daily analysis
python learning_agent.py
```

### 4. Live Trading (Keyin)
```bash
# Minimum 30 trading days paper test kerak
# Minimum 10 trades
# Win rate > 40%
# Profit factor > 1.5
# Max drawdown < 10%

python main.py --mode=live
```

## 📝 Logging

Har trade quyidagi ma'lumotlar bilan qaydlanadi:
```json
{
  "ticker": "AAPL",
  "timestamp": "2026-05-13 10:30:00",
  "market_regime": "BULL",
  "setup_type": "VWAP_RECLAIM",
  "score": 75,
  "entry_price": 150.25,
  "stop_loss": 149.50,
  "target_1": 153.25,
  "target_2": 156.25,
  "position_size": 100,
  "risk_per_share": 0.75,
  "risk_reward_ratio": 2.0,
  "exit_price": 156.25,
  "profit_loss": 600,
  "trade_duration": "45 minutes",
  "result": "WIN",
  "reason": "Target hit"
}
```

## 📊 Performance Metrics

```
Total Trades:        X
Win Rate:            X%
Profit Factor:       X
Average Win:         +X%
Average Loss:        -X%
Largest Win:         +X%
Largest Loss:        -X%
Daily Max Loss Hit:  X days
Max Drawdown:        X%
Risk/Reward Avg:     1:X
```

## ⚠️ Muhim Disclaimer

⚠️ **Paper trading only by default**
⚠️ **Past performance ≠ Future results**
⚠️ **Always review system output manually**
⚠️ **Use at your own risk**
⚠️ **Never trade with money you cannot afford to lose**

## 📁 Directory Structure

```
algo-trading-system/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   └── default_config.yaml
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── market_regime_agent.py
│   │   ├── screener_agent.py
│   │   ├── signal_agent.py
│   │   └── learning_agent.py
│   ├── engines/
│   │   ├── __init__.py
│   │   └── score_engine.py
│   ├── managers/
│   │   ├── __init__.py
│   │   └── risk_manager.py
│   ├── execution/
│   │   ├── __init__.py
│   │   └── execution_engine.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
├── logs/
│   ├── signals.json
│   ├── trades.json
│   └── performance.json
├── main.py
├── monitor.py
└── learning_agent.py
```

## 🔧 Configuration

Barcha parametrlar `config/default_config.yaml` da:
- Market regime rules
- Screener filters
- Technical indicators
- Score engine weights
- Risk management
- Exit rules

## 📚 Qo'llanma

1. Market Regime Agent tahlili
2. Screener har minutda aktsiya topadi
3. Signal Agent technical analysis qiladi
4. Score Engine bahogi hisoblaydi
5. Hard Gates check qiladi
6. Risk Manager position sizing qiladi
7. Execution bracket order yuboradi
8. Learning Agent kunlik analiz qiladi

## 🤝 Support

Ishlashida muammo bo'lsa, logs folder da kayt ko'ring.

## 📄 License

Private - Faqat educationа va personal use uchun.

---

**Version:** v1.0.0 (May 2026)
**Author:** Hasan AI Trading Agent
**Status:** Beta (Paper Trading)
