"""Risk Manager - Position sizing, stop loss, take profit calculations"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for a trade"""
    entry_price: float
    stop_loss: float
    take_profit_1: float  # Partial exit at +2%
    take_profit_2: float  # Main exit at 1:2 R/R
    risk_per_share: float
    position_size: int
    position_value: float
    account_risk: float  # % of account risked
    risk_reward_ratio: float
    max_daily_loss_remaining: float
    
    def __str__(self) -> str:
        return (
            f"Entry: ${self.entry_price:.2f} | "
            f"Stop: ${self.stop_loss:.2f} | "
            f"TP1: ${self.take_profit_1:.2f} | "
            f"TP2: ${self.take_profit_2:.2f} | "
            f"Position: {self.position_size} shares | "
            f"Risk: {self.account_risk:.2f}% | "
            f"R/R: 1:{self.risk_reward_ratio:.1f}"
        )


class RiskManager:
    """Manages position sizing and risk parameters"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.risk_config = self.config.get('risk_management', {})
        self.daily_loss = 0.0
        self.trades_today = []
        
    def calculate_position(self,
                          entry_price: float,
                          stop_loss: float,
                          account_size: float,
                          technical_analysis=None) -> Optional[RiskMetrics]:
        """Calculate position size and risk metrics
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            account_size: Total account size
            technical_analysis: Technical analysis for better calculations
            
        Returns:
            RiskMetrics object or None if invalid
        """
        
        # Validate inputs
        if entry_price <= 0 or stop_loss <= 0:
            logger.error("Invalid entry or stop loss price")
            return None
        
        if stop_loss >= entry_price:
            logger.error("Stop loss must be below entry price")
            return None
        
        # Calculate risk per share
        risk_per_share = entry_price - stop_loss
        
        # Validate min risk (at least 0.5%)
        min_risk = entry_price * 0.005
        if risk_per_share < min_risk:
            logger.warning(f"Risk per share (${risk_per_share:.2f}) too small, using minimum")
            risk_per_share = min_risk
            stop_loss = entry_price - risk_per_share
        
        # Position sizing: Risk 0.5% per trade
        risk_per_trade = self.risk_config.get('position_sizing', {}).get('risk_per_trade', 0.005)
        account_risk_dollars = account_size * risk_per_trade
        position_size = int(account_risk_dollars / risk_per_share)
        
        # Check max daily loss constraint
        max_daily_loss = self.risk_config.get('position_sizing', {}).get('daily_max_loss', 0.02)
        max_daily_dollars = account_size * max_daily_loss
        max_daily_loss_remaining = max(max_daily_dollars - self.daily_loss, 0)
        
        if account_risk_dollars > max_daily_loss_remaining:
            logger.warning(f"Daily loss limit approaching: ${max_daily_loss_remaining:.2f} remaining")
            position_size = int(max_daily_loss_remaining / risk_per_share) if max_daily_loss_remaining > 0 else 0
        
        if position_size <= 0:
            logger.error("Position size calculated as 0 or negative")
            return None
        
        # Calculate take profits
        tp_config = self.risk_config.get('take_profit', {})
        partial_at_pct = tp_config.get('partial_at_pct', 0.02)
        main_target_rr = tp_config.get('main_target_rr', 2.0)
        
        # TP1: +2% from entry
        take_profit_1 = entry_price * (1 + partial_at_pct)
        
        # TP2: 1:2 risk/reward
        profit_2 = risk_per_share * main_target_rr
        take_profit_2 = entry_price + profit_2
        
        # Calculate actual account risk
        actual_account_risk = (account_risk_dollars / account_size) * 100
        
        # Risk/Reward ratio
        risk_reward = (take_profit_2 - entry_price) / risk_per_share
        
        metrics = RiskMetrics(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            risk_per_share=risk_per_share,
            position_size=position_size,
            position_value=entry_price * position_size,
            account_risk=actual_account_risk,
            risk_reward_ratio=risk_reward,
            max_daily_loss_remaining=max_daily_loss_remaining
        )
        
        logger.info(f"Position calculated: {metrics}")
        return metrics
    
    def validate_risk_reward(self, risk_metrics: RiskMetrics,
                            min_rr: float = 2.0) -> bool:
        """Validate if risk/reward meets minimum
        
        Args:
            risk_metrics: RiskMetrics object
            min_rr: Minimum risk/reward ratio (default 1:2)
            
        Returns:
            True if risk/reward acceptable
        """
        if risk_metrics.risk_reward_ratio < min_rr:
            logger.warning(
                f"Risk/reward {risk_metrics.risk_reward_ratio:.2f}:1 "
                f"below minimum {min_rr}:1"
            )
            return False
        return True
    
    def update_daily_loss(self, realized_loss: float) -> None:
        """Update daily loss counter
        
        Args:
            realized_loss: Realized loss in dollars
        """
        if realized_loss > 0:
            self.daily_loss += realized_loss
            logger.info(f"Daily loss updated: ${self.daily_loss:.2f}")
    
    def should_stop_trading(self, account_size: float) -> bool:
        """Check if daily loss limit exceeded
        
        Args:
            account_size: Total account size
            
        Returns:
            True if should stop trading
        """
        max_daily_loss = self.risk_config.get('position_sizing', {}).get('daily_max_loss', 0.02)
        max_daily_dollars = account_size * max_daily_loss
        
        if self.daily_loss >= max_daily_dollars:
            logger.warning(
                f"Daily loss limit hit: ${self.daily_loss:.2f} >= ${max_daily_dollars:.2f}. "
                f"Stop trading for today."
            )
            return True
        return False
    
    def move_stop_to_breakeven(self, risk_metrics: RiskMetrics,
                               current_price: float) -> Optional[float]:
        """Move stop loss to breakeven after +1R profit
        
        Args:
            risk_metrics: RiskMetrics object
            current_price: Current stock price
            
        Returns:
            New stop loss price or None if not ready
        """
        # Check if trade is at +1R
        profit_at_1r = risk_metrics.entry_price + risk_metrics.risk_per_share
        
        if current_price >= profit_at_1r:
            new_stop = risk_metrics.entry_price
            logger.info(
                f"Moving stop to breakeven: ${risk_metrics.stop_loss:.2f} -> ${new_stop:.2f}"
            )
            return new_stop
        
        return None
    
    def calculate_trailing_stop(self, entry_price: float,
                               current_price: float,
                               current_stop: float,
                               trail_percent: float = 0.02) -> float:
        """Calculate trailing stop loss
        
        Args:
            entry_price: Original entry price
            current_price: Current stock price
            current_stop: Current stop loss
            trail_percent: Trail percentage (default 2%)
            
        Returns:
            New stop loss price
        """
        trailing_stop = current_price * (1 - trail_percent)
        # Never trail below original stop or entry
        new_stop = max(trailing_stop, current_stop, entry_price - 0.01)
        return new_stop
    
    def reset_daily_loss(self) -> None:
        """Reset daily loss counter (call at market open)"""
        self.daily_loss = 0.0
        self.trades_today = []
        logger.info("Daily loss counter reset")
    
    def add_trade_result(self, pnl: float, entry_price: float,
                        exit_price: float, shares: int) -> None:
        """Log trade result
        
        Args:
            pnl: Profit/loss in dollars
            entry_price: Entry price
            exit_price: Exit price
            shares: Number of shares
        """
        trade_result = {
            'pnl': pnl,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'return_pct': ((exit_price - entry_price) / entry_price) * 100
        }
        self.trades_today.append(trade_result)
        
        if pnl < 0:
            self.daily_loss += abs(pnl)
        
        logger.info(f"Trade result: {trade_result['return_pct']:+.2f}% | PnL: ${pnl:+.2f}")
    
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics
        
        Returns:
            Dictionary of daily stats
        """
        if not self.trades_today:
            return {'trades': 0, 'pnl': 0, 'win_rate': 0}
        
        trades = self.trades_today
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = sum(1 for t in trades if t['pnl'] < 0)
        total_pnl = sum(t['pnl'] for t in trades)
        
        return {
            'trades': len(trades),
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(trades)) * 100 if trades else 0,
            'pnl': total_pnl,
            'avg_return': sum(t['return_pct'] for t in trades) / len(trades)
        }
