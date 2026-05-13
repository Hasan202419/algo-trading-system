"""Market Regime Agent - Classifies market conditions"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    BULL = "BULL"
    NEUTRAL = "NEUTRAL"
    BEAR = "BEAR"
    NEWS_LOCK = "NEWS_LOCK"


@dataclass
class RegimeAnalysis:
    """Market regime analysis result"""
    regime: MarketRegime
    confidence: float
    spy_price: float
    spy_ma200: float
    vix_level: float
    breadth_percent: float
    news_events: List[str]
    timestamp: datetime
    
    def __str__(self) -> str:
        return f"{self.regime.value} (confidence: {self.confidence:.1%})"


class MarketRegimeAgent:
    """Analyzes market conditions and classifies market regime"""
    
    def __init__(self, config: Dict = None):
        """Initialize market regime agent
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.regime_history = []
        self.last_regime = None
        
    def analyze(self,
                spy_price: float,
                spy_ma200: float,
                spy_ma50: float,
                vix_level: float,
                breadth_percent: float,
                major_news: List[str] = None,
                recent_macro_events: List[str] = None) -> RegimeAnalysis:
        """Analyze market regime
        
        Args:
            spy_price: Current SPY price
            spy_ma200: SPY 200-day moving average
            spy_ma50: SPY 50-day moving average
            vix_level: VIX index level
            breadth_percent: % of NYSE stocks above 50-day MA
            major_news: List of major news events
            recent_macro_events: Macro events (CPI, FOMC, etc)
            
        Returns:
            RegimeAnalysis object
        """
        major_news = major_news or []
        recent_macro_events = recent_macro_events or []
        
        # Check for NEWS_LOCK conditions
        if self._is_news_lock(major_news, recent_macro_events):
            analysis = RegimeAnalysis(
                regime=MarketRegime.NEWS_LOCK,
                confidence=0.95,
                spy_price=spy_price,
                spy_ma200=spy_ma200,
                vix_level=vix_level,
                breadth_percent=breadth_percent,
                news_events=major_news,
                timestamp=datetime.now()
            )
            self._log_analysis(analysis)
            return analysis
        
        # Determine regime based on technical indicators
        regime, confidence = self._classify_regime(
            spy_price, spy_ma200, spy_ma50, vix_level, breadth_percent
        )
        
        analysis = RegimeAnalysis(
            regime=regime,
            confidence=confidence,
            spy_price=spy_price,
            spy_ma200=spy_ma200,
            vix_level=vix_level,
            breadth_percent=breadth_percent,
            news_events=major_news,
            timestamp=datetime.now()
        )
        
        self._log_analysis(analysis)
        self.last_regime = analysis
        self.regime_history.append(analysis)
        
        return analysis
    
    def _is_news_lock(self, major_news: List[str], macro_events: List[str]) -> bool:
        """Check if market is in NEWS_LOCK condition"""
        lock_keywords = [
            'FOMC', 'CPI', 'NFP', 'FOMC STATEMENT',
            'GEOPOLITICAL CRISIS', 'MARKET HALT',
            'GOVERNMENT SHUTDOWN', 'MAJOR DISASTER'
        ]
        
        for event in major_news + macro_events:
            if any(keyword in str(event).upper() for keyword in lock_keywords):
                return True
        
        return False
    
    def _classify_regime(self,
                        spy_price: float,
                        spy_ma200: float,
                        spy_ma50: float,
                        vix_level: float,
                        breadth_percent: float) -> Tuple[MarketRegime, float]:
        """Classify market regime based on technical indicators"""
        scores = {'bull': 0, 'neutral': 0, 'bear': 0}
        
        # SPY positioning (40% weight)
        if spy_price > spy_ma200:
            scores['bull'] += 40 * 0.5
            if spy_price > spy_ma50:
                scores['bull'] += 40 * 0.5
        elif spy_price > spy_ma50:
            scores['neutral'] += 30
        else:
            scores['bear'] += 40
        
        # VIX level (30% weight)
        if vix_level < 15:
            scores['bull'] += 15
        elif vix_level < 20:
            scores['bull'] += 10
            scores['neutral'] += 5
        elif vix_level < 25:
            scores['neutral'] += 15
        elif vix_level < 30:
            scores['neutral'] += 5
            scores['bear'] += 10
        else:
            scores['bear'] += 30
        
        # Breadth (30% weight)
        if breadth_percent > 0.60:
            scores['bull'] += 30
        elif breadth_percent > 0.50:
            scores['bull'] += 15
            scores['neutral'] += 10
        elif breadth_percent > 0.40:
            scores['neutral'] += 20
        else:
            scores['bear'] += 30
        
        # Determine regime
        total = sum(scores.values())
        if total == 0:
            return MarketRegime.NEUTRAL, 0.50
        
        normalized = {k: v / total for k, v in scores.items()}
        
        if normalized['bull'] > 0.50:
            return MarketRegime.BULL, normalized['bull']
        elif normalized['bear'] > 0.50:
            return MarketRegime.BEAR, normalized['bear']
        else:
            return MarketRegime.NEUTRAL, normalized['neutral']
    
    def _log_analysis(self, analysis: RegimeAnalysis) -> None:
        """Log regime analysis"""
        logger.info(
            f"Market Regime: {analysis.regime.value} | "
            f"Confidence: {analysis.confidence:.1%} | "
            f"SPY: {analysis.spy_price:.2f} | "
            f"MA200: {analysis.spy_ma200:.2f} | "
            f"VIX: {analysis.vix_level:.2f} | "
            f"Breadth: {analysis.breadth_percent:.1%}"
        )
    
    def is_bullish(self) -> bool:
        """Check if market is in bullish regime"""
        if not self.last_regime:
            return False
        return self.last_regime.regime == MarketRegime.BULL
    
    def is_neutral(self) -> bool:
        """Check if market is neutral"""
        if not self.last_regime:
            return True
        return self.last_regime.regime == MarketRegime.NEUTRAL
    
    def is_bearish(self) -> bool:
        """Check if market is in bearish regime"""
        if not self.last_regime:
            return False
        return self.last_regime.regime == MarketRegime.BEAR
    
    def is_news_locked(self) -> bool:
        """Check if market is in NEWS_LOCK"""
        if not self.last_regime:
            return False
        return self.last_regime.regime == MarketRegime.NEWS_LOCK
    
    def get_regime_rules(self) -> Dict:
        """Get trading rules based on current regime"""
        if not self.last_regime:
            return {'allow_all': False}
        
        regime = self.last_regime.regime
        
        rules = {
            MarketRegime.BULL: {
                'allow_breakout': True,
                'allow_trend_continuation': True,
                'allow_pullback': True,
                'allow_vwap_reclaim': True,
                'max_new_trades': 5,
                'description': 'Bullish market - Allow all quality setups'
            },
            MarketRegime.NEUTRAL: {
                'allow_breakout': False,
                'allow_trend_continuation': False,
                'allow_pullback': True,
                'allow_vwap_reclaim': True,
                'max_new_trades': 2,
                'description': 'Neutral market - Only pullback/VWAP setups'
            },
            MarketRegime.BEAR: {
                'allow_breakout': False,
                'allow_trend_continuation': False,
                'allow_pullback': False,
                'allow_vwap_reclaim': False,
                'max_new_trades': 0,
                'description': 'Bearish market - Avoid new longs'
            },
            MarketRegime.NEWS_LOCK: {
                'allow_breakout': False,
                'allow_trend_continuation': False,
                'allow_pullback': False,
                'allow_vwap_reclaim': False,
                'max_new_trades': 0,
                'description': 'NEWS_LOCK - Manage existing positions only'
            }
        }
        
        return rules.get(regime, {})
