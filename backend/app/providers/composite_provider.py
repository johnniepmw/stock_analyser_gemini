"""
Composite provider that combines multiple data sources.

Allows mixing real data (e.g., prices from yfinance) with supplemental data
(e.g., mock ratings) or combining multiple real providers.
"""

from datetime import date
from typing import Optional

from .base import (
    AnalystData,
    BaseRatingsProvider,
    BaseStockProvider,
    CompanyData,
    PriceData,
    RatingData,
)


class CompositeProvider(BaseStockProvider, BaseRatingsProvider):
    """
    Combines multiple providers with priority ordering.
    
    Stock data is fetched from the first available stock provider.
    Ratings can be aggregated from multiple ratings providers.
    """

    def __init__(
        self,
        stock_providers: list[BaseStockProvider],
        ratings_providers: list[BaseRatingsProvider],
        aggregate_ratings: bool = True
    ):
        """
        Initialize composite provider.
        
        Args:
            stock_providers: Ordered list of stock providers (first success wins).
            ratings_providers: List of ratings providers.
            aggregate_ratings: If True, combine ratings from all providers.
                             If False, use first provider with data.
        """
        self.stock_providers = stock_providers
        self.ratings_providers = ratings_providers
        self.aggregate_ratings = aggregate_ratings

    # Stock provider methods - use first successful provider

    def get_sp500_companies(self) -> list[CompanyData]:
        """Get S&P 500 companies from first available provider."""
        for provider in self.stock_providers:
            try:
                companies = provider.get_sp500_companies()
                if companies:
                    return companies
            except Exception as e:
                print(f"Provider {type(provider).__name__} failed: {e}")
                continue
        return []

    def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> list[PriceData]:
        """Get price history from first available provider."""
        for provider in self.stock_providers:
            try:
                prices = provider.get_price_history(ticker, start_date, end_date)
                if prices:
                    return prices
            except Exception as e:
                print(f"Provider {type(provider).__name__} failed for {ticker}: {e}")
                continue
        return []

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price from first available provider."""
        for provider in self.stock_providers:
            try:
                price = provider.get_current_price(ticker)
                if price is not None:
                    return price
            except Exception:
                continue
        return None

    # Ratings provider methods - aggregate or use first

    def get_analysts(self) -> list[AnalystData]:
        """Get analysts, optionally aggregating from all providers."""
        if self.aggregate_ratings:
            all_analysts = {}
            for provider in self.ratings_providers:
                for analyst in provider.get_analysts():
                    # Use analyst_id as key to avoid duplicates
                    all_analysts[analyst.analyst_id] = analyst
            return list(all_analysts.values())
        else:
            for provider in self.ratings_providers:
                analysts = provider.get_analysts()
                if analysts:
                    return analysts
            return []

    def get_ratings_for_company(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Get company ratings, optionally aggregating from all providers."""
        if self.aggregate_ratings:
            all_ratings = []
            for provider in self.ratings_providers:
                all_ratings.extend(
                    provider.get_ratings_for_company(ticker, start_date, end_date)
                )
            return all_ratings
        else:
            for provider in self.ratings_providers:
                ratings = provider.get_ratings_for_company(ticker, start_date, end_date)
                if ratings:
                    return ratings
            return []

    def get_ratings_by_analyst(
        self,
        analyst_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Get analyst ratings, optionally aggregating from all providers."""
        if self.aggregate_ratings:
            all_ratings = []
            for provider in self.ratings_providers:
                all_ratings.extend(
                    provider.get_ratings_by_analyst(analyst_id, start_date, end_date)
                )
            return all_ratings
        else:
            for provider in self.ratings_providers:
                ratings = provider.get_ratings_by_analyst(analyst_id, start_date, end_date)
                if ratings:
                    return ratings
            return []

    def get_all_ratings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Get all ratings, optionally aggregating from all providers."""
        if self.aggregate_ratings:
            all_ratings = []
            for provider in self.ratings_providers:
                all_ratings.extend(
                    provider.get_all_ratings(start_date, end_date)
                )
            return all_ratings
        else:
            for provider in self.ratings_providers:
                ratings = provider.get_all_ratings(start_date, end_date)
                if ratings:
                    return ratings
            return []
