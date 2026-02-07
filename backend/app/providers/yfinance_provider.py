"""
YFinance implementation of data providers.

Uses the yfinance library to fetch stock prices and available analyst data.
"""

import hashlib
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

from .base import (
    AnalystData,
    BaseRatingsProvider,
    BaseStockProvider,
    CompanyData,
    PriceData,
    RatingData,
    RatingType,
)


class YFinanceProvider(BaseStockProvider, BaseRatingsProvider):
    """Data provider using yfinance library."""

    def __init__(self):
        self._analysts_cache: dict[str, AnalystData] = {}
        self._ratings_cache: list[RatingData] = []

    def get_sp500_companies(self) -> list[CompanyData]:
        """Fetch S&P 500 list from Wikipedia."""
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]

        companies = []
        for _, row in df.iterrows():
            companies.append(CompanyData(
                ticker=row["Symbol"].replace(".", "-"),  # Yahoo uses - instead of .
                name=row["Security"],
                sector=row.get("GICS Sector"),
                industry=row.get("GICS Sub-Industry"),
            ))
        return companies

    def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> list[PriceData]:
        """Fetch historical prices from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(
                start=start_date.isoformat(),
                end=end_date.isoformat()
            )

            prices = []
            for idx, row in df.iterrows():
                prices.append(PriceData(
                    ticker=ticker,
                    date=idx.date(),
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    adj_close=row["Close"],  # yfinance returns adjusted by default
                    volume=int(row["Volume"]),
                ))
            return prices
        except Exception as e:
            print(f"Error fetching prices for {ticker}: {e}")
            return []

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Fetch latest price from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get("regularMarketPrice") or info.get("currentPrice")
        except Exception:
            return None

    def _generate_analyst_id(self, firm: str) -> str:
        """Generate a consistent analyst ID from firm name."""
        return hashlib.md5(firm.encode()).hexdigest()[:8]

    def _map_rating(self, rating_str: str) -> Optional[RatingType]:
        """Map yfinance rating strings to RatingType enum."""
        rating_lower = rating_str.lower()
        mappings = {
            "strong buy": RatingType.STRONG_BUY,
            "buy": RatingType.BUY,
            "outperform": RatingType.BUY,
            "overweight": RatingType.BUY,
            "hold": RatingType.HOLD,
            "neutral": RatingType.HOLD,
            "equal-weight": RatingType.HOLD,
            "sector perform": RatingType.HOLD,
            "market perform": RatingType.HOLD,
            "sell": RatingType.SELL,
            "underperform": RatingType.SELL,
            "underweight": RatingType.SELL,
            "strong sell": RatingType.STRONG_SELL,
        }
        for key, value in mappings.items():
            if key in rating_lower:
                return value
        return RatingType.HOLD  # Default to hold if unknown

    def _fetch_recommendations(self, ticker: str) -> list[RatingData]:
        """Fetch recommendations for a ticker and cache analysts."""
        try:
            stock = yf.Ticker(ticker)
            recs = stock.recommendations
            if recs is None or recs.empty:
                return []

            ratings = []
            for idx, row in recs.iterrows():
                firm = row.get("Firm", "Unknown")
                analyst_id = self._generate_analyst_id(firm)

                # Cache analyst
                if analyst_id not in self._analysts_cache:
                    self._analysts_cache[analyst_id] = AnalystData(
                        analyst_id=analyst_id,
                        name=f"Analyst at {firm}",
                        firm=firm,
                    )

                to_grade = row.get("To Grade", row.get("toGrade", ""))
                if not to_grade:
                    continue

                rating_type = self._map_rating(to_grade)
                if rating_type is None:
                    continue

                # Handle date
                if isinstance(idx, pd.Timestamp):
                    rating_date = idx.date()
                else:
                    rating_date = date.today()

                ratings.append(RatingData(
                    analyst_id=analyst_id,
                    ticker=ticker,
                    date=rating_date,
                    rating=rating_type,
                    price_target=None,  # yfinance doesn't provide this in recommendations
                ))

            return ratings
        except Exception as e:
            print(f"Error fetching recommendations for {ticker}: {e}")
            return []

    def get_analysts(self) -> list[AnalystData]:
        """Return cached analysts (must fetch ratings first to populate)."""
        return list(self._analysts_cache.values())

    def get_ratings_for_company(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Fetch ratings for a company."""
        ratings = self._fetch_recommendations(ticker)

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
    ) -> list[RatingData]:
        """Return all cached ratings."""
        ratings = self._ratings_cache.copy()

        if start_date:
            ratings = [r for r in ratings if r.date >= start_date]
        if end_date:
            ratings = [r for r in ratings if r.date <= end_date]

        return ratings

    def fetch_all_ratings_for_companies(self, tickers: list[str]) -> None:
        """Batch fetch ratings for multiple companies and cache them."""
        for ticker in tickers:
            ratings = self._fetch_recommendations(ticker)
            self._ratings_cache.extend(ratings)
