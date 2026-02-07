"""
Financial Modeling Prep (FMP) Data Provider.

Requires FMP_API_KEY environment variable.
"""

import os
import requests
from datetime import date, datetime
from typing import Optional, List
import hashlib

from .base import (
    AnalystData,
    BaseRatingsProvider,
    RatingData,
    RatingType,
)


class FMPProvider(BaseRatingsProvider):
    """Data provider using Financial Modeling Prep API."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            print("Warning: FMP_API_KEY not found. FMP provider will not work.")
            
        self._analysts_cache: dict[str, AnalystData] = {}
        self._ratings_cache: list[RatingData] = []

    def _map_rating(self, rating_text: str) -> RatingType:
        """Map FMP rating text to RatingType enum."""
        rating_lower = rating_text.lower()
        if "strong buy" in rating_lower:
            return RatingType.STRONG_BUY
        elif "buy" in rating_lower:
            return RatingType.BUY
        elif "hard buy" in rating_lower: # FMP sometimes uses this
            return RatingType.STRONG_BUY # Map to strong buy?
        elif "hold" in rating_lower or "neutral" in rating_lower:
            return RatingType.HOLD
        elif "sell" in rating_lower:
            return RatingType.SELL
        elif "strong sell" in rating_lower:
            return RatingType.STRONG_SELL
        return RatingType.HOLD

    def get_ratings_for_company(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[RatingData]:
        """Fetch analyst ratings for a company from FMP."""
        if not self.api_key:
            return []
        
        url = f"{self.BASE_URL}/upgrades-downgrades?symbol={ticker}&apikey={self.api_key}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Error fetching FMP data: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            ratings = []
            
            for item in data:
                rating_date_str = item.get("publishedDate", "").split("T")[0]
                if not rating_date_str:
                    continue
                    
                try:
                    rating_date = datetime.strptime(rating_date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                
                if start_date and rating_date < start_date:
                    continue
                if end_date and rating_date > end_date:
                    continue
                    
                firm = item.get("gradingCompany", "Unknown")
                # Create a consistent ID for the analyst/firm
                analyst_id = hashlib.md5(firm.encode()).hexdigest()[:8]
                
                # Cache analyst
                if analyst_id not in self._analysts_cache:
                    self._analysts_cache[analyst_id] = AnalystData(
                        analyst_id=analyst_id,
                        name=f"Analyst at {firm}",
                        firm=firm,
                    )
                
                new_grade = item.get("newGrade", "")
                if not new_grade:
                    continue
                    
                rating_type = self._map_rating(new_grade)
                
                # FMP upgrades-downgrades endpoint sometimes has priceTarget, usually in 'priceTarget' field
                # If not present, it might be None or 0
                price_target = item.get("priceTarget")
                if price_target == 0:
                    price_target = None
                
                ratings.append(RatingData(
                    analyst_id=analyst_id,
                    ticker=ticker,
                    date=rating_date,
                    rating=rating_type,
                    price_target=price_target
                ))
            
            # Cache the fetched ratings
            self._ratings_cache.extend(ratings)
            return ratings

        except Exception as e:
            print(f"Error in FMP provider: {e}")
            return []

    def get_analysts(self) -> List[AnalystData]:
        """Return cached analysts."""
        return list(self._analysts_cache.values())

    def get_ratings_by_analyst(
        self,
        analyst_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[RatingData]:
        """Filter cached ratings by analyst."""
        ratings = [r for r in self._ratings_cache if r.analyst_id == analyst_id]
        if start_date:
            ratings = [r for r in ratings if r.date >= start_date]
        if end_date:
            ratings = [r for r in ratings if r.date <= end_date]
        return ratings

    def get_all_ratings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[RatingData]:
        """Return all cached ratings."""
        ratings = self._ratings_cache
        if start_date:
            ratings = [r for r in ratings if r.date >= start_date]
        if end_date:
            ratings = [r for r in ratings if r.date <= end_date]
        return ratings
