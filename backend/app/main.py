"""
FastAPI application entry point.

Provides REST API endpoints for the Stock Analyser frontend.
"""

from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select, func

from .database import create_db_and_tables, get_session
from .models import Analyst, AnalystRating, BenchmarkPrice, Company, StockPrice


# Pydantic response models
class AnalystSummary(BaseModel):
    analyst_id: str
    name: str
    firm: str
    confidence_score: Optional[float]
    total_ratings: int


class AnalystDetail(AnalystSummary):
    accurate_ratings: int
    ratings: list["RatingSummary"]


class RatingSummary(BaseModel):
    ticker: str
    company_name: Optional[str]
    date: date
    rating: str
    price_target: Optional[float]
    was_accurate: Optional[bool]
    actual_return: Optional[float]


class CompanySummary(BaseModel):
    ticker: str
    name: str
    sector: Optional[str]
    current_price: Optional[float]
    target_price: Optional[float]
    investment_score: Optional[float]


class CompanyDetail(CompanySummary):
    industry: Optional[str]
    market_cap: Optional[float]
    analyst_ratings: list["CompanyRating"]


class CompanyRating(BaseModel):
    analyst_id: str
    analyst_name: str
    firm: str
    confidence_score: Optional[float]
    date: date
    rating: str
    price_target: Optional[float]


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


# Create FastAPI app
app = FastAPI(
    title="Stock Analyser API",
    description="API for analyzing stocks based on analyst ratings",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


# --- Analyst Endpoints ---

@app.get("/api/analysts", response_model=PaginatedResponse)
def list_analysts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("confidence_score", regex="^(confidence_score|name|firm|total_ratings)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    session: Session = Depends(get_session)
):
    """List all analysts with pagination and sorting."""
    # Build query
    stmt = select(Analyst)

    # Apply sorting
    sort_col = getattr(Analyst, sort_by)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_col.desc().nulls_last())
    else:
        stmt = stmt.order_by(sort_col.asc().nulls_last())

    # Get total count
    count_stmt = select(func.count()).select_from(Analyst)
    total = session.exec(count_stmt).one()

    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    analysts = session.exec(stmt).all()

    items = [
        AnalystSummary(
            analyst_id=a.analyst_id,
            name=a.name,
            firm=a.firm,
            confidence_score=a.confidence_score,
            total_ratings=a.total_ratings,
        )
        for a in analysts
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.get("/api/analysts/{analyst_id}", response_model=AnalystDetail)
def get_analyst(analyst_id: str, session: Session = Depends(get_session)):
    """Get detailed information about an analyst."""
    analyst = session.get(Analyst, analyst_id)
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found")

    # Get ratings with company names
    stmt = select(AnalystRating, Company.name).join(
        Company, AnalystRating.ticker == Company.ticker, isouter=True
    ).where(
        AnalystRating.analyst_id == analyst_id
    ).order_by(AnalystRating.rating_date.desc())

    results = session.exec(stmt).all()

    ratings = [
        RatingSummary(
            ticker=r[0].ticker,
            company_name=r[1],
            date=r[0].rating_date,
            rating=r[0].rating,
            price_target=r[0].price_target,
            was_accurate=r[0].was_accurate,
            actual_return=r[0].actual_return,
        )
        for r in results
    ]

    return AnalystDetail(
        analyst_id=analyst.analyst_id,
        name=analyst.name,
        firm=analyst.firm,
        confidence_score=analyst.confidence_score,
        total_ratings=analyst.total_ratings,
        accurate_ratings=analyst.accurate_ratings,
        ratings=ratings,
    )


# --- Company Endpoints ---

@app.get("/api/companies", response_model=PaginatedResponse)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("investment_score", regex="^(investment_score|name|current_price|target_price|sector)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    sector: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """List all companies with pagination and sorting."""
    stmt = select(Company)

    # Apply sector filter
    if sector:
        stmt = stmt.where(Company.sector == sector)

    # Apply sorting
    sort_col = getattr(Company, sort_by)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_col.desc().nulls_last())
    else:
        stmt = stmt.order_by(sort_col.asc().nulls_last())

    # Get total count
    count_stmt = select(func.count()).select_from(Company)
    if sector:
        count_stmt = count_stmt.where(Company.sector == sector)
    total = session.exec(count_stmt).one()

    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    companies = session.exec(stmt).all()

    items = [
        CompanySummary(
            ticker=c.ticker,
            name=c.name,
            sector=c.sector,
            current_price=c.current_price,
            target_price=c.target_price,
            investment_score=c.investment_score,
        )
        for c in companies
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.get("/api/companies/{ticker}", response_model=CompanyDetail)
def get_company(ticker: str, session: Session = Depends(get_session)):
    """Get detailed information about a company."""
    company = session.get(Company, ticker.upper())
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get ratings with analyst info
    stmt = select(AnalystRating, Analyst).join(
        Analyst, AnalystRating.analyst_id == Analyst.analyst_id, isouter=True
    ).where(
        AnalystRating.ticker == ticker.upper()
    ).order_by(AnalystRating.rating_date.desc())

    results = session.exec(stmt).all()

    analyst_ratings = [
        CompanyRating(
            analyst_id=r[0].analyst_id,
            analyst_name=r[1].name if r[1] else "Unknown",
            firm=r[1].firm if r[1] else "Unknown",
            confidence_score=r[1].confidence_score if r[1] else None,
            date=r[0].rating_date,
            rating=r[0].rating,
            price_target=r[0].price_target,
        )
        for r in results
    ]

    return CompanyDetail(
        ticker=company.ticker,
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        market_cap=company.market_cap,
        current_price=company.current_price,
        target_price=company.target_price,
        investment_score=company.investment_score,
        analyst_ratings=analyst_ratings,
    )


@app.get("/api/companies/{ticker}/prices")
def get_company_prices(
    ticker: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """Get historical prices for a company."""
    company = session.get(Company, ticker.upper())
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    stmt = select(StockPrice).where(StockPrice.ticker == ticker.upper())

    if start_date:
        stmt = stmt.where(StockPrice.price_date >= start_date)
    if end_date:
        stmt = stmt.where(StockPrice.price_date <= end_date)

    stmt = stmt.order_by(StockPrice.price_date)
    prices = session.exec(stmt).all()

    return [
        {
            "date": p.price_date.isoformat(),
            "open": p.open_price,
            "high": p.high_price,
            "low": p.low_price,
            "close": p.close_price,
            "volume": p.volume,
        }
        for p in prices
    ]


@app.get("/api/sectors")
def get_sectors(session: Session = Depends(get_session)):
    """Get list of all sectors."""
    stmt = select(Company.sector).distinct().where(Company.sector.is_not(None))
    sectors = session.exec(stmt).all()
    return sorted([s for s in sectors if s])


@app.get("/api/benchmark/{symbol}/prices")
def get_benchmark_prices(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """Get historical prices for a benchmark index."""
    stmt = select(BenchmarkPrice).where(BenchmarkPrice.symbol == symbol.upper())

    if start_date:
        stmt = stmt.where(BenchmarkPrice.price_date >= start_date)
    if end_date:
        stmt = stmt.where(BenchmarkPrice.price_date <= end_date)

    stmt = stmt.order_by(BenchmarkPrice.price_date)
    prices = session.exec(stmt).all()

    if not prices:
        raise HTTPException(status_code=404, detail=f"No benchmark data found for {symbol}")

    return [
        {
            "date": p.price_date.isoformat(),
            "close": p.close_price,
        }
        for p in prices
    ]


# Health check
@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
