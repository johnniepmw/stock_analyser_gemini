"""
Abstract base classes for data providers.

This module defines the interfaces that all data providers must implement,
enabling easy swapping between different data sources (yfinance, Alpha Vantage, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class RatingType(str, Enum):
    """Analyst rating categories."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class CompanyData:
    """Standardized company information from any provider."""
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None


@dataclass
class PriceData:
    """Standardized price data from any provider."""
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


@dataclass
class AnalystData:
    """Standardized analyst information."""
    analyst_id: str
    name: str
    firm: str


@dataclass
class RatingData:
    """Standardized analyst rating from any provider."""
    analyst_id: str
    ticker: str
    date: date
    rating: RatingType
    price_target: Optional[float] = None
    previous_rating: Optional[RatingType] = None


class BaseStockProvider(ABC):
    """Abstract base class for stock/company data providers."""

    @abstractmethod
    def get_sp500_companies(self) -> list[CompanyData]:
        """Fetch list of S&P 500 companies.
        
        Returns:
            List of CompanyData objects for all S&P 500 constituents.
        """
        pass

    @abstractmethod
    def get_price_history(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> list[PriceData]:
        """Fetch historical price data for a ticker.
        
        Args:
            ticker: Stock symbol.
            start_date: Start of date range.
            end_date: End of date range.
            
        Returns:
            List of PriceData objects for the date range.
        """
        pass

    @abstractmethod
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Fetch current/latest price for a ticker.
        
        Args:
            ticker: Stock symbol.
            
        Returns:
            Current price or None if unavailable.
        """
        pass


class BaseRatingsProvider(ABC):
    """Abstract base class for analyst ratings data providers."""

    @abstractmethod
    def get_analysts(self) -> list[AnalystData]:
        """Fetch list of all analysts.
        
        Returns:
            List of AnalystData objects.
        """
        pass

    @abstractmethod
    def get_ratings_for_company(
        self,
        ticker: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Fetch analyst ratings for a specific company.
        
        Args:
            ticker: Stock symbol.
            start_date: Optional start of date range.
            end_date: Optional end of date range.
            
        Returns:
            List of RatingData objects.
        """
        pass

    @abstractmethod
    def get_ratings_by_analyst(
        self,
        analyst_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Fetch all ratings by a specific analyst.
        
        Args:
            analyst_id: Unique analyst identifier.
            start_date: Optional start of date range.
            end_date: Optional end of date range.
            
        Returns:
            List of RatingData objects.
        """
        pass

    @abstractmethod
    def get_all_ratings(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[RatingData]:
        """Fetch all available ratings.
        
        Args:
            start_date: Optional start of date range.
            end_date: Optional end of date range.
            
        Returns:
            List of RatingData objects.
        """
        pass
