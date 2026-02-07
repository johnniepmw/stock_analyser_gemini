"""
Data ingestion service.

Orchestrates data providers to fetch and store data in the database.
"""

from datetime import date, timedelta
from sqlmodel import Session, select

from .database import get_direct_session, create_db_and_tables
from .models import Analyst, AnalystRating, BenchmarkPrice, Company, StockPrice
from .providers.base import BaseRatingsProvider, BaseStockProvider


class IngestionService:
    """Service for ingesting data from providers into the database."""

    def __init__(
        self,
        stock_provider: BaseStockProvider,
        ratings_provider: BaseRatingsProvider
    ):
        self.stock_provider = stock_provider
        self.ratings_provider = ratings_provider

    def ingest_companies(self, session: Session) -> int:
        """Ingest S&P 500 companies.
        
        Returns:
            Number of companies ingested.
        """
        companies = self.stock_provider.get_sp500_companies()
        count = 0

        for company_data in companies:
            # Check if exists
            existing = session.get(Company, company_data.ticker)
            if existing:
                existing.name = company_data.name
                existing.sector = company_data.sector
                existing.industry = company_data.industry
                existing.market_cap = company_data.market_cap
            else:
                company = Company(
                    ticker=company_data.ticker,
                    name=company_data.name,
                    sector=company_data.sector,
                    industry=company_data.industry,
                    market_cap=company_data.market_cap,
                )
                session.add(company)
                count += 1

        session.commit()
        return count

    def ingest_price_history(
        self,
        session: Session,
        tickers: list[str],
        years: int = 5
    ) -> int:
        """Ingest historical prices for given tickers.
        
        Args:
            session: Database session.
            tickers: List of stock tickers.
            years: Number of years of history to fetch.
            
        Returns:
            Number of price records ingested.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=years * 365)
        count = 0

        for ticker in tickers:
            # Check for most recent price in DB
            stmt = select(StockPrice).where(
                StockPrice.ticker == ticker
            ).order_by(StockPrice.price_date.desc()).limit(1)
            latest = session.exec(stmt).first()

            fetch_start = start_date
            if latest:
                fetch_start = latest.price_date + timedelta(days=1)
                if fetch_start >= end_date:
                    continue  # Already up to date

            prices = self.stock_provider.get_price_history(
                ticker, fetch_start, end_date
            )

            for price_data in prices:
                price = StockPrice(
                    ticker=price_data.ticker,
                    price_date=price_data.date,
                    open_price=price_data.open,
                    high_price=price_data.high,
                    low_price=price_data.low,
                    close_price=price_data.close,
                    adj_close=price_data.adj_close,
                    volume=price_data.volume,
                )
                session.add(price)
                count += 1

            # Commit periodically to avoid memory issues
            if count % 1000 == 0:
                session.commit()

        session.commit()
        return count

    def ingest_current_prices(
        self,
        session: Session,
        tickers: list[str]
    ) -> int:
        """Update current prices for companies.
        
        Returns:
            Number of prices updated.
        """
        count = 0
        for ticker in tickers:
            price = self.stock_provider.get_current_price(ticker)
            if price:
                company = session.get(Company, ticker)
                if company:
                    company.current_price = price
                    count += 1

        session.commit()
        return count

    def ingest_benchmark_prices(
        self,
        session: Session,
        symbol: str = "SPY",
        years: int = 5
    ) -> int:
        """Ingest historical prices for a benchmark index.
        
        Args:
            session: Database session.
            symbol: Benchmark symbol (e.g., SPY for S&P 500 ETF).
            years: Number of years of history to fetch.
            
        Returns:
            Number of price records ingested.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=years * 365)
        count = 0

        # Check for most recent price in DB
        stmt = select(BenchmarkPrice).where(
            BenchmarkPrice.symbol == symbol.upper()
        ).order_by(BenchmarkPrice.price_date.desc()).limit(1)
        latest = session.exec(stmt).first()

        fetch_start = start_date
        if latest:
            fetch_start = latest.price_date + timedelta(days=1)
            if fetch_start >= end_date:
                return 0  # Already up to date

        prices = self.stock_provider.get_price_history(
            symbol, fetch_start, end_date
        )

        for price_data in prices:
            benchmark = BenchmarkPrice(
                symbol=symbol.upper(),
                price_date=price_data.date,
                close_price=price_data.close,
            )
            session.add(benchmark)
            count += 1

            # Commit periodically
            if count % 1000 == 0:
                session.commit()

        session.commit()
        return count

    def ingest_analysts(self, session: Session) -> int:
        """Ingest analysts from ratings provider.
        
        Returns:
            Number of analysts ingested.
        """
        analysts = self.ratings_provider.get_analysts()
        count = 0

        for analyst_data in analysts:
            existing = session.get(Analyst, analyst_data.analyst_id)
            if existing:
                existing.name = analyst_data.name
                existing.firm = analyst_data.firm
            else:
                analyst = Analyst(
                    analyst_id=analyst_data.analyst_id,
                    name=analyst_data.name,
                    firm=analyst_data.firm,
                )
                session.add(analyst)
                count += 1

        session.commit()
        return count

    def ingest_ratings(
        self,
        session: Session,
        tickers: list[str]
    ) -> int:
        """Ingest analyst ratings for given tickers.
        
        Returns:
            Number of ratings ingested.
        """
        count = 0

        for ticker in tickers:
            ratings = self.ratings_provider.get_ratings_for_company(ticker)

            for rating_data in ratings:
                # Check for duplicate
                stmt = select(AnalystRating).where(
                    AnalystRating.analyst_id == rating_data.analyst_id,
                    AnalystRating.ticker == rating_data.ticker,
                    AnalystRating.rating_date == rating_data.date,
                )
                existing = session.exec(stmt).first()
                if existing:
                    continue

                # Ensure analyst exists
                analyst = session.get(Analyst, rating_data.analyst_id)
                if not analyst:
                    analyst = Analyst(
                        analyst_id=rating_data.analyst_id,
                        name=f"Unknown ({rating_data.analyst_id})",
                        firm="Unknown",
                    )
                    session.add(analyst)

                rating = AnalystRating(
                    analyst_id=rating_data.analyst_id,
                    ticker=rating_data.ticker,
                    rating_date=rating_data.date,
                    rating=rating_data.rating.value,
                    price_target=rating_data.price_target,
                )
                session.add(rating)
                count += 1

            # Commit periodically
            if count % 500 == 0:
                session.commit()

        session.commit()
        return count

    def run_full_ingestion(
        self,
        price_years: int = 5,
        limit_companies: int | None = None
    ) -> dict:
        """Run complete data ingestion pipeline.
        
        Args:
            price_years: Years of price history to fetch.
            limit_companies: Limit to first N companies (for testing).
            
        Returns:
            Dictionary with ingestion statistics.
        """
        create_db_and_tables()
        session = get_direct_session()
        
        stats = {}

        # 1. Ingest companies
        print("Ingesting S&P 500 companies...")
        stats["companies"] = self.ingest_companies(session)
        print(f"  -> {stats['companies']} new companies")

        # Get ticker list
        tickers = [c.ticker for c in session.exec(select(Company)).all()]
        if limit_companies:
            tickers = tickers[:limit_companies]

        # 2. Ingest price history
        print(f"Ingesting {price_years} years of price history...")
        stats["prices"] = self.ingest_price_history(session, tickers, price_years)
        print(f"  -> {stats['prices']} price records")

        # 3. Update current prices
        print("Updating current prices...")
        stats["current_prices"] = self.ingest_current_prices(session, tickers)
        print(f"  -> {stats['current_prices']} prices updated")

        # 4. Ingest ratings (this also creates analysts)
        print("Ingesting analyst ratings...")
        stats["ratings"] = self.ingest_ratings(session, tickers)
        print(f"  -> {stats['ratings']} ratings")

        # 5. Ingest analysts (from cache)
        print("Ingesting analysts...")
        stats["analysts"] = self.ingest_analysts(session)
        print(f"  -> {stats['analysts']} analysts")

        session.close()
        return stats
