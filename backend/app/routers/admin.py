from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime

from app.database import get_session
from app.models import DataSource, DataSourceCategory, Job, JobStatus
from app.ingestion import IngestionService
from app.providers import YFinanceProvider, FMPProvider

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/data-sources", response_model=dict[str, List[DataSource]])
def get_data_sources(session: Session = Depends(get_session)):
    """Get all data sources grouped by category."""
    sources = session.exec(select(DataSource)).all()
    
    # helper to ensure default sources exist if DB is empty
    if not sources:
        defaults = [
            DataSource(name="YFinance", category=DataSourceCategory.STOCK_PRICES, is_active=True),
            DataSource(name="FMP", category=DataSourceCategory.STOCK_PRICES, is_active=False),
            DataSource(name="YFinance", category=DataSourceCategory.COMPANY_INFO, is_active=True),
            DataSource(name="FMP", category=DataSourceCategory.COMPANY_INFO, is_active=False),
            DataSource(name="YFinance", category=DataSourceCategory.ANALYST_RATINGS, is_active=False), 
            DataSource(name="FMP", category=DataSourceCategory.ANALYST_RATINGS, is_active=True), # FMP better for ratings
            DataSource(name="Mock", category=DataSourceCategory.ANALYST_RATINGS, is_active=False),
        ]
        for ds in defaults:
            session.add(ds)
        session.commit()
        sources = session.exec(select(DataSource)).all()

    grouped = {}
    for cat in DataSourceCategory:
        grouped[cat.value] = [s for s in sources if s.category == cat]
        
    return grouped

@router.post("/data-sources/{source_id}/activate")
def activate_data_source(source_id: int, session: Session = Depends(get_session)):
    """Set a data source as active for its category."""
    source = session.get(DataSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Deactivate others in same category
    stmt = select(DataSource).where(DataSource.category == source.category)
    others = session.exec(stmt).all()
    for s in others:
        s.is_active = (s.id == source_id)
        session.add(s)
    
    session.commit()
    return {"message": f"Activated {source.name} for {source.category}"}

@router.get("/jobs", response_model=List[Job])
def get_jobs(limit: int = 50, session: Session = Depends(get_session)):
    """Get recent background jobs."""
    stmt = select(Job).order_by(Job.start_time.desc()).limit(limit)
    return session.exec(stmt).all()

def run_ingestion_job(job_type: str, session: Session):
    """Background task to run ingestion."""
    # This is a simplified DI - in real app use dependency injection properly
    # For now, we instantiate providers based on active settings
    
    # Re-create session for background task
    from app.database import engine
    from sqlmodel import Session as SMSession
    
    with SMSession(engine) as bg_session:
        # Check active providers
        stock_source = bg_session.exec(select(DataSource).where(DataSource.category == DataSourceCategory.STOCK_PRICES, DataSource.is_active == True)).first()
        rating_source = bg_session.exec(select(DataSource).where(DataSource.category == DataSourceCategory.ANALYST_RATINGS, DataSource.is_active == True)).first()
        
        stock_provider = FMPProvider() if stock_source and stock_source.name == "FMP" else YFinanceProvider()
        
        if rating_source and rating_source.name == "FMP":
            rating_provider = FMPProvider()
        elif rating_source and rating_source.name == "YFinance":
            rating_provider = YFinanceProvider()
        else:
            from app.providers.mock_provider import MockProvider
            rating_provider = MockProvider()

        service = IngestionService(stock_provider, rating_provider)
        
        try:
            if job_type == "ingest_prices":
                # Get tickers first
                from app.models import Company
                tickers = [c.ticker for c in bg_session.exec(select(Company)).all()]
                if not tickers:
                    # If nocompanies, ingest sp500 first
                    service.ingest_companies(bg_session)
                    tickers = [c.ticker for c in bg_session.exec(select(Company)).all()]
                
                service.ingest_price_history(bg_session, tickers)
                service.ingest_current_prices(bg_session, tickers)
                
            elif job_type == "ingest_companies":
                service.ingest_companies(bg_session)
                
            elif job_type == "ingest_ratings":
                from app.models import Company
                tickers = [c.ticker for c in bg_session.exec(select(Company)).all()]
                service.ingest_ratings(bg_session, tickers)
                service.ingest_analysts(bg_session)
                
            elif job_type == "ingest_benchmark":
                service.ingest_benchmark_prices(bg_session)
                
            elif job_type == "ingest_current_prices":
                from app.models import Company
                tickers = [c.ticker for c in bg_session.exec(select(Company)).all()]
                service.ingest_current_prices(bg_session, tickers)

        except Exception as e:
            print(f"Job failed: {e}")

@router.post("/jobs/trigger")
def trigger_job(
    job_type: str, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Trigger a new ingestion job."""
    valid_jobs = ["ingest_prices", "ingest_companies", "ingest_ratings", "ingest_benchmark", "ingest_current_prices"]
    if job_type not in valid_jobs:
        raise HTTPException(status_code=400, detail="Invalid job type")
        
    background_tasks.add_task(run_ingestion_job, job_type, session)
    return {"message": f"Job {job_type} triggered"}
