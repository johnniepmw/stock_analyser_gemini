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

    # GitHub raw CSV URL for S&P 500 list
    SP500_CSV_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
    
    def get_sp500_companies(self) -> list[CompanyData]:
        """Fetch S&P 500 list with tiered fallback for reliability.
        
        Priority:
        1. GitHub datasets CSV (most reliable remote source)
        2. Local bundled CSV file
        3. Hardcoded fallback list
        """
        # Try GitHub CSV first
        companies = self._fetch_from_github_csv()
        if companies:
            return companies
            
        # Try local file
        companies = self._load_from_local_csv()
        if companies:
            return companies
            
        # Final fallback
        print("All sources failed, using hardcoded fallback")
        return self._get_hardcoded_fallback()

    def _fetch_from_github_csv(self) -> list[CompanyData] | None:
        """Fetch S&P 500 list from GitHub datasets repository."""
        try:
            response = requests.get(self.SP500_CSV_URL, timeout=10)
            response.raise_for_status()
            
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            companies = []
            for _, row in df.iterrows():
                companies.append(CompanyData(
                    ticker=str(row["Symbol"]).replace(".", "-"),
                    name=row["Security"],
                    sector=row.get("GICS Sector"),
                    industry=row.get("GICS Sub-Industry"),
                ))
            print(f"Loaded {len(companies)} companies from GitHub CSV")
            return companies
        except Exception as e:
            print(f"GitHub CSV fetch failed: {e}")
            return None

    def _load_from_local_csv(self) -> list[CompanyData] | None:
        """Load S&P 500 list from bundled local CSV file."""
        import os
        
        # Look for CSV in data directory relative to this module
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        csv_path = os.path.join(base_dir, "data", "sp500.csv")
        
        if not os.path.exists(csv_path):
            print(f"Local CSV not found at {csv_path}")
            return None
            
        try:
            df = pd.read_csv(csv_path)
            companies = []
            for _, row in df.iterrows():
                companies.append(CompanyData(
                    ticker=str(row["Symbol"]).replace(".", "-"),
                    name=row["Security"],
                    sector=row.get("GICS Sector"),
                    industry=row.get("GICS Sub-Industry"),
                ))
            print(f"Loaded {len(companies)} companies from local CSV")
            return companies
        except Exception as e:
            print(f"Local CSV load failed: {e}")
            return None

    def _get_hardcoded_fallback(self) -> list[CompanyData]:
        """Hardcoded fallback list of top S&P 500 companies."""
        fallback = [
            ("AAPL", "Apple Inc.", "Information Technology", "Technology Hardware"),
            ("MSFT", "Microsoft Corporation", "Information Technology", "Software"),
            ("GOOGL", "Alphabet Inc.", "Communication Services", "Interactive Media"),
            ("AMZN", "Amazon.com Inc.", "Consumer Discretionary", "Broadline Retail"),
            ("NVDA", "NVIDIA Corporation", "Information Technology", "Semiconductors"),
            ("META", "Meta Platforms Inc.", "Communication Services", "Interactive Media"),
            ("TSLA", "Tesla Inc.", "Consumer Discretionary", "Automobiles"),
            ("BRK-B", "Berkshire Hathaway Inc.", "Financials", "Multi-Sector Holdings"),
            ("UNH", "UnitedHealth Group Inc.", "Health Care", "Managed Health Care"),
            ("JNJ", "Johnson & Johnson", "Health Care", "Pharmaceuticals"),
            ("V", "Visa Inc.", "Financials", "Transaction Processing"),
            ("XOM", "Exxon Mobil Corporation", "Energy", "Oil & Gas"),
            ("JPM", "JPMorgan Chase & Co.", "Financials", "Diversified Banks"),
            ("WMT", "Walmart Inc.", "Consumer Staples", "Consumer Staples Merch."),
            ("MA", "Mastercard Incorporated", "Financials", "Transaction Processing"),
            ("PG", "Procter & Gamble Company", "Consumer Staples", "Household Products"),
            ("HD", "The Home Depot Inc.", "Consumer Discretionary", "Home Improvement"),
            ("CVX", "Chevron Corporation", "Energy", "Oil & Gas"),
            ("MRK", "Merck & Co. Inc.", "Health Care", "Pharmaceuticals"),
            ("LLY", "Eli Lilly and Company", "Health Care", "Pharmaceuticals"),
        ]
        return [
            CompanyData(ticker=t, name=n, sector=s, industry=i)
            for t, n, s, i in fallback
        ]

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
