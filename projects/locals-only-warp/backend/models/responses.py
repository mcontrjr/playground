"""
Response models for Google Places API.
Based on the official Google Maps Platform OpenAPI specification.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from .place import Place
from .base import PlacesSearchStatus


class PlacesNearbySearchResponse(BaseModel):
    """
    Response from Google Places Nearby Search API.
    Based on the official PlacesNearbySearchResponse schema.
    """
    html_attributions: List[str] = Field(
        ...,
        description="May contain a set of attributions about this listing which must be displayed to the user"
    )
    results: List[Place] = Field(
        ...,
        description="Contains an array of places"
    )
    status: PlacesSearchStatus = Field(
        ...,
        description="Contains the status of the request, and may contain debugging information"
    )
    error_message: Optional[str] = Field(
        None,
        description="When the service returns a status code other than OK, there may be an additional error_message field"
    )
    info_messages: Optional[List[str]] = Field(
        None,
        description="When the service returns additional information about the request specification"
    )
    next_page_token: Optional[str] = Field(
        None,
        description="Contains a token that can be used to return up to 20 additional results"
    )


class PlacesTextSearchResponse(BaseModel):
    """
    Response from Google Places Text Search API.
    Based on the official PlacesTextSearchResponse schema.
    """
    html_attributions: List[str] = Field(
        ...,
        description="May contain a set of attributions about this listing which must be displayed to the user"
    )
    results: List[Place] = Field(
        ...,
        description="Contains an array of places"
    )
    status: PlacesSearchStatus = Field(
        ...,
        description="Contains the status of the request, and may contain debugging information"
    )
    error_message: Optional[str] = Field(
        None,
        description="When the service returns a status code other than OK, there may be an additional error_message field"
    )
    info_messages: Optional[List[str]] = Field(
        None,
        description="When the service returns additional information about the request specification"
    )
    next_page_token: Optional[str] = Field(
        None,
        description="Contains a token that can be used to return up to 20 additional results"
    )


class PlacesFindPlaceFromTextResponse(BaseModel):
    """
    Response from Google Places Find Place From Text API.
    Based on the official PlacesFindPlaceFromTextResponse schema.
    """
    candidates: List[Place] = Field(
        ...,
        description="Contains an array of Place candidates"
    )
    status: PlacesSearchStatus = Field(
        ...,
        description="Contains the status of the request, and may contain debugging information"
    )
    error_message: Optional[str] = Field(
        None,
        description="When the service returns a status code other than OK, there may be an additional error_message field",
        example="Error while parsing 'fields' parameter: Unsupported field name 'invalid'. "
    )
    info_messages: Optional[List[str]] = Field(
        None,
        description="When the service returns additional information about the request specification"
    )


# Error response model for API errors
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[dict] = Field(None, description="Additional error details")


# Health check response
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status", example="healthy")
    timestamp: str = Field(..., description="Current timestamp", example="2023-12-07T10:30:00Z")
    version: str = Field(..., description="API version", example="1.0.0")
