#!/usr/bin/env python3
"""
CLI script to run data ingestion and ranking.

Usage:
    python -m app.cli ingest [--limit N] [--years N]
    python -m app.cli rank
    python -m app.cli benchmark [--symbol SPY] [--years N]
    python -m app.cli all [--limit N] [--years N]
"""

import argparse
import sys

from .database import create_db_and_tables
from .ingestion import IngestionService
from .ranking import RankingService
from .providers import YFinanceProvider, MockProvider, CompositeProvider, FMPProvider


def create_default_provider(use_mock_ratings: bool = True, use_fmp: bool = False):
    """Create default provider configuration."""
    stock_providers = [YFinanceProvider()]
    ratings_providers = [YFinanceProvider()]

    if use_fmp:
        fmp = FMPProvider()
        if fmp.api_key:
            print("Using Financial Modeling Prep (FMP) for analyst ratings")
            ratings_providers.append(fmp)
        else:
            print("Warning: --fmp flag used but FMP_API_KEY not found. Skipping FMP provider.")

    if use_mock_ratings:
        # Use mock for additional coverage
        mock_provider = MockProvider(num_analysts=50, ratings_per_analyst=100)
        ratings_providers.append(mock_provider)
        return CompositeProvider(
            stock_providers=stock_providers,
            ratings_providers=ratings_providers,
            aggregate_ratings=True
        ), mock_provider
    else:
        return CompositeProvider(
            stock_providers=stock_providers,
            ratings_providers=ratings_providers,
            aggregate_ratings=True  # Aggregate if multiple (e.g. YFinance + FMP)
        ), None


def cmd_ingest(args):
    """Run data ingestion."""
    print("=" * 50)
    print("Stock Analyser - Data Ingestion")
    print("=" * 50)

    create_db_and_tables()

    use_fmp = getattr(args, 'use_fmp', False)
    provider, mock_provider = create_default_provider(
        use_mock_ratings=args.mock_ratings,
        use_fmp=use_fmp
    )

    # If using mock ratings, we need to pre-generate them for the tickers
    # First, get the company list
    yf = YFinanceProvider()
    companies = yf.get_sp500_companies()
    tickers = [c.ticker for c in companies]
    if args.limit:
        tickers = tickers[:args.limit]

    if mock_provider:
        print(f"Generating mock ratings for {len(tickers)} companies...")
        mock_provider.generate_data(tickers)

    # Also fetch yfinance ratings
    if hasattr(provider, 'stock_providers'):
        for sp in provider.stock_providers:
            if isinstance(sp, YFinanceProvider):
                print("Fetching real analyst ratings from yfinance...")
                sp.fetch_all_ratings_for_companies(tickers[:20])  # Limit to avoid rate limits

    service = IngestionService(
        stock_provider=provider,
        ratings_provider=provider
    )

    stats = service.run_full_ingestion(
        price_years=args.years,
        limit_companies=args.limit
    )

    print("\n" + "=" * 50)
    print("Ingestion Complete!")
    print(f"  Companies: {stats.get('companies', 0)}")
    print(f"  Prices: {stats.get('prices', 0)}")
    print(f"  Ratings: {stats.get('ratings', 0)}")
    print(f"  Analysts: {stats.get('analysts', 0)}")
    print("=" * 50)


def cmd_rank(args):
    """Run ranking calculations."""
    print("=" * 50)
    print("Stock Analyser - Ranking Calculation")
    print("=" * 50)

    service = RankingService(
        evaluation_horizon_days=args.horizon,
        min_ratings_for_confidence=args.min_ratings
    )

    stats = service.run_full_ranking()

    print("\n" + "=" * 50)
    print("Ranking Complete!")
    print(f"  Analysts Ranked: {stats.get('analysts_ranked', 0)}")
    print(f"  Companies Ranked: {stats.get('companies_ranked', 0)}")
    print("=" * 50)


def cmd_benchmark(args):
    """Ingest benchmark data."""
    print("=" * 50)
    print("Stock Analyser - Benchmark Ingestion")
    print("=" * 50)

    from .database import get_direct_session
    create_db_and_tables()

    yf_provider = YFinanceProvider()
    mock_provider = MockProvider(num_analysts=1, ratings_per_analyst=1)
    
    composite = CompositeProvider(
        stock_providers=[yf_provider],
        ratings_providers=[mock_provider],
        aggregate_ratings=False
    )

    service = IngestionService(
        stock_provider=composite,
        ratings_provider=composite
    )

    session = get_direct_session()
    count = service.ingest_benchmark_prices(
        session,
        symbol=args.symbol,
        years=args.years
    )
    session.close()

    print(f"\nIngested {count} benchmark prices for {args.symbol}")
    print("=" * 50)


def cmd_all(args):
    """Run full pipeline: ingest + rank."""
    # Ensure use_fmp is set if not present (handled by argparse default typically but good to be safe)
    if not hasattr(args, 'use_fmp'):
        args.use_fmp = False
    cmd_ingest(args)
    cmd_rank(args)


def main():
    parser = argparse.ArgumentParser(
        description="Stock Analyser CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Run data ingestion")
    ingest_parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit to first N companies (for testing)"
    )
    ingest_parser.add_argument(
        "--years", type=int, default=5,
        help="Years of price history to fetch"
    )
    ingest_parser.add_argument(
        "--mock-ratings", action="store_true", default=True,
        help="Include mock ratings (default: True)"
    )
    ingest_parser.add_argument(
        "--no-mock-ratings", action="store_false", dest="mock_ratings",
        help="Only use real ratings from yfinance"
    )
    ingest_parser.add_argument(
        "--fmp", action="store_true", dest="use_fmp",
        help="Use Financial Modeling Prep API (requires FMP_API_KEY)"
    )

    # Rank command
    rank_parser = subparsers.add_parser("rank", help="Run ranking calculations")
    rank_parser.add_argument(
        "--horizon", type=int, default=90,
        help="Days after rating to evaluate performance"
    )
    rank_parser.add_argument(
        "--min-ratings", type=int, default=5,
        help="Minimum ratings for confidence score"
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Ingest benchmark data")
    benchmark_parser.add_argument(
        "--symbol", type=str, default="SPY",
        help="Benchmark symbol to fetch (default: SPY)"
    )
    benchmark_parser.add_argument(
        "--years", type=int, default=5,
        help="Years of history to fetch"
    )

    # All command
    all_parser = subparsers.add_parser("all", help="Run full pipeline")
    all_parser.add_argument("--limit", type=int, default=None)
    all_parser.add_argument("--years", type=int, default=5)
    all_parser.add_argument("--mock-ratings", action="store_true", default=True)
    all_parser.add_argument("--no-mock-ratings", action="store_false", dest="mock_ratings")
    all_parser.add_argument("--fmp", action="store_true", dest="use_fmp")
    all_parser.add_argument("--horizon", type=int, default=90)
    all_parser.add_argument("--min-ratings", type=int, default=5)

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "rank":
        cmd_rank(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "all":
        cmd_all(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
