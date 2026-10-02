from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite Database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./locations.db"

# connect_args={"check_same_thread": False} is required for SQLite in multithreaded environments like FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize SQLite database tables."""
    Base.metadata.create_all(bind=engine)
