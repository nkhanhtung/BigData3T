from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg://neondb_owner:npg_X3MpLju8nzxi@ep-lingering-pond-a1q4x3j5-pooler.ap-southeast-1.aws.neon.tech:5432/neondb"

engine = create_engine(DATABASE_URL, echo=True)  # echo=True để debug SQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
