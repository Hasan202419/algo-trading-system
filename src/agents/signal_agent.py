"""Signal Agent - 5-minute technical analysis and entry signals"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class EntryType(Enum):
    """Entry signal types"""
    VWAP_RECLAIM = "VWAP_RECLAIM"
    HIGHER_LOW_PULLBACK = "HIGHER_LOW_PULLBACK"
    RESISTANCE_BREAKOUT = "RESISTANCE_BREAKOUT"
    TREND_CONTINUATION = "TREND_CONTINUATION"
    NONE = "NONE"


@dataclass
class CandleAnalysis:
    """Candle analysis result"""
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    body_size: float
    wick_ratio: float
    is_parabolic: bool
    is_hammer: bool
    is_doji: bool


@dataclass
class TechnicalAnalysis:
    """Technical analysis result"""
    ticker: str
    timestamp: datetime
    price: float
    vwap: float
    ema9: float
    ema20: float
    ema50: float
    ema100: float
    ema200: float
    rsi: float
    adx: float
    volume: int
    avg_volume: int
    price_above_vwap: bool
    price_above_ema9: bool
    price_above_ema20: bool
    ema9_above_ema20: bool
    rsi_in_zone: bool
    adx_strong: bool
    higher_low: bool
    buy_pressure: float
    sell_pressure: float
    last_candle: CandleAnalysis
    prev_candle: CandleAnalysis
    entry_signal: EntryType
    
    def is_bullish(self) -> bool:
        """Check if technical setup is bullish"""
        return (
            self.price_above_vwap and
            self.price_above_ema9 and
            self.price_above_ema20 and
            self.ema9_above_ema20
        )


class SignalAgent:
    """Analyzes 5-minute technical indicators and generates entry signals"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.price_history = {}
        self.signal_history = []
        
    def analyze(self,
                ticker: str,
                ohlcv_data: pd.DataFrame) -> TechnicalAnalysis:
        """Analyze stock for trading signals
        
        Args:
            ticker: Stock ticker
            ohlcv_data: DataFrame with columns [open, high, low, close, volume]
            
        Returns:
            TechnicalAnalysis object
        """
        if len(ohlcv_data) < 100:
            logger.warning(f"{ticker}: Insufficient data for analysis")
            return None
        
        # Calculate technical indicators
        vwap = self._calculate_vwap(ohlcv_data)
        ema9 = self._calculate_ema(ohlcv_data['close'], 9)
        ema20 = self._calculate_ema(ohlcv_data['close'], 20)
        ema50 = self._calculate_ema(ohlcv_data['close'], 50)
        ema100 = self._calculate_ema(ohlcv_data['close'], 100)
        ema200 = self._calculate_ema(ohlcv_data['close'], 200)
        rsi = self._calculate_rsi(ohlcv_data['close'], 14)
        adx = self._calculate_adx(ohlcv_data)
        
        # Current values
        current_price = ohlcv_data['close'].iloc[-1]
        current_volume = ohlcv_data['volume'].iloc[-1]
        avg_volume = ohlcv_data['volume'].rolling(20).mean().iloc[-1]
        
        # Candle analysis
        last_candle = self._analyze_candle(ohlcv_data.iloc[-1])
        prev_candle = self._analyze_candle(ohlcv_data.iloc[-2]) if len(ohlcv_data) > 1 else None
        
        # Boolean conditions
        price_above_vwap = current_price > vwap[-1]
        price_above_ema9 = current_price > ema9[-1]
        price_above_ema20 = current_price > ema20[-1]
        ema9_above_ema20 = ema9[-1] > ema20[-1]
        rsi_in_zone = 52 <= rsi[-1] <= 72
        adx_strong = adx[-1] > 18
        
        # Structure analysis
        higher_low = self._detect_higher_low(ohlcv_data)
        buy_pressure, sell_pressure = self._analyze_buy_sell_pressure(ohlcv_data)
        
        # Entry signal detection
        entry_signal = self._detect_entry_signal(
            current_price, vwap[-1], ema20[-1], ema9[-1],
            higher_low, buy_pressure, sell_pressure,
            last_candle.is_parabolic if last_candle else False
        )
        
        analysis = TechnicalAnalysis(
            ticker=ticker,
            timestamp=datetime.now(),
            price=current_price,
            vwap=vwap[-1],
            ema9=ema9[-1],
            ema20=ema20[-1],
            ema50=ema50[-1],
            ema100=ema100[-1],
            ema200=ema200[-1],
            rsi=rsi[-1],
            adx=adx[-1],
            volume=current_volume,
            avg_volume=int(avg_volume),
            price_above_vwap=price_above_vwap,
            price_above_ema9=price_above_ema9,
            price_above_ema20=price_above_ema20,
            ema9_above_ema20=ema9_above_ema20,
            rsi_in_zone=rsi_in_zone,
            adx_strong=adx_strong,
            higher_low=higher_low,
            buy_pressure=buy_pressure,
            sell_pressure=sell_pressure,
            last_candle=last_candle,
            prev_candle=prev_candle,
            entry_signal=entry_signal
        )
        
        self.signal_history.append(analysis)
        return analysis
    
    def _calculate_vwap(self, ohlcv_data: pd.DataFrame) -> np.ndarray:
        """Calculate Volume Weighted Average Price"""
        typical_price = (ohlcv_data['high'] + ohlcv_data['low'] + ohlcv_data['close']) / 3
        cum_volume = ohlcv_data['volume'].cumsum()
        cum_tp_volume = (typical_price * ohlcv_data['volume']).cumsum()
        vwap = cum_tp_volume / cum_volume
        return vwap.values
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean().values
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.values
    
    def _calculate_adx(self, ohlcv_data: pd.DataFrame, period: int = 14) -> np.ndarray:
        """Calculate Average Directional Index"""
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        close = ohlcv_data['close']
        
        tr = self._calculate_true_range(high, low, close)
        atr = tr.rolling(window=period).mean()
        
        plus_dm = np.where(high.diff() > low.diff() * -1, high.diff(), 0)
        minus_dm = np.where(low.diff() * -1 > high.diff(), low.diff() * -1, 0)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.values
    
    def _calculate_true_range(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate True Range for ATR"""
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    def _analyze_candle(self, candle: pd.Series) -> CandleAnalysis:
        """Analyze single candle"""
        open_p = candle['open']
        high = candle['high']
        low = candle['low']
        close = candle['close']
        volume = candle['volume']
        
        body_size = abs(close - open_p)
        wick_up = high - max(open_p, close)
        wick_down = min(open_p, close) - low
        total_range = high - low
        wick_ratio = max(wick_up, wick_down) / total_range if total_range > 0 else 0
        
        # Parabolic candle: large body with small wicks
        is_parabolic = body_size > (total_range * 0.7) and wick_ratio < 0.15
        
        # Hammer: small body, long lower wick
        is_hammer = wick_down > (body_size * 2) and wick_up < body_size
        
        # Doji: open == close
        is_doji = abs(open_p - close) < 0.01
        
        return CandleAnalysis(
            open=open_p,
            high=high,
            low=low,
            close=close,
            volume=volume,
            timestamp=candle.name if hasattr(candle, 'name') else datetime.now(),
            body_size=body_size,
            wick_ratio=wick_ratio,
            is_parabolic=is_parabolic,
            is_hammer=is_hammer,
            is_doji=is_doji
        )
    
    def _detect_higher_low(self, ohlcv_data: pd.DataFrame, lookback: int = 5) -> bool:
        """Detect higher low pattern in last N candles"""
        if len(ohlcv_data) < lookback + 1:
            return False
        
        lows = ohlcv_data['low'].tail(lookback).values
        return lows[-1] > lows[-2]  # Current low higher than previous low
    
    def _analyze_buy_sell_pressure(self, ohlcv_data: pd.DataFrame) -> Tuple[float, float]:
        """Analyze buy vs sell pressure using volume distribution"""
        last_candle = ohlcv_data.iloc[-1]
        
        # Calculate body size and color
        body_size = abs(last_candle['close'] - last_candle['open'])
        is_bullish = last_candle['close'] > last_candle['open']
        
        # Volume distribution
        volume = last_candle['volume']
        avg_volume = ohlcv_data['volume'].rolling(20).mean().iloc[-1]
        
        # Buy pressure: bullish candle with volume > average
        buy_pressure = 1.0 if (is_bullish and volume > avg_volume) else 0.5 if is_bullish else 0.2
        
        # Sell pressure: bearish candle with volume > average
        sell_pressure = 1.0 if (not is_bullish and volume > avg_volume) else 0.5 if not is_bullish else 0.2
        
        return buy_pressure, sell_pressure
    
    def _detect_entry_signal(self,
                            price: float,
                            vwap: float,
                            ema20: float,
                            ema9: float,
                            higher_low: bool,
                            buy_pressure: float,
                            sell_pressure: float,
                            is_parabolic: bool) -> EntryType:
        """Detect entry signal type"""
        
        # Hard gate: no parabolic candles
        if is_parabolic:
            return EntryType.NONE
        
        # Hard gate: price must be above VWAP and EMA20
        if price <= vwap or price <= ema20:
            return EntryType.NONE
        
        # Hard gate: buy pressure > sell pressure
        if buy_pressure <= sell_pressure:
            return EntryType.NONE
        
        # VWAP Reclaim: price bounces above VWAP
        if price > vwap and buy_pressure > 0.7:
            return EntryType.VWAP_RECLAIM
        
        # Higher Low Pullback: price forms higher low near support
        if higher_low and price > ema20 and buy_pressure > 0.6:
            return EntryType.HIGHER_LOW_PULLBACK
        
        # Resistance Breakout: price breaks above recent resistance
        if price > ema9 and buy_pressure > 0.8:
            return EntryType.RESISTANCE_BREAKOUT
        
        return EntryType.NONE
