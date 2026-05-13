"""Learning Agent - Daily performance analysis and optimization"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class SetupPerformance:
    """Performance metrics for a setup type"""
    setup_type: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    total_return_pct: float
    best_trade: float
    worst_trade: float
    avg_r_multiple: float


@dataclass
class RegimePerformance:
    """Performance metrics by market regime"""
    regime: str
    trades: int
    wins: int
    win_rate: float
    total_return_pct: float
    profit_factor: float
    avg_r_multiple: float


@dataclass
class DailyReport:
    """Daily trading report"""
    date: str
    total_trades: int
    total_wins: int
    total_losses: int
    win_rate: float
    daily_pnl: float
    daily_return_pct: float
    largest_win: float
    largest_loss: float
    setup_performances: List[SetupPerformance]
    regime_performances: List[RegimePerformance]
    alerts: List[str]
    recommendations: List[str]


class LearningAgent:
    """Analyzes trading performance and recommends optimizations"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.learning_config = self.config.get('learning', {})
        self.trade_history = []
        self.signal_history = []
        self.daily_reports = []
        
    def add_trade(self, trade_record: Dict) -> None:
        """Add trade to history
        
        Args:
            trade_record: Dictionary with trade details
        """
        self.trade_history.append(trade_record)
        logger.debug(f"Trade added to history: {trade_record.get('ticker')}")
    
    def add_signal(self, signal_record: Dict) -> None:
        """Add signal to history
        
        Args:
            signal_record: Dictionary with signal details
        """
        self.signal_history.append(signal_record)
    
    def generate_daily_report(self) -> DailyReport:
        """Generate daily performance report
        
        Returns:
            DailyReport object
        """
        
        if not self.trade_history:
            logger.warning("No trades to analyze")
            return None
        
        today = datetime.now().strftime('%Y-%m-%d')
        trades = [t for t in self.trade_history if t.get('date') == today]
        
        if not trades:
            logger.info("No trades today")
            return None
        
        # Calculate basic metrics
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losses = total_trades - wins
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        daily_pnl = sum(t.get('pnl', 0) for t in trades)
        daily_return_pct = (daily_pnl / (sum(t.get('position_value', 0) for t in trades) / total_trades)) * 100
        
        largest_win = max((t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0), default=0)
        largest_loss = min((t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0), default=0)
        
        # Setup performance analysis
        setup_performances = self._analyze_setup_performance(trades)
        
        # Regime performance analysis
        regime_performances = self._analyze_regime_performance(trades)
        
        # Generate alerts
        alerts = self._generate_alerts(trades, win_rate, setup_performances)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(trades, setup_performances, regime_performances)
        
        report = DailyReport(
            date=today,
            total_trades=total_trades,
            total_wins=wins,
            total_losses=losses,
            win_rate=win_rate,
            daily_pnl=daily_pnl,
            daily_return_pct=daily_return_pct,
            largest_win=largest_win,
            largest_loss=largest_loss,
            setup_performances=setup_performances,
            regime_performances=regime_performances,
            alerts=alerts,
            recommendations=recommendations
        )
        
        self.daily_reports.append(report)
        self._log_report(report)
        
        return report
    
    def _analyze_setup_performance(self, trades: List[Dict]) -> List[SetupPerformance]:
        """Analyze performance by setup type
        
        Args:
            trades: List of trade records
            
        Returns:
            List of SetupPerformance objects
        """
        setup_groups = {}
        
        for trade in trades:
            setup = trade.get('setup_type', 'UNKNOWN')
            if setup not in setup_groups:
                setup_groups[setup] = []
            setup_groups[setup].append(trade)
        
        performances = []
        
        for setup, group in setup_groups.items():
            trades_count = len(group)
            wins = sum(1 for t in group if t.get('pnl', 0) > 0)
            losses = trades_count - wins
            win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
            
            winning_trades = [t for t in group if t.get('pnl', 0) > 0]
            losing_trades = [t for t in group if t.get('pnl', 0) < 0]
            
            avg_profit = (sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)) if winning_trades else 0
            avg_loss = (sum(abs(t.get('pnl', 0)) for t in losing_trades) / len(losing_trades)) if losing_trades else 0
            
            profit_factor = (avg_profit * wins) / (avg_loss * losses) if losses > 0 and avg_loss > 0 else float('inf')
            
            total_return = sum(t.get('pnl', 0) for t in group)
            total_return_pct = (total_return / (sum(t.get('position_value', 0) for t in group) / trades_count)) * 100
            
            best_trade = max((t.get('pnl', 0) for t in group), default=0)
            worst_trade = min((t.get('pnl', 0) for t in group), default=0)
            
            avg_r = sum(t.get('r_multiple', 0) for t in group) / trades_count if trades_count > 0 else 0
            
            performances.append(SetupPerformance(
                setup_type=setup,
                trades=trades_count,
                wins=wins,
                losses=losses,
                win_rate=win_rate,
                avg_profit=avg_profit,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                total_return_pct=total_return_pct,
                best_trade=best_trade,
                worst_trade=worst_trade,
                avg_r_multiple=avg_r
            ))
        
        return performances
    
    def _analyze_regime_performance(self, trades: List[Dict]) -> List[RegimePerformance]:
        """Analyze performance by market regime
        
        Args:
            trades: List of trade records
            
        Returns:
            List of RegimePerformance objects
        """
        regime_groups = {}
        
        for trade in trades:
            regime = trade.get('market_regime', 'UNKNOWN')
            if regime not in regime_groups:
                regime_groups[regime] = []
            regime_groups[regime].append(trade)
        
        performances = []
        
        for regime, group in regime_groups.items():
            trades_count = len(group)
            wins = sum(1 for t in group if t.get('pnl', 0) > 0)
            win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
            
            total_return = sum(t.get('pnl', 0) for t in group)
            total_return_pct = (total_return / (sum(t.get('position_value', 0) for t in group) / trades_count)) * 100 if group else 0
            
            winning_trades = [t for t in group if t.get('pnl', 0) > 0]
            losing_trades = [t for t in group if t.get('pnl', 0) < 0]
            
            avg_profit = (sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)) if winning_trades else 0
            avg_loss = (sum(abs(t.get('pnl', 0)) for t in losing_trades) / len(losing_trades)) if losing_trades else 0
            
            profit_factor = (avg_profit * wins) / (avg_loss * (trades_count - wins)) if (trades_count - wins) > 0 and avg_loss > 0 else float('inf')
            
            avg_r = sum(t.get('r_multiple', 0) for t in group) / trades_count if trades_count > 0 else 0
            
            performances.append(RegimePerformance(
                regime=regime,
                trades=trades_count,
                wins=wins,
                win_rate=win_rate,
                total_return_pct=total_return_pct,
                profit_factor=profit_factor,
                avg_r_multiple=avg_r
            ))
        
        return performances
    
    def _generate_alerts(self, trades: List[Dict], win_rate: float,
                        setup_perfs: List[SetupPerformance]) -> List[str]:
        """Generate alerts based on performance
        
        Args:
            trades: List of trade records
            win_rate: Overall win rate
            setup_perfs: Setup performance list
            
        Returns:
            List of alert strings
        """
        alerts = []
        
        if win_rate < 40:
            alerts.append("⚠️ Win rate below 40% - Review entry criteria")
        
        if win_rate > 70:
            alerts.append("✅ Excellent win rate > 70% - Maintain current strategy")
        
        # Check for fake breakouts
        fake_breakouts = sum(1 for t in trades if t.get('reason_exit') == 'FAKE_BREAKOUT')
        if fake_breakouts > 2:
            alerts.append(f"⚠️ {fake_breakouts} fake breakouts detected - Tighten breakout criteria")
        
        # Check for extended losses
        recent_trades = trades[-5:] if len(trades) >= 5 else trades
        recent_losses = sum(1 for t in recent_trades if t.get('pnl', 0) < 0)
        if recent_losses >= 4:
            alerts.append("⚠️ 4+ losses in last 5 trades - Take a break and review")
        
        # Check setup performance
        for setup in setup_perfs:
            if setup.trades >= 5 and setup.win_rate < 30:
                alerts.append(f"⚠️ {setup.setup_type}: Win rate {setup.win_rate:.0f}% - Consider reducing frequency")
        
        return alerts
    
    def _generate_recommendations(self, trades: List[Dict],
                                 setup_perfs: List[SetupPerformance],
                                 regime_perfs: List[RegimePerformance]) -> List[str]:
        """Generate trading recommendations
        
        Args:
            trades: List of trade records
            setup_perfs: Setup performance list
            regime_perfs: Regime performance list
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Best performing setup
        best_setup = max(setup_perfs, key=lambda x: x.profit_factor, default=None)
        if best_setup and best_setup.trades >= 3:
            recommendations.append(
                f"📈 {best_setup.setup_type} is working well ({best_setup.win_rate:.0f}% WR, {best_setup.profit_factor:.2f} PF) - "
                f"Consider trading more of this setup"
            )
        
        # Best performing regime
        best_regime = max(regime_perfs, key=lambda x: x.profit_factor, default=None)
        if best_regime and best_regime.trades >= 2:
            recommendations.append(
                f"🎯 {best_regime.regime} regime is most profitable - "
                f"Allocate more trades in this market condition"
            )
        
        # Risk management recommendation
        if trades:
            avg_r = sum(t.get('r_multiple', 0) for t in trades) / len(trades)
            if avg_r < 1.5:
                recommendations.append(
                    f"💰 Average R/R ({avg_r:.2f}) below 1:2 target - "
                    f"Wait for better entries with higher targets"
                )
        
        # Time-based recommendation
        if len(trades) >= 10:
            recommendations.append("✅ Sufficient sample size (10+ trades) - Parameters are reliable")
        else:
            remaining = 10 - len(trades)
            recommendations.append(f"📊 Need {remaining} more trades for statistical significance")
        
        return recommendations
    
    def _log_report(self, report: DailyReport) -> None:
        """Log daily report
        
        Args:
            report: DailyReport object
        """
        logger.info(
            f"\n{'='*80}\n"
            f"DAILY REPORT - {report.date}\n"
            f"{'='*80}\n"
            f"Trades: {report.total_trades} | Wins: {report.total_wins} | "
            f"Losses: {report.total_losses} | Win Rate: {report.win_rate:.1f}%\n"
            f"Daily P&L: ${report.daily_pnl:+.2f} | Return: {report.daily_return_pct:+.2f}%\n"
            f"Best: ${report.largest_win:+.2f} | Worst: ${report.largest_loss:+.2f}\n"
            f"{'='*80}\n"
        )
        
        for setup in report.setup_performances:
            logger.info(
                f"Setup: {setup.setup_type} | Trades: {setup.trades} | "
                f"WR: {setup.win_rate:.1f}% | PF: {setup.profit_factor:.2f} | "
                f"Avg R: {setup.avg_r_multiple:.2f}"
            )
        
        for alert in report.alerts:
            logger.warning(alert)
        
        for rec in report.recommendations:
            logger.info(rec)
    
    def detect_fake_breakouts(self) -> List[Dict]:
        """Detect fake breakout patterns
        
        Returns:
            List of fake breakout trade records
        """
        fake_breakouts = []
        
        for trade in self.trade_history:
            # Fake breakout: price breaks above resistance but reverses within N candles
            if trade.get('setup_type') == 'RESISTANCE_BREAKOUT':
                if trade.get('exit_reason') in ['STRUCTURE_BREAK', 'LOWER_LOW', 'EMA9_CLOSE']:
                    if trade.get('duration_minutes', 0) < 15:  # Exited quickly
                        fake_breakouts.append(trade)
        
        return fake_breakouts
    
    def export_report(self, report: DailyReport, filepath: str) -> bool:
        """Export daily report to JSON file
        
        Args:
            report: DailyReport object
            filepath: Output file path
            
        Returns:
            True if successful
        """
        try:
            report_dict = {
                'date': report.date,
                'total_trades': report.total_trades,
                'total_wins': report.total_wins,
                'win_rate': report.win_rate,
                'daily_pnl': report.daily_pnl,
                'daily_return_pct': report.daily_return_pct,
                'setup_performances': [
                    {
                        'setup_type': s.setup_type,
                        'trades': s.trades,
                        'win_rate': s.win_rate,
                        'profit_factor': s.profit_factor,
                        'avg_r_multiple': s.avg_r_multiple
                    }
                    for s in report.setup_performances
                ],
                'regime_performances': [
                    {
                        'regime': r.regime,
                        'trades': r.trades,
                        'win_rate': r.win_rate,
                        'profit_factor': r.profit_factor
                    }
                    for r in report.regime_performances
                ],
                'alerts': report.alerts,
                'recommendations': report.recommendations
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2)
            
            logger.info(f"Report exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False
