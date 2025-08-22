"""
Response models for the backend API.
"""
from typing import Optional
from pydantic import BaseModel, Field


# Error response model for API errors
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message with reason")
    status_code: int = Field(..., description="HTTP status code")
    reason: str = Field(..., description="Specific reason for the error")
    details: Optional[dict] = Field(None, description="Additional error details")


# Health check response
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status", example="healthy")
    timestamp: str = Field(..., description="Current timestamp", example="2023-12-07T10:30:00Z")
    version: str = Field(..., description="API version", example="1.0.0")
