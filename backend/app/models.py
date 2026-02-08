"""
Database models using SQLModel.

These models represent the core entities stored in the database.
"""

from datetime import date, datetime
from typing import Optional
from enum import Enum
from sqlmodel import Field, Relationship, SQLModel


class DataSourceCategory(str, Enum):
    """Category of data source."""
    STOCK_PRICES = "stock_prices"
    COMPANY_INFO = "company_info"
    ANALYST_RATINGS = "analyst_ratings"


class DataSource(SQLModel, table=True):
    """Configuration for a data source."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # e.g. "YFinance", "FMP"
    category: DataSourceCategory = Field(index=True)
    is_active: bool = Field(default=False)
    last_updated: Optional[datetime] = None


class JobStatus(str, Enum):
    """Status of a background job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(SQLModel, table=True):
    """Record of a data ingestion job."""
    id: Optional[int] = Field(default=None, primary_key=True)
    job_type: str  # e.g. "ingest_prices"
    status: JobStatus = Field(default=JobStatus.PENDING)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    details: Optional[str] = None  # JSON or text logs


class Company(SQLModel, table=True):
    """S&P 500 company."""
    ticker: str = Field(primary_key=True)
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    investment_score: Optional[float] = None  # Calculated weighted score
    target_price: Optional[float] = None  # Weighted average target price

    # Relationships
    prices: list["StockPrice"] = Relationship(back_populates="company")
    ratings: list["AnalystRating"] = Relationship(back_populates="company")


class StockPrice(SQLModel, table=True):
    """Historical daily stock price."""
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(foreign_key="company.ticker", index=True)
    price_date: date = Field(index=True)
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    adj_close: float
    volume: int

    # Relationship
    company: Optional[Company] = Relationship(back_populates="prices")


class Analyst(SQLModel, table=True):
    """Financial analyst who provides ratings."""
    analyst_id: str = Field(primary_key=True)
    name: str
    firm: str
    confidence_score: Optional[float] = None  # 0-100 calculated score
    total_ratings: int = 0
    accurate_ratings: int = 0

    # Relationships
    ratings: list["AnalystRating"] = Relationship(back_populates="analyst")


class AnalystRating(SQLModel, table=True):
    """Individual analyst rating for a company."""
    id: Optional[int] = Field(default=None, primary_key=True)
    analyst_id: str = Field(foreign_key="analyst.analyst_id", index=True)
    ticker: str = Field(foreign_key="company.ticker", index=True)
    rating_date: date = Field(index=True)
    rating: str  # buy, sell, hold, strong_buy, strong_sell
    price_target: Optional[float] = None
    
    # For tracking accuracy
    was_accurate: Optional[bool] = None
    actual_return: Optional[float] = None  # Actual stock return after rating

    # Relationships
    analyst: Optional[Analyst] = Relationship(back_populates="ratings")
    company: Optional[Company] = Relationship(back_populates="ratings")


class BenchmarkPrice(SQLModel, table=True):
    """Historical daily price for a benchmark index (e.g., S&P 500)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)  # e.g., "SPY" or "^GSPC"
    price_date: date = Field(index=True)
    close_price: float
