from contextlib import contextmanager
from datetime import datetime
from typing import Generator
from sqlmodel import Session
from .models import Job, JobStatus

@contextmanager
def track_job(session: Session, job_type: str) -> Generator[Job, None, None]:
    """Context manager to track an ingestion job."""
    job = Job(job_type=job_type, status=JobStatus.RUNNING)
    session.add(job)
    session.commit()
    session.refresh(job)
    
    try:
        yield job
        job.status = JobStatus.COMPLETED
        job.end_time = datetime.utcnow()
    except Exception as e:
        job.status = JobStatus.FAILED
        job.end_time = datetime.utcnow()
        job.details = str(e)
        raise e
    finally:
        session.add(job)
        session.commit()
