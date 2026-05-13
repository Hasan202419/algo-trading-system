"""Screener Agent - Finds high-quality stock setups"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StockCandidate:
    """Stock candidate for trading"""
    ticker: str
    company_name: str
    price: float
    average_volume: int
    current_volume: int
    dollar_volume: float
    rvol: float
    today_change_pct: float
    days_up: int
    spread: float
    catalysts: List[str] = field(default_factory=list)
    ortex_data: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_liquid(self, config: Dict) -> bool:
        """Check if stock meets liquidity requirements"""
        return (
            self.average_volume >= config.get('min_average_volume', 1000000) and
            self.dollar_volume >= config.get('min_dollar_volume', 50000000)
        )
    
    def is_extended(self, config: Dict) -> bool:
        """Check if stock is too extended"""
        return self.today_change_pct >= config.get('max_today_change', 0.10)
    
    def already_up_too_much(self, config: Dict) -> bool:
        """Check if stock is already up too much"""
        return self.days_up >= config.get('max_already_up_pct', 0.20)


class ScreenerAgent:
    """Scans for high-quality stock trading candidates"""
    
    def __init__(self, config: Dict = None):
        """Initialize screener agent
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.candidates = []
        self.filtered_candidates = []
        self.last_scan_time = None
        
    def screen(self, stocks_data: List[Dict]) -> List[StockCandidate]:
        """Screen stocks for trading candidates
        
        Args:
            stocks_data: List of stock data dictionaries
            
        Returns:
            List of screened candidates
        """
        logger.info(f"Screening {len(stocks_data)} stocks...")
        
        candidates = []
        for stock in stocks_data:
            try:
                candidate = self._parse_stock_data(stock)
                if self._passes_filters(candidate):
                    candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Error processing {stock.get('ticker', 'UNKNOWN')}: {e}")
        
        self.filtered_candidates = candidates
        self.last_scan_time = datetime.now()
        
        logger.info(f"Found {len(candidates)} candidates after filtering")
        return candidates
    
    def _parse_stock_data(self, stock_data: Dict) -> StockCandidate:
        """Parse raw stock data into StockCandidate"""
        return StockCandidate(
            ticker=stock_data.get('ticker', ''),
            company_name=stock_data.get('name', ''),
            price=float(stock_data.get('price', 0)),
            average_volume=int(stock_data.get('avg_volume', 0)),
            current_volume=int(stock_data.get('volume', 0)),
            dollar_volume=float(stock_data.get('dollar_volume', 0)),
            rvol=float(stock_data.get('rvol', 0)),
            today_change_pct=float(stock_data.get('change_pct', 0)),
            days_up=int(stock_data.get('days_up', 0)),
            spread=float(stock_data.get('spread', 0)),
            catalysts=stock_data.get('catalysts', []),
            ortex_data=stock_data.get('ortex', {}),
            timestamp=datetime.now()
        )
    
    def _passes_filters(self, candidate: StockCandidate) -> bool:
        """Check if candidate passes all filters"""
        filters = self.config.get('filters', {})
        
        # Liquidity checks
        if candidate.average_volume < filters.get('min_average_volume', 1000000):
            logger.debug(f"{candidate.ticker}: Insufficient average volume")
            return False
        
        if candidate.dollar_volume < filters.get('min_dollar_volume', 50000000):
            logger.debug(f"{candidate.ticker}: Insufficient dollar volume")
            return False
        
        # Volume checks
        if candidate.rvol < filters.get('min_rvol', 1.5):
            logger.debug(f"{candidate.ticker}: RVOL too low ({candidate.rvol:.2f})")
            return False
        
        # Change checks
        if candidate.today_change_pct < filters.get('min_today_change', 0.0):
            logger.debug(f"{candidate.ticker}: Change too low")
            return False
        
        if candidate.today_change_pct > filters.get('max_today_change', 0.10):
            logger.debug(f"{candidate.ticker}: Change too high ({candidate.today_change_pct:.1%})")
            return False
        
        if candidate.days_up > filters.get('max_already_up', 0.20):
            logger.debug(f"{candidate.ticker}: Already up too much")
            return False
        
        # Spread check
        if candidate.spread > filters.get('max_spread', 0.05):
            logger.debug(f"{candidate.ticker}: Spread too wide ({candidate.spread:.2f})")
            return False
        
        return True
    
    def get_candidates(self) -> List[StockCandidate]:
        """Get current filtered candidates"""
        return self.filtered_candidates
    
    def rank_by_catalyst(self, candidates: List[StockCandidate]) -> List[StockCandidate]:
        """Rank candidates by catalyst strength"""
        catalyst_scores = {
            'FDA_APPROVAL': 100,
            'EARNINGS_BEAT': 90,
            'ANALYST_UPGRADE': 80,
            'MAJOR_PARTNERSHIP': 85,
            'ACQUISITION': 95,
            'SECTOR_ROTATION': 60,
            'BUYBACK': 70,
            'DIVIDEND_INCREASE': 65,
        }
        
        def get_catalyst_score(candidate: StockCandidate) -> int:
            max_score = 0
            for catalyst in candidate.catalysts:
                score = catalyst_scores.get(catalyst.upper(), 0)
                max_score = max(max_score, score)
            return max_score
        
        return sorted(candidates, key=lambda c: get_catalyst_score(c), reverse=True)
    
    def rank_by_squeeze_potential(self, candidates: List[StockCandidate]) -> List[StockCandidate]:
        """Rank candidates by short squeeze potential (ORTEX)"""
        def get_squeeze_score(candidate: StockCandidate) -> float:
            ortex = candidate.ortex_data or {}
            
            score = 0
            
            # Short interest weight
            short_interest = float(ortex.get('short_interest_pct', 0))
            if short_interest > 30:
                score += 30
            elif short_interest > 20:
                score += 20
            elif short_interest > 10:
                score += 10
            
            # Utilization weight
            utilization = float(ortex.get('utilization_pct', 0))
            if utilization > 90:
                score += 20
            elif utilization > 75:
                score += 10
            
            # Cost to borrow weight
            cost = float(ortex.get('cost_to_borrow_pct', 0))
            if cost > 50:
                score += 15
            elif cost > 20:
                score += 10
            
            # Days to cover weight
            days = float(ortex.get('days_to_cover', 0))
            if days > 5:
                score += 10
            elif days > 3:
                score += 5
            
            return score
        
        return sorted(candidates, key=lambda c: get_squeeze_score(c), reverse=True)
