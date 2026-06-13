from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

url = settings.database_url
connect_args = {}
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+pg8000://", 1)
    connect_args["ssl_context"] = True
elif url.startswith("sqlite://"):
    connect_args["check_same_thread"] = False

engine = create_engine(url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
