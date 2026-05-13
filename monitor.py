"""Real-time Trading Monitor"""

import logging
import asyncio
from datetime import datetime
from typing import Dict
import json
from pathlib import Path

from main import TradingSystem
from src.utils.logger import setup_logger

logger = setup_logger('monitor')


class TradingMonitor:
    """Real-time trading system monitor"""
    
    def __init__(self, trading_system: TradingSystem):
        """Initialize monitor
        
        Args:
            trading_system: TradingSystem instance
        """
        self.system = trading_system
        self.monitoring = False
        
    def start(self) -> None:
        """Start monitoring"""
        self.monitoring = True
        logger.info("Monitor started")
        self._print_header()
    
    def stop(self) -> None:
        """Stop monitoring"""
        self.monitoring = False
        logger.info("Monitor stopped")
    
    def display_status(self) -> None:
        """Display current system status"""
        status = self.system.get_system_status()
        
        print(f"\n{'='*80}")
        print(f"TRADING SYSTEM STATUS - {status['timestamp']}")
        print(f"{'='*80}")
        print(f"Mode: {status['mode'].upper()}")
        print(f"Running: {'YES' if status['running'] else 'NO'}")
        print(f"Account Value: ${status['account_value']:,.2f}" if status['account_value'] else "Account Value: N/A")
        print(f"Active Trades: {status['active_trades']}")
        print(f"Daily Signals: {status['daily_signals']}")
        print(f"Daily Loss: ${status['daily_loss']:+,.2f}")
        print(f"Active Brackets: {status['active_brackets']}")
        print(f"{'='*80}\n")
    
    def display_active_trades(self) -> None:
        """Display active trades"""
        if not self.system.active_trades:
            print("\nNo active trades\n")
            return
        
        print(f"\n{'='*80}")
        print("ACTIVE TRADES")
        print(f"{'='*80}")
        
        for ticker, trade in self.system.active_trades.items():
            print(
                f"{ticker} | Entry: ${trade['entry_price']:.2f} | "
                f"Quantity: {trade['quantity']} | "
                f"SL: ${trade['stop_loss']:.2f} | "
                f"Target: ${trade['target']:.2f}"
            )
        
        print(f"{'='*80}\n")
    
    def display_daily_signals(self, limit: int = 10) -> None:
        """Display recent signals
        
        Args:
            limit: Number of signals to display
        """
        signals = self.system.daily_signals[-limit:]
        
        if not signals:
            print("\nNo signals today\n")
            return
        
        print(f"\n{'='*80}")
        print(f"RECENT SIGNALS (Last {limit})")
        print(f"{'='*80}")
        
        for signal in signals:
            print(
                f"{signal['ticker']} | {signal['setup_type']} | "
                f"Score: {signal['score']:.0f} | {signal['decision']} | "
                f"${signal['price']:.2f}"
            )
        
        print(f"{'='*80}\n")
    
    def _print_header(self) -> None:
        """Print system header"""
        print(f"\n{'='*80}")
        print("HASAN AI ALGO TRADING SYSTEM - MONITOR")
        print(f"{'='*80}")
        print(f"Start Time: {datetime.now()}")
        print(f"Mode: {self.system.execution_engine.mode.upper()}")
        print(f"{'='*80}\n")
    
    async def monitor_loop(self, interval: int = 60) -> None:
        """Monitor system in loop
        
        Args:
            interval: Update interval in seconds
        """
        while self.monitoring:
            self.display_status()
            self.display_active_trades()
            self.display_daily_signals()
            
            await asyncio.sleep(interval)


if __name__ == "__main__":
    # Initialize trading system
    system = TradingSystem('./config/default_config.yaml')
    system.start()
    
    # Initialize monitor
    monitor = TradingMonitor(system)
    monitor.start()
    
    # Run monitoring loop
    try:
        asyncio.run(monitor.monitor_loop(interval=60))
    except KeyboardInterrupt:
        logger.info("Monitor interrupted by user")
        monitor.stop()
        system.stop()
