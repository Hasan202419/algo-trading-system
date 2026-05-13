"""Execution Engine - Alpaca paper/live trading integration"""

import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class OrderStatus(Enum):
    """Order status types"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


@dataclass
class BracketOrder:
    """Bracket order with stop loss and take profit"""
    ticker: str
    entry_order_id: str
    entry_price: float
    stop_loss_order_id: str
    stop_loss_price: float
    take_profit_1_id: str
    take_profit_1_price: float
    take_profit_2_id: str
    take_profit_2_price: float
    quantity: int
    timestamp: datetime
    entry_status: OrderStatus = OrderStatus.PENDING
    exit_status: OrderStatus = OrderStatus.PENDING
    
    def __str__(self) -> str:
        return (
            f"{self.ticker} | Entry: {self.entry_price:.2f} x {self.quantity} | "
            f"SL: {self.stop_loss_price:.2f} | TP1: {self.take_profit_1_price:.2f} | "
            f"TP2: {self.take_profit_2_price:.2f}"
        )


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    success: bool
    ticker: str
    entry_price: float
    quantity: int
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    bracket_order: Optional[BracketOrder]
    error_message: str = ""
    timestamp: datetime = None


class ExecutionEngine:
    """Executes trades on Alpaca (paper or live)"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.exec_config = self.config.get('execution', {})
        self.mode = self.exec_config.get('mode', 'paper')
        self.broker = self.exec_config.get('broker', 'alpaca')
        self.active_brackets = []
        self.order_history = []
        
        # Initialize broker connection (placeholder)
        self._init_broker_connection()
        
    def _init_broker_connection(self) -> None:
        """Initialize broker API connection"""
        if self.broker == 'alpaca':
            try:
                api_key = os.getenv('ALPACA_API_KEY')
                secret_key = os.getenv('ALPACA_SECRET_KEY')
                base_url = os.getenv(
                    'ALPACA_BASE_URL',
                    'https://paper-api.alpaca.markets' if self.mode == 'paper' else 'https://api.alpaca.markets'
                )
                
                if not api_key or not secret_key:
                    logger.error("Alpaca API credentials not found in .env")
                    raise ValueError("Missing Alpaca credentials")
                
                logger.info(f"Alpaca connection initialized ({self.mode} mode)")
                # Actual API client would be initialized here
                
            except Exception as e:
                logger.error(f"Failed to initialize broker: {e}")
                raise
    
    def place_bracket_order(self,
                           ticker: str,
                           quantity: int,
                           entry_price: float,
                           stop_loss: float,
                           take_profit_1: float,
                           take_profit_2: float) -> ExecutionResult:
        """Place bracket order (entry + stop loss + take profit)
        
        Args:
            ticker: Stock ticker
            quantity: Number of shares
            entry_price: Entry price (limit order)
            stop_loss: Stop loss price
            take_profit_1: First take profit (partial exit)
            take_profit_2: Second take profit (main exit)
            
        Returns:
            ExecutionResult object
        """
        
        try:
            # Validate inputs
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            if stop_loss >= entry_price:
                raise ValueError("Stop loss must be below entry price")
            
            if take_profit_1 <= entry_price or take_profit_2 <= take_profit_1:
                raise ValueError("Take profits must be above entry and in order")
            
            logger.info(
                f"Placing bracket order: {ticker} x {quantity} @ ${entry_price:.2f} | "
                f"SL: ${stop_loss:.2f} | TP1: ${take_profit_1:.2f} | TP2: ${take_profit_2:.2f}"
            )
            
            # Create bracket order object
            bracket = BracketOrder(
                ticker=ticker,
                entry_order_id=f"{ticker}_entry_{datetime.now().timestamp()}",
                entry_price=entry_price,
                stop_loss_order_id=f"{ticker}_stop_{datetime.now().timestamp()}",
                stop_loss_price=stop_loss,
                take_profit_1_id=f"{ticker}_tp1_{datetime.now().timestamp()}",
                take_profit_1_price=take_profit_1,
                take_profit_2_id=f"{ticker}_tp2_{datetime.now().timestamp()}",
                take_profit_2_price=take_profit_2,
                quantity=quantity,
                timestamp=datetime.now()
            )
            
            # In real implementation, this would submit to broker API
            # For now, simulate successful placement
            if self.mode == 'paper':
                logger.info(f"[PAPER] Bracket order placed: {bracket}")
            else:
                logger.info(f"[LIVE] Bracket order placed: {bracket}")
            
            self.active_brackets.append(bracket)
            
            return ExecutionResult(
                success=True,
                ticker=ticker,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                bracket_order=bracket,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to place bracket order: {e}")
            return ExecutionResult(
                success=False,
                ticker=ticker,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                bracket_order=None,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel specific order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if canceled successfully
        """
        try:
            logger.info(f"Canceling order: {order_id}")
            # API call would go here
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_bracket(self, bracket_order: BracketOrder) -> bool:
        """Cancel entire bracket order
        
        Args:
            bracket_order: BracketOrder to cancel
            
        Returns:
            True if all orders canceled
        """
        try:
            logger.info(f"Canceling bracket order: {bracket_order.ticker}")
            
            # Cancel all legs
            self.cancel_order(bracket_order.entry_order_id)
            self.cancel_order(bracket_order.stop_loss_order_id)
            self.cancel_order(bracket_order.take_profit_1_id)
            self.cancel_order(bracket_order.take_profit_2_id)
            
            # Remove from active brackets
            if bracket_order in self.active_brackets:
                self.active_brackets.remove(bracket_order)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cancel bracket: {e}")
            return False
    
    def get_account_value(self) -> Optional[float]:
        """Get current account equity
        
        Returns:
            Account value in dollars
        """
        try:
            # API call would go here
            # For now, return placeholder
            logger.debug("Fetching account value")
            return 100000.0  # Placeholder
        except Exception as e:
            logger.error(f"Failed to get account value: {e}")
            return None
    
    def get_position(self, ticker: str) -> Optional[Dict]:
        """Get position details
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Position dictionary or None
        """
        try:
            # API call would go here
            logger.debug(f"Fetching position: {ticker}")
            return None  # No position
        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return None
    
    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """Get order status
        
        Args:
            order_id: Order ID
            
        Returns:
            OrderStatus or None
        """
        try:
            # API call would go here
            logger.debug(f"Checking order status: {order_id}")
            return OrderStatus.PENDING  # Placeholder
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None
    
    def get_active_brackets(self) -> List[BracketOrder]:
        """Get list of active bracket orders
        
        Returns:
            List of BracketOrder objects
        """
        return self.active_brackets
    
    def is_market_open(self) -> bool:
        """Check if US stock market is currently open
        
        Returns:
            True if market is open
        """
        from datetime import datetime, time
        import pytz
        
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        
        # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        is_weekday = now.weekday() < 5  # Monday=0, Friday=4
        is_within_hours = market_open <= now.time() <= market_close
        
        return is_weekday and is_within_hours
    
    def get_time_to_close(self) -> int:
        """Get minutes until market close
        
        Returns:
            Minutes until market close
        """
        from datetime import datetime, time
        import pytz
        
        ny_tz = pytz.timezone('America/New_York')
        now = datetime.now(ny_tz)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        minutes = int((market_close - now).total_seconds() / 60)
        return max(minutes, 0)
