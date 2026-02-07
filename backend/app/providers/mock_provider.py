"""
Mock data provider for testing and demonstration.

Generates synthetic analyst ratings with controlled accuracy levels
to test the ranking algorithms.
"""

import random
from datetime import date, timedelta
from typing import Optional

from .base import (
    AnalystData,
    BaseRatingsProvider,
    BaseStockProvider,
    CompanyData,
    PriceData,
    RatingData,
    RatingType,
)


# Sample analyst firms for mock data
MOCK_FIRMS = [
    "Goldman Sachs",
    "Morgan Stanley",
    "JP Morgan",
    "Bank of America",
    "Citigroup",
    "Wells Fargo",
    "Barclays",
    "Deutsche Bank",
    "Credit Suisse",
    "UBS",
    "Jefferies",
    "Raymond James",
    "Piper Sandler",
    "Stifel",
    "Cowen",
]


class MockProvider(BaseRatingsProvider):
    """
    Mock provider that generates synthetic analyst ratings.
    
    Useful for:
    - Testing ranking algorithms
    - Demonstrating the application
    - Supplementing real data where gaps exist
    """

    def __init__(
        self,
        num_analysts: int = 50,
        ratings_per_analyst: int = 100,
        seed: int = 42
    ):
        """
        Initialize mock provider.
        
        Args:
            num_analysts: Number of mock analysts to generate.
            ratings_per_analyst: Average ratings per analyst.
            seed: Random seed for reproducibility.
        """
        self.num_analysts = num_analysts
        self.ratings_per_analyst = ratings_per_analyst
        self.seed = seed
        random.seed(seed)

        self._analysts: list[AnalystData] = []
        self._ratings: list[RatingData] = []
        self._generated = False

    def _generate_analysts(self) -> None:
        """Generate mock analysts."""
        for i in range(self.num_analysts):
            firm = random.choice(MOCK_FIRMS)
            self._analysts.append(AnalystData(
                analyst_id=f"mock_{i:04d}",
                name=f"Analyst {i+1}",
                firm=firm,
            ))

    def _generate_ratings(self, tickers: list[str], start_date: date, end_date: date) -> None:
        """Generate mock ratings for given tickers over date range."""
        date_range = (end_date - start_date).days

        for analyst in self._analysts:
            # Each analyst covers a random subset of companies
            covered_tickers = random.sample(
                tickers,
                min(len(tickers), random.randint(10, 50))
            )

            num_ratings = random.randint(
                self.ratings_per_analyst // 2,
                self.ratings_per_analyst * 2
            )

            for _ in range(num_ratings):
                ticker = random.choice(covered_tickers)
                days_offset = random.randint(0, date_range)
                rating_date = start_date + timedelta(days=days_offset)

                # Weight toward hold/buy ratings (realistic distribution)
                rating = random.choices(
                    [RatingType.STRONG_BUY, RatingType.BUY, RatingType.HOLD,
                     RatingType.SELL, RatingType.STRONG_SELL],
                    weights=[5, 30, 40, 20, 5]
                )[0]

                # Generate a price target as a percentage of the base price
                # (in a real scenario, we'd use actual prices)
                base_price = random.uniform(20, 500)
                target_multiplier = {
                    RatingType.STRONG_BUY: random.uniform(1.15, 1.40),
                    RatingType.BUY: random.uniform(1.05, 1.20),
                    RatingType.HOLD: random.uniform(0.95, 1.05),
                    RatingType.SELL: random.uniform(0.80, 0.95),
                    RatingType.STRONG_SELL: random.uniform(0.60, 0.80),
                }
                price_target = base_price * target_multiplier[rating]

                self._ratings.append(RatingData(
                    analyst_id=analyst.analyst_id,
                    ticker=ticker,
                    date=rating_date,
                    rating=rating,
                    price_target=round(price_target, 2),
                ))

    def generate_data(
        self,
        tickers: list[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> None:
        """
        Generate mock data for the given tickers.
        
        Args:
            tickers: List of stock tickers to generate ratings for.
            start_date: Start of date range (default: 5 years ago).
            end_date: End of date range (default: today).
        """
        if self._generated:
            return

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=5*365)

        self._generate_analysts()
        self._generate_ratings(tickers, start_date, end_date)
        self._generated = True

    def get_analysts(self) -> list[AnalystData]:
        """Return mock analysts."""
        return self._analysts.copy()

    def get_ratings_for_company(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Filter ratings by company."""
        ratings = [r for r in self._ratings if r.ticker == ticker]

        if start_date:
            ratings = [r for r in ratings if r.date >= start_date]
        if end_date:
            ratings = [r for r in ratings if r.date <= end_date]

        return ratings

    def get_ratings_by_analyst(
        self,
        analyst_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Filter ratings by analyst."""
        ratings = [r for r in self._ratings if r.analyst_id == analyst_id]

        if start_date:
            ratings = [r for r in ratings if r.date >= start_date]
        if end_date:
            ratings = [r for r in ratings if r.date <= end_date]

        return ratings

    def get_all_ratings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Return all mock ratings."""
        ratings = self._ratings.copy()

        if start_date:
            ratings = [r for r in ratings if r.date >= start_date]
        if end_date:
            ratings = [r for r in ratings if r.date <= end_date]

        return ratings
