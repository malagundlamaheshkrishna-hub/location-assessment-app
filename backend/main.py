from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import Assessment
from .schemas import (
    AssessmentCreate,
    AssessmentResponse,
    HealthResponse,
)
from .services.geocoder import geocode_address
from .services.elevation import get_elevation
from .services.weather import get_weather
from .scoring import compute_assessment_scoring

# Initialize SQLite database tables on startup
init_db()

app = FastAPI(
    title="Location Assessment Tool API",
    description="Backend API for assessing locations using Geocoding, USGS Elevation, and Open-Meteo Weather.",
    version="1.0.0",
)

# Configure CORS so React frontend can communicate with FastAPI
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint providing service status."""
    return {
        "message": "Welcome to Location Assessment Tool API",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "app_name": "Location Assessment Tool Backend",
        "version": "1.0.0"
    }


@app.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED, tags=["Assessments"])
@app.post("/api/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_assessment(assessment_in: AssessmentCreate, db: Session = Depends(get_db)):
    """
    Complete assessment workflow:
    1. Geocode the address via US Census Geocoder.
    2. If geocoding fails, save record with status 'failed' / 'unavailable'.
    3. If geocoding succeeds, fetch USGS elevation and Open-Meteo weather in parallel/sequence.
    4. Apply scoring rules from scoring.py (never convert missing values to 0).
    5. Save complete assessment to SQLite and return.
    """
    address = assessment_in.address
    label = assessment_in.label

    # Step 1 & 2: Call Census Geocoder
    geo_result = await geocode_address(address)

    # Step 3: If geocoding fails, save assessment with unavailable status
    if not geo_result.get("available"):
        db_assessment = Assessment(
            label=label,
            address=address,
            latitude=None,
            longitude=None,
            elevation=None,
            temperature=None,
            elevation_score=None,
            temperature_score=None,
            total_score=None,
            status="failed"
        )
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)
        return db_assessment

    # Step 4: Geocoding succeeded -> extract coordinates
    latitude = geo_result["latitude"]
    longitude = geo_result["longitude"]

    # Step 5: Call USGS Elevation service
    elev_result = await get_elevation(latitude, longitude)
    elevation_val = elev_result.get("elevation") if elev_result.get("available") else None

    # Step 6: Call Open-Meteo Weather service
    weather_result = await get_weather(latitude, longitude)
    temperature_val = weather_result.get("temperature") if weather_result.get("available") else None

    # Step 7: Apply scoring rules (does NOT treat unavailable values as 0)
    scores = compute_assessment_scoring(elevation=elevation_val, temperature=temperature_val)

    # Step 8: Save the complete result to SQLite
    db_assessment = Assessment(
        label=label,
        address=address,
        latitude=latitude,
        longitude=longitude,
        elevation=elevation_val,
        temperature=temperature_val,
        elevation_score=scores["elevation_score"],
        temperature_score=scores["temperature_score"],
        total_score=scores["total_score"],
        status=scores["status"]
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)

    # Step 9: Return saved assessment
    return db_assessment


@app.get("/assessments", response_model=List[AssessmentResponse], tags=["Assessments"])
@app.get("/api/assessments", response_model=List[AssessmentResponse], include_in_schema=False)
def list_assessments(db: Session = Depends(get_db)):
    """Retrieve all saved location assessments from SQLite."""
    assessments = db.query(Assessment).order_by(Assessment.id.desc()).all()
    return assessments


@app.get("/assessments/{assessment_id}", response_model=AssessmentResponse, tags=["Assessments"])
@app.get("/api/assessments/{assessment_id}", response_model=AssessmentResponse, include_in_schema=False)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Retrieve a single assessment by ID with complete details."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with id {assessment_id} not found"
        )
    return assessment
