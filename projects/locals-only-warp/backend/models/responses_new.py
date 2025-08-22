"""
Response models for the New Places API.
Based on the official Google Maps Platform New Places API specification.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from .place import Place


class PlaceDetailsNewResponse(BaseModel):
    """Response from Place Details (New) API."""
    # The place details are returned directly, not in a wrapper
    # This will be the Place object itself


class NearbySearchNewResponse(BaseModel):
    """Response from Nearby Search (New) API."""
    places: List[Place] = Field(
        ...,
        description="Array of places found in the nearby search"
    )


class TextSearchNewResponse(BaseModel):
    """Response from Text Search (New) API."""
    places: List[Place] = Field(
        ...,
        description="Array of places found in the text search"
    )
    # Optional context token for pagination (if supported)
    context_token: Optional[str] = Field(
        None,
        description="Context token for pagination"
    )


class PlacePhotoNewResponse(BaseModel):
    """Response from Place Photo (New) API."""
    # The photo API returns the image directly as binary data
    # This model is mainly for documenting the response structure
    content_type: str = Field(..., description="MIME type of the image")
    content_length: Optional[int] = Field(None, description="Size of the image in bytes")
    # The actual image data would be in the HTTP response body
