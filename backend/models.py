from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base


class Assessment(Base):
    """
    SQLAlchemy Model for storing location assessment records in SQLite.
    
    Fields:
    - id: Unique identifier
    - label: Optional human-readable name or label (e.g. "Primary Office")
    - address: Input location address or query string
    - latitude: Geocoded latitude coordinate
    - longitude: Geocoded longitude coordinate
    - elevation: Elevation in meters (can be unavailable/null)
    - temperature: Temperature value (can be unavailable/null)
    - elevation_score: Calculated elevation score (can be unavailable/null)
    - temperature_score: Calculated temperature score (can be unavailable/null)
    - total_score: Composite score without treating unavailable values as zero (can be null)
    - status: Indicates data state ('complete', 'partial', 'pending', 'failed')
    - created_at: Timestamp when record was created
    """
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    label = Column(String, nullable=True, index=True)
    address = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    elevation_score = Column(Float, nullable=True)
    temperature_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
