"""Main Trading Loop - Orchestrates all agents and execution"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import yaml
import json
from pathlib import Path

from src.agents.market_regime_agent import MarketRegimeAgent, MarketRegime
from src.agents.screener_agent import ScreenerAgent
from src.agents.signal_agent import SignalAgent, EntryType
from src.agents.learning_agent import LearningAgent
from src.engines.score_engine import ScoreEngine, TradeDecision
from src.managers.risk_manager import RiskManager
from src.execution.execution_engine import ExecutionEngine
from src.utils.logger import setup_logger

logger = setup_logger('trading_system')


class TradingSystem:
    """Main trading system orchestrator"""
    
    def __init__(self, config_path: str = './config/default_config.yaml'):
        """Initialize trading system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        logger.info("Configuration loaded")
        
        # Initialize agents and engines
        self.market_regime_agent = MarketRegimeAgent(self.config)
        self.screener_agent = ScreenerAgent(self.config)
        self.signal_agent = SignalAgent(self.config)
        self.score_engine = ScoreEngine(self.config)
        self.risk_manager = RiskManager(self.config)
        self.execution_engine = ExecutionEngine(self.config)
        self.learning_agent = LearningAgent(self.config)
        
        logger.info("All agents initialized")
        
        # State tracking
        self.active_trades = {}
        self.daily_signals = []
        self.running = False
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def start(self) -> None:
        """Start the trading system"""
        self.running = True
        logger.info("="*80)
        logger.info("HASAN AI ALGO TRADING SYSTEM - STARTED")
        logger.info("="*80)
        logger.info(f"Mode: {self.execution_engine.mode.upper()}")
        logger.info(f"Start time: {datetime.now()}")
        logger.info("="*80)
    
    def stop(self) -> None:
        """Stop the trading system"""
        self.running = False
        logger.info("="*80)
        logger.info("TRADING SYSTEM - STOPPED")
        logger.info(f"Stop time: {datetime.now()}")
        logger.info("="*80)
    
    def analyze_and_trade(self,
                         market_data: Dict,
                         stock_data: List[Dict]) -> None:
        """Main trading logic: Analyze market and place trades
        
        Args:
            market_data: SPY, VIX, breadth data
            stock_data: Stock OHLCV data
        """
        if not self.running:
            logger.warning("System not running")
            return
        
        # Step 1: Analyze market regime
        regime = self.market_regime_agent.analyze(
            spy_price=market_data.get('spy_price', 0),
            spy_ma200=market_data.get('spy_ma200', 0),
            spy_ma50=market_data.get('spy_ma50', 0),
            vix_level=market_data.get('vix_level', 0),
            breadth_percent=market_data.get('breadth_percent', 0),
            major_news=market_data.get('major_news', []),
            recent_macro_events=market_data.get('macro_events', [])
        )
        
        logger.info(f"Market Regime: {regime}")
        
        # Hard gate: NEWS_LOCK - no trading
        if regime.regime == MarketRegime.NEWS_LOCK:
            logger.warning("NEWS_LOCK detected - No new trades")
            return
        
        # Step 2: Screen stocks for candidates
        candidates = self.screener_agent.screen(stock_data)
        
        if not candidates:
            logger.info("No candidates passed screening")
            return
        
        logger.info(f"Screening complete: {len(candidates)} candidates")
        
        # Step 3: Analyze signals and generate scores
        trade_opportunities = []
        
        for candidate in candidates:
            try:
                # Get technical analysis
                ohlcv_data = self._get_ohlcv_data(candidate.ticker)
                if ohlcv_data is None or len(ohlcv_data) < 100:
                    continue
                
                technical = self.signal_agent.analyze(candidate.ticker, ohlcv_data)
                if technical is None:
                    continue
                
                # Hard gate: Price must be above VWAP and EMA20
                if not technical.price_above_vwap or not technical.price_above_ema20:
                    continue
                
                # Hard gate: No parabolic candles
                if technical.last_candle and technical.last_candle.is_parabolic:
                    continue
                
                # Score the trade
                risk_reward = self._calculate_risk_reward(candidate, technical)
                score_breakdown = self.score_engine.score_trade(
                    candidate, technical, regime, risk_reward
                )
                
                if score_breakdown.decision in [TradeDecision.BUY, TradeDecision.WATCH]:
                    trade_opportunities.append({
                        'candidate': candidate,
                        'technical': technical,
                        'score': score_breakdown,
                        'regime': regime,
                        'risk_reward': risk_reward
                    })
            
            except Exception as e:
                logger.warning(f"Error analyzing {candidate.ticker}: {e}")
                continue
        
        # Step 4: Check regime rules and filter
        regime_rules = regime.regime.get_regime_rules()
        buy_opportunities = [
            t for t in trade_opportunities
            if t['score'].decision == TradeDecision.BUY
        ]
        
        logger.info(f"Found {len(buy_opportunities)} BUY signals, {len(trade_opportunities) - len(buy_opportunities)} WATCH signals")
        
        # Step 5: Execute trades
        for opportunity in buy_opportunities:
            self._execute_trade(opportunity)
        
        # Step 6: Log signals
        for opportunity in trade_opportunities:
            self._log_signal(opportunity)
    
    def _get_ohlcv_data(self, ticker: str):
        """Get OHLCV data for stock (placeholder)
        
        Args:
            ticker: Stock ticker
            
        Returns:
            DataFrame with OHLCV data
        """
        # In real implementation, would fetch from Alpaca or data provider
        return None
    
    def _calculate_risk_reward(self, candidate, technical) -> float:
        """Calculate risk/reward ratio
        
        Args:
            candidate: StockCandidate
            technical: TechnicalAnalysis
            
        Returns:
            Risk/reward ratio
        """
        # Calculate based on support/resistance levels
        stop_loss = technical.ema20 * 0.99  # 1% below EMA20
        target = technical.price * 1.04  # 4% profit target
        
        risk = technical.price - stop_loss
        reward = target - technical.price
        
        if risk > 0:
            return reward / risk
        return 0
    
    def _execute_trade(self, opportunity: Dict) -> None:
        """Execute a trade
        
        Args:
            opportunity: Trade opportunity dictionary
        """
        candidate = opportunity['candidate']
        technical = opportunity['technical']
        score = opportunity['score']
        risk_reward = opportunity['risk_reward']
        
        # Calculate position sizing
        account_value = self.execution_engine.get_account_value()
        if not account_value:
            logger.error("Cannot get account value")
            return
        
        # Set stop loss below support
        stop_loss = technical.ema20 * 0.99
        
        # Calculate position
        risk_metrics = self.risk_manager.calculate_position(
            entry_price=technical.price,
            stop_loss=stop_loss,
            account_size=account_value,
            technical_analysis=technical
        )
        
        if not risk_metrics:
            logger.warning(f"{candidate.ticker}: Position size calculation failed")
            return
        
        # Validate risk/reward
        if not self.risk_manager.validate_risk_reward(risk_metrics):
            logger.warning(f"{candidate.ticker}: Risk/reward below minimum")
            return
        
        # Check daily loss limit
        if self.risk_manager.should_stop_trading(account_value):
            logger.warning("Daily loss limit reached - Stop trading")
            return
        
        # Place bracket order
        execution_result = self.execution_engine.place_bracket_order(
            ticker=candidate.ticker,
            quantity=risk_metrics.position_size,
            entry_price=technical.price,
            stop_loss=risk_metrics.stop_loss,
            take_profit_1=risk_metrics.take_profit_1,
            take_profit_2=risk_metrics.take_profit_2
        )
        
        if execution_result.success:
            logger.info(
                f"\n{'='*80}\n"
                f"TRADE EXECUTED: {candidate.ticker}\n"
                f"{'='*80}\n"
                f"Company: {candidate.company_name}\n"
                f"Entry: ${technical.price:.2f}\n"
                f"Stop: ${risk_metrics.stop_loss:.2f}\n"
                f"TP1: ${risk_metrics.take_profit_1:.2f}\n"
                f"TP2: ${risk_metrics.take_profit_2:.2f}\n"
                f"Position: {risk_metrics.position_size} shares\n"
                f"Risk/Reward: 1:{risk_metrics.risk_reward_ratio:.1f}\n"
                f"Account Risk: {risk_metrics.account_risk:.2f}%\n"
                f"Setup: {technical.entry_signal.value}\n"
                f"Score: {score.total_score:.1f}/100 ({score.decision.value})\n"
                f"Market: {score.reasoning}\n"
                f"{'='*80}\n"
            )
            
            # Track active trade
            self.active_trades[candidate.ticker] = {
                'entry_time': datetime.now(),
                'entry_price': technical.price,
                'stop_loss': risk_metrics.stop_loss,
                'target': risk_metrics.take_profit_2,
                'quantity': risk_metrics.position_size,
                'execution_result': execution_result
            }
        else:
            logger.error(f"Trade execution failed: {execution_result.error_message}")
    
    def _log_signal(self, opportunity: Dict) -> None:
        """Log signal for learning
        
        Args:
            opportunity: Trade opportunity
        """
        candidate = opportunity['candidate']
        technical = opportunity['technical']
        score = opportunity['score']
        regime = opportunity['regime']
        
        signal_record = {
            'timestamp': datetime.now().isoformat(),
            'ticker': candidate.ticker,
            'company': candidate.company_name,
            'market_regime': regime.regime.value,
            'setup_type': technical.entry_signal.value,
            'price': technical.price,
            'vwap': technical.vwap,
            'ema20': technical.ema20,
            'rsi': technical.rsi,
            'volume': technical.volume,
            'score': score.total_score,
            'decision': score.decision.value,
            'reasoning': score.reasoning,
            'catalyst': candidate.catalysts,
            'rvol': candidate.rvol
        }
        
        self.daily_signals.append(signal_record)
        self.learning_agent.add_signal(signal_record)
        
        logger.debug(f"Signal logged: {candidate.ticker}")
    
    def generate_daily_report(self) -> None:
        """Generate and save daily report"""
        report = self.learning_agent.generate_daily_report()
        
        if report:
            report_file = f'./logs/report_{report.date}.json'
            self.learning_agent.export_report(report, report_file)
            logger.info(f"Daily report saved: {report_file}")
    
    def get_system_status(self) -> Dict:
        """Get system status
        
        Returns:
            Status dictionary
        """
        account_value = self.execution_engine.get_account_value()
        
        return {
            'running': self.running,
            'timestamp': datetime.now().isoformat(),
            'mode': self.execution_engine.mode,
            'account_value': account_value,
            'active_trades': len(self.active_trades),
            'daily_signals': len(self.daily_signals),
            'daily_loss': self.risk_manager.daily_loss,
            'active_brackets': len(self.execution_engine.active_brackets)
        }
