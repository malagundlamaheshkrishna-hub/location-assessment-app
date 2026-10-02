from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AssessmentBase(BaseModel):
    """Base schema with common assessment fields."""
    address: str = Field(..., json_schema_extra={"example": "1600 Amphitheatre Pkwy, Mountain View, CA"})
    label: Optional[str] = Field(None, json_schema_extra={"example": "Google HQ"})
    latitude: Optional[float] = Field(None, json_schema_extra={"example": 37.4220})
    longitude: Optional[float] = Field(None, json_schema_extra={"example": -122.0841})


class AssessmentCreate(AssessmentBase):
    """Schema used when requesting a new assessment."""
    pass


class AssessmentResponse(AssessmentBase):
    """
    Schema returned to client representing an assessment record.
    Supports nullable fields for unavailable data without defaulting to zero.
    """
    id: int
    elevation: Optional[float] = None
    temperature: Optional[float] = None
    elevation_score: Optional[float] = None
    temperature_score: Optional[float] = None
    total_score: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Schema for API health status check."""
    status: str
    app_name: str
    version: str
