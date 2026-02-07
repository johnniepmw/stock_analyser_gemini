"""
Database models using SQLModel.

These models represent the core entities stored in the database.
"""

from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel


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
    date: date = Field(index=True)
    open: float
    high: float
    low: float
    close: float
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
    date: date = Field(index=True)
    rating: str  # buy, sell, hold, strong_buy, strong_sell
    price_target: Optional[float] = None
    
    # For tracking accuracy
    was_accurate: Optional[bool] = None
    actual_return: Optional[float] = None  # Actual stock return after rating

    # Relationships
    analyst: Optional[Analyst] = Relationship(back_populates="ratings")
    company: Optional[Company] = Relationship(back_populates="ratings")
