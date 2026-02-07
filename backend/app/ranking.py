"""
Ranking algorithms for analysts and companies.

Calculates:
1. Analyst confidence scores based on historical accuracy
2. Company investment scores weighted by analyst confidence
"""

from datetime import date, timedelta
from sqlmodel import Session, select

from .database import get_direct_session
from .models import Analyst, AnalystRating, Company, StockPrice


class RankingService:
    """Service for calculating analyst and company rankings."""

    def __init__(
        self,
        evaluation_horizon_days: int = 90,
        min_ratings_for_confidence: int = 5
    ):
        """
        Initialize ranking service.
        
        Args:
            evaluation_horizon_days: Days after rating to measure performance.
            min_ratings_for_confidence: Minimum ratings needed to generate confidence score.
        """
        self.evaluation_horizon = evaluation_horizon_days
        self.min_ratings = min_ratings_for_confidence

    def _get_price_at_date(
        self,
        session: Session,
        ticker: str,
        target_date: date,
        tolerance_days: int = 5
    ) -> float | None:
        """Get closest price to target date within tolerance."""
        stmt = select(StockPrice).where(
            StockPrice.ticker == ticker,
            StockPrice.date >= target_date - timedelta(days=tolerance_days),
            StockPrice.date <= target_date + timedelta(days=tolerance_days),
        ).order_by(
            # Order by distance from target date
            (StockPrice.date - target_date).abs()
        ).limit(1)

        price = session.exec(stmt).first()
        return price.adj_close if price else None

    def _was_rating_accurate(
        self,
        rating: str,
        return_pct: float,
        threshold: float = 0.05
    ) -> bool:
        """
        Determine if a rating was accurate based on actual return.
        
        Args:
            rating: The analyst rating (buy, sell, hold, etc.)
            return_pct: Actual return over evaluation horizon.
            threshold: Return threshold for considering a prediction accurate.
            
        Returns:
            True if the rating direction matched the actual performance.
        """
        bullish = rating in ("strong_buy", "buy")
        bearish = rating in ("strong_sell", "sell")
        neutral = rating == "hold"

        if bullish:
            return return_pct > threshold
        elif bearish:
            return return_pct < -threshold
        else:  # hold
            return abs(return_pct) <= threshold * 2

    def calculate_analyst_confidence(self, session: Session) -> int:
        """
        Calculate confidence scores for all analysts.
        
        Evaluates each historical rating against actual stock performance
        and updates analyst confidence scores.
        
        Returns:
            Number of analysts updated.
        """
        analysts = session.exec(select(Analyst)).all()
        cutoff_date = date.today() - timedelta(days=self.evaluation_horizon)
        updated = 0

        for analyst in analysts:
            # Get ratings old enough to evaluate
            stmt = select(AnalystRating).where(
                AnalystRating.analyst_id == analyst.analyst_id,
                AnalystRating.date <= cutoff_date
            )
            ratings = session.exec(stmt).all()

            if len(ratings) < self.min_ratings:
                continue

            total = 0
            accurate = 0

            for rating in ratings:
                rating_date = rating.date
                eval_date = rating_date + timedelta(days=self.evaluation_horizon)

                # Get prices
                start_price = self._get_price_at_date(session, rating.ticker, rating_date)
                end_price = self._get_price_at_date(session, rating.ticker, eval_date)

                if not start_price or not end_price or start_price == 0:
                    continue

                return_pct = (end_price - start_price) / start_price
                is_accurate = self._was_rating_accurate(rating.rating, return_pct)

                # Update rating record
                rating.actual_return = return_pct
                rating.was_accurate = is_accurate

                total += 1
                if is_accurate:
                    accurate += 1

            # Calculate confidence score (0-100)
            if total >= self.min_ratings:
                analyst.total_ratings = total
                analyst.accurate_ratings = accurate
                analyst.confidence_score = (accurate / total) * 100
                updated += 1

        session.commit()
        return updated

    def calculate_company_scores(self, session: Session) -> int:
        """
        Calculate investment scores for all companies.
        
        Aggregates current analyst ratings weighted by analyst confidence.
        
        Returns:
            Number of companies updated.
        """
        companies = session.exec(select(Company)).all()
        updated = 0

        # Define rating values for weighted average
        rating_values = {
            "strong_buy": 2.0,
            "buy": 1.0,
            "hold": 0.0,
            "sell": -1.0,
            "strong_sell": -2.0,
        }

        for company in companies:
            # Get recent ratings (last 6 months)
            recent_date = date.today() - timedelta(days=180)
            stmt = select(AnalystRating).where(
                AnalystRating.ticker == company.ticker,
                AnalystRating.date >= recent_date
            )
            ratings = session.exec(stmt).all()

            if not ratings:
                continue

            weighted_sum = 0.0
            weight_total = 0.0
            target_weighted_sum = 0.0
            target_weight_total = 0.0

            for rating in ratings:
                # Get analyst confidence
                analyst = session.get(Analyst, rating.analyst_id)
                confidence = analyst.confidence_score if analyst and analyst.confidence_score else 50.0

                # Weight by confidence (normalized 0-1)
                weight = confidence / 100.0

                # Add to weighted rating sum
                rating_value = rating_values.get(rating.rating, 0.0)
                weighted_sum += rating_value * weight
                weight_total += weight

                # Add to target price calculation if available
                if rating.price_target:
                    target_weighted_sum += rating.price_target * weight
                    target_weight_total += weight

            # Calculate investment score (normalize to 0-100)
            if weight_total > 0:
                avg_rating = weighted_sum / weight_total  # Range: -2 to 2
                # Normalize to 0-100: (value + 2) / 4 * 100
                company.investment_score = ((avg_rating + 2) / 4) * 100
                updated += 1

            # Calculate weighted average target price
            if target_weight_total > 0:
                company.target_price = target_weighted_sum / target_weight_total

        session.commit()
        return updated

    def run_full_ranking(self) -> dict:
        """Run complete ranking pipeline.
        
        Returns:
            Dictionary with ranking statistics.
        """
        session = get_direct_session()
        stats = {}

        print("Calculating analyst confidence scores...")
        stats["analysts_ranked"] = self.calculate_analyst_confidence(session)
        print(f"  -> {stats['analysts_ranked']} analysts scored")

        print("Calculating company investment scores...")
        stats["companies_ranked"] = self.calculate_company_scores(session)
        print(f"  -> {stats['companies_ranked']} companies scored")

        session.close()
        return stats
