"""Score Engine - Evaluates trade quality with probabilistic scoring"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TradeDecision(Enum):
    """Trade decision based on score"""
    BUY = "BUY"
    WATCH = "WATCH"
    REJECT = "REJECT"


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown"""
    volume_score: float
    trend_score: float
    structure_score: float
    momentum_score: float
    market_score: float
    catalyst_score: float
    total_score: float
    hard_gates_passed: bool
    decision: TradeDecision
    reasoning: str


class ScoreEngine:
    """Scores trading opportunities on 100-point scale"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.scoring_config = self.config.get('scoring', {})
        
    def score_trade(self,
                   screener_candidate,
                   technical_analysis,
                   market_regime_analysis,
                   risk_reward: float = None) -> ScoreBreakdown:
        """Score a trade opportunity
        
        Args:
            screener_candidate: StockCandidate from screener
            technical_analysis: TechnicalAnalysis from signal agent
            market_regime_analysis: RegimeAnalysis from market regime agent
            risk_reward: Risk/reward ratio
            
        Returns:
            ScoreBreakdown object
        """
        
        # Check hard gates first
        hard_gates_passed = self._check_hard_gates(
            screener_candidate,
            technical_analysis,
            market_regime_analysis,
            risk_reward
        )
        
        if not hard_gates_passed:
            return ScoreBreakdown(
                volume_score=0,
                trend_score=0,
                structure_score=0,
                momentum_score=0,
                market_score=0,
                catalyst_score=0,
                total_score=0,
                hard_gates_passed=False,
                decision=TradeDecision.REJECT,
                reasoning="Hard gate rules failed - Trade rejected"
            )
        
        # Calculate individual scores
        volume_score = self._score_volume(screener_candidate)
        trend_score = self._score_trend(technical_analysis)
        structure_score = self._score_structure(technical_analysis)
        momentum_score = self._score_momentum(technical_analysis)
        market_score = self._score_market(market_regime_analysis)
        catalyst_score = self._score_catalyst(screener_candidate)
        
        # Total score
        total_score = (
            volume_score +
            trend_score +
            structure_score +
            momentum_score +
            market_score +
            catalyst_score
        )
        
        # Decision
        decision, reasoning = self._make_decision(total_score, technical_analysis)
        
        return ScoreBreakdown(
            volume_score=volume_score,
            trend_score=trend_score,
            structure_score=structure_score,
            momentum_score=momentum_score,
            market_score=market_score,
            catalyst_score=catalyst_score,
            total_score=total_score,
            hard_gates_passed=True,
            decision=decision,
            reasoning=reasoning
        )
    
    def _check_hard_gates(self,
                         candidate,
                         technical,
                         regime,
                         risk_reward) -> bool:
        """Check non-negotiable hard gates"""
        
        gates = self.config.get('hard_gates', {})
        
        # Liquidity gates
        if candidate.average_volume < gates.get('liquidity', {}).get('min_average_volume', 1000000):
            logger.debug(f"Hard gate failed: Average volume too low")
            return False
        
        if candidate.dollar_volume < gates.get('liquidity', {}).get('min_dollar_volume', 50000000):
            logger.debug(f"Hard gate failed: Dollar volume too low")
            return False
        
        if candidate.spread > gates.get('liquidity', {}).get('max_spread', 0.05):
            logger.debug(f"Hard gate failed: Spread too wide")
            return False
        
        # Technical gates
        if not technical.price_above_vwap:
            logger.debug(f"Hard gate failed: Price below VWAP")
            return False
        
        if not technical.price_above_ema20:
            logger.debug(f"Hard gate failed: Price below EMA20")
            return False
        
        # Risk/Reward gate
        if risk_reward and risk_reward < gates.get('technical', {}).get('min_risk_reward', 2.0):
            logger.debug(f"Hard gate failed: Risk/reward < 1:2")
            return False
        
        # No parabolic chasing
        if technical.last_candle and technical.last_candle.is_parabolic:
            logger.debug(f"Hard gate failed: Parabolic candle detected")
            return False
        
        # Market panic check
        if regime.vix_level > 40:
            logger.debug(f"Hard gate failed: VIX too high (market panic)")
            return False
        
        # NEWS_LOCK check
        if regime.regime.value == "NEWS_LOCK":
            logger.debug(f"Hard gate failed: Market in NEWS_LOCK")
            return False
        
        return True
    
    def _score_volume(self, candidate, max_points: float = 20) -> float:
        """Score volume metrics"""
        score = 0
        
        # RVOL scoring
        if candidate.rvol > 2.5:
            score += max_points * 0.4
        elif candidate.rvol > 2.0:
            score += max_points * 0.35
        elif candidate.rvol > 1.5:
            score += max_points * 0.25
        else:
            score += max_points * 0.1
        
        # Dollar volume scoring
        if candidate.dollar_volume > 200000000:
            score += max_points * 0.3
        elif candidate.dollar_volume > 100000000:
            score += max_points * 0.25
        elif candidate.dollar_volume > 50000000:
            score += max_points * 0.15
        
        # Current volume ratio
        ratio = candidate.current_volume / max(candidate.average_volume, 1)
        if ratio > 3.0:
            score += max_points * 0.3
        elif ratio > 2.0:
            score += max_points * 0.2
        elif ratio > 1.5:
            score += max_points * 0.1
        
        return min(score, max_points)
    
    def _score_trend(self, technical, max_points: float = 20) -> float:
        """Score trend alignment"""
        score = 0
        
        # EMA alignment (9 > 20 > 50)
        if technical.ema9 > technical.ema20 > technical.ema50:
            score += max_points * 0.4
        elif technical.ema9 > technical.ema20:
            score += max_points * 0.25
        else:
            score += 0
        
        # Price above VWAP
        if technical.price_above_vwap:
            score += max_points * 0.3
        
        # RSI in zone (52-72)
        if technical.rsi_in_zone:
            score += max_points * 0.3
        elif 40 < technical.rsi < 80:
            score += max_points * 0.15
        
        return min(score, max_points)
    
    def _score_structure(self, technical, max_points: float = 20) -> float:
        """Score price structure"""
        score = 0
        
        # Higher low pattern
        if technical.higher_low:
            score += max_points * 0.4
        
        # Support near (price close to EMA20)
        distance_to_ema20 = (technical.price - technical.ema20) / technical.ema20
        if 0 < distance_to_ema20 < 0.02:  # Within 2% of EMA20
            score += max_points * 0.3
        elif 0 < distance_to_ema20 < 0.05:
            score += max_points * 0.2
        
        # Entry signal type
        if str(technical.entry_signal.value) in ['VWAP_RECLAIM', 'HIGHER_LOW_PULLBACK']:
            score += max_points * 0.3
        elif str(technical.entry_signal.value) == 'RESISTANCE_BREAKOUT':
            score += max_points * 0.25
        
        return min(score, max_points)
    
    def _score_momentum(self, technical, max_points: float = 20) -> float:
        """Score momentum indicators"""
        score = 0
        
        # ADX strength (trend strength)
        if technical.adx > 25:
            score += max_points * 0.4
        elif technical.adx > 18:
            score += max_points * 0.3
        elif technical.adx > 15:
            score += max_points * 0.15
        
        # Buy pressure > sell pressure
        if technical.buy_pressure > technical.sell_pressure:
            pressure_diff = (technical.buy_pressure - technical.sell_pressure) / max(technical.buy_pressure, 0.1)
            if pressure_diff > 0.5:
                score += max_points * 0.3
            elif pressure_diff > 0.2:
                score += max_points * 0.15
        
        # No parabolic candles
        if not (technical.last_candle and technical.last_candle.is_parabolic):
            score += max_points * 0.3
        
        return min(score, max_points)
    
    def _score_market(self, regime, max_points: float = 10) -> float:
        """Score market conditions"""
        score = 0
        
        # Market regime
        regime_value = regime.regime.value
        if regime_value == "BULL":
            score += max_points * 0.5
        elif regime_value == "NEUTRAL":
            score += max_points * 0.25
        else:  # BEAR or NEWS_LOCK
            score += 0
        
        # Breadth (advancing stocks %)
        if regime.breadth_percent > 0.60:
            score += max_points * 0.5
        elif regime.breadth_percent > 0.50:
            score += max_points * 0.3
        
        return min(score, max_points)
    
    def _score_catalyst(self, candidate, max_points: float = 10) -> float:
        """Score catalyst and squeeze potential"""
        score = 0
        
        # Catalyst strength
        catalyst_scores = {
            'FDA_APPROVAL': 10,
            'ACQUISITION': 9,
            'EARNINGS_BEAT': 8,
            'MAJOR_PARTNERSHIP': 8,
            'ANALYST_UPGRADE': 7,
            'SECTOR_ROTATION': 5,
            'BUYBACK': 6,
            'DIVIDEND_INCREASE': 5,
        }
        
        for catalyst in candidate.catalysts:
            catalyst_score = catalyst_scores.get(catalyst.upper(), 0)
            score = max(score, catalyst_score * (max_points / 10))
        
        # ORTEX squeeze potential
        ortex = candidate.ortex_data or {}
        short_interest = float(ortex.get('short_interest_pct', 0))
        
        if short_interest > 30:
            score += (max_points / 2) * 0.5
        elif short_interest > 20:
            score += (max_points / 2) * 0.3
        
        return min(score, max_points)
    
    def _make_decision(self, total_score: float, technical) -> tuple:
        """Make BUY/WATCH/REJECT decision"""
        thresholds = self.scoring_config.get('thresholds', {})
        buy_min = thresholds.get('buy_minimum', 70)
        watch_min = thresholds.get('watch_minimum', 60)
        
        if total_score >= buy_min:
            reasoning = f"Strong setup: Score {total_score:.1f} >= {buy_min}. {technical.entry_signal.value}"
            return TradeDecision.BUY, reasoning
        elif total_score >= watch_min:
            reasoning = f"Monitoring setup: Score {total_score:.1f} between {watch_min}-{buy_min}. Wait for better entry."
            return TradeDecision.WATCH, reasoning
        else:
            reasoning = f"Weak setup: Score {total_score:.1f} < {watch_min}. Setup quality insufficient."
            return TradeDecision.REJECT, reasoning
