# Hasan AI Algo Trading System

**Professional Adaptive Long-Only US Stock Trading System**

A sophisticated 5-minute bullish stock trading system designed for capital preservation with adaptive market regime detection.

## System Architecture

### Core Components

1. **Market Regime Agent** - Market condition classification
2. **Screener Agent** - High-quality stock discovery
3. **Signal Agent** - 5-minute technical analysis
4. **Score Engine** - Probabilistic trade evaluation
5. **Hard Gate Rules** - Non-negotiable risk thresholds
6. **Risk Manager** - Position sizing and drawdown control
7. **Exit Rules** - Dynamic exit logic
8. **Execution Engine** - Alpaca paper/live trading
9. **Logging System** - Complete trade documentation
10. **Learning Agent** - Daily performance analysis

## Key Features

✅ **Capital Protection First** - Risk per trade: 0.5% of account
✅ **Adaptive Logic** - Adjusts to BULL, NEUTRAL, BEAR, NEWS_LOCK regimes
✅ **Score-Based Entries** - Minimum score 70 for BUY, 60-69 for WATCH
✅ **Hard Gate Rules** - Non-negotiable liquidity and technical thresholds
✅ **Bracket Orders** - Automatic stop loss and take profit
✅ **Paper Trading First** - 30-day minimum backtest before live
✅ **Complete Logging** - Every signal and trade documented
✅ **Daily Learning** - Analyze setup performance and optimize

## Trading Rules

### What We Do
- Long-only positions
- NYSE, NASDAQ, AMEX common stocks only
- Average volume > 1M shares
- Dollar volume > $50M
- 5-minute timeframe
- VWAP reclaim, higher low, breakout setups

### What We Don't Do
- Short selling
- Options
- Margin or leverage
- OTC stocks
- Force trades

## Setup Types

1. **VWAP Reclaim** - Price bounces above VWAP after pullback
2. **Higher Low Pullback** - Price pulls back to support, forms higher low
3. **Resistance Breakout** - Price breaks above daily/intraday resistance
4. **Trend Continuation** - Price continues higher in strong market only

## Entry Criteria

```
✓ Price above VWAP
✓ Price above EMA9
✓ Price above EMA20
✓ EMA9 > EMA20
✓ RSI 52-72 (ideally)
✓ ADX > 18-20 (ideally)
✓ Higher Low or VWAP reclaim
✓ Buy pressure > sell pressure
✓ No parabolic candles
✓ Score >= 70
```

## Risk Management

```
Risk per Trade:     0.5% of account
Daily Max Loss:     2% of account
Default Risk/Reward: 1:2 minimum
Stop Loss Placement: Clear support/structure
Take Profit 1:      +2% (partial exit)
Take Profit 2:      1:2 R/R (main target)
Move Stop:          Breakeven after +1R
```

## Market Regime Classification

### BULL
- SPY above key moving averages
- VIX < 25
- Breadth positive
- Allow breakout and trend continuation

### NEUTRAL
- SPY between support/resistance
- Allow pullback near support
- VWAP reclaim only

### BEAR
- SPY below key moving averages
- Reject most long trades
- Wait for very strong catalyst

### NEWS_LOCK
- Major news event (CPI, FOMC, geopolitical)
- Reject all new trades
- Manage existing positions

## Screener Criteria

```
Average Volume:     > 1,000,000
Dollar Volume:      > $50,000,000
RVOL:               > 1.5x
Current Volume:     > 1.5x average
Today Change:       0% to +10%
Not already up:     < 20%
Spread:             Tight (< $0.05 usually)
Catalyst:           News, earnings, FDA, etc.
ORTEX Pressure:     High short squeeze potential
```

## Score Engine (100 points)

```
Volume Score:       0-20 points
Trend Score:        0-20 points
Structure Score:    0-20 points
Momentum Score:     0-20 points
Market Score:       0-10 points
Catalyst Score:     0-10 points

Total Score:        BUY (70+) / WATCH (60-69) / REJECT (<60)
```

## Hard Gate Rules (Cannot be overridden by score)

```
❌ Hard Gate Fails if:
   - Liquidity weak (volume < 1M or dollar volume < $50M)
   - Price below VWAP
   - Price below EMA20
   - Risk/reward < 1:2
   - No clear stop loss
   - Market in panic
   - NEWS_LOCK active
   - Parabolic chase
   - Tight spread (> $0.05)
```

## Exit Triggers

```
✓ Take profit hit
✓ Stop loss hit
✓ Close below EMA9 for 2 candles
✓ Loses VWAP
✓ Structure breaks (lower low)
✓ Sell pressure dominant + below EMA9
✓ Market condition turns bad
✓ Session near close
```

## Paper Trading Requirements

- Minimum 30 trading days
- Minimum 10 trades
- Win rate > 40%
- Profit factor > 1.5
- Max drawdown < 10%
- Review all setup types

## Getting Started

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\\Scripts\\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure Credentials**
   ```bash
   cp .env.example .env
   # Edit .env with your Alpaca API keys
   ```

3. **Run Paper Trading**
   ```bash
   python main.py --mode=paper
   ```

4. **Monitor Signals**
   ```bash
   python monitor.py
   ```

5. **Daily Analysis**
   ```bash
   python learning_agent.py
   ```

## Logging & Analytics

Every trade is logged with:
- Ticker, entry time, market regime
- Setup type, total score, reason
- Entry, stop loss, target levels
- Position size, risk per share
- Exit price, P&L, reason for exit
- Trade duration, setup quality

## Important Disclaimers

⚠️ **Paper trading only by default**
⚠️ **Past performance does not guarantee future results**
⚠️ **Always review system output manually**
⚠️ **Use at your own risk**
⚠️ **Never trade with money you cannot afford to lose**

## Version

**v1.0.0** - Initial Release (May 2026)

## License

Private - For educational and personal use only.
