from sqlmodel import create_engine, text
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS job"))
    conn.commit()
    print("Job table dropped")
