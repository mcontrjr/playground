"""
Recommendation models for the simplified Places API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """
    Simplified recommendation model extracted from Google Places data.
    Contains only the most useful information for local recommendations.
    """
    # Core identification
    name: str = Field(..., description="Name of the place", example="Joe's Coffee Shop")
    place_id: str = Field(..., description="Google Place ID", example="ChIJN1t_tDeuEmsRUsoyG83frY4")
    
    # Location
    address: Optional[str] = Field(None, description="Formatted address", example="123 Main St, Anytown, CA 12345")
    latitude: float = Field(..., description="Latitude coordinate", example=37.7749)
    longitude: float = Field(..., description="Longitude coordinate", example=-122.4194)
    
    # Key details
    rating: Optional[float] = Field(
        None, 
        description="Average rating from 1.0 to 5.0", 
        example=4.2,
        ge=1.0, 
        le=5.0
    )
    review_count: Optional[int] = Field(None, description="Total number of reviews", example=156)
    price_level: Optional[int] = Field(
        None,
        description="Price level: 0=Free, 1=Inexpensive, 2=Moderate, 3=Expensive, 4=Very Expensive",
        ge=0,
        le=4,
        example=2
    )
    
    # Category and status
    category: Optional[str] = Field(None, description="Primary category/type", example="restaurant")
    is_open: Optional[bool] = Field(None, description="Whether the place is currently open")
    
    # Contact (optional)
    phone: Optional[str] = Field(None, description="Phone number", example="(555) 123-4567")
    website: Optional[str] = Field(None, description="Website URL", example="https://joescoffee.com")


class RecommendationsRequest(BaseModel):
    """Request model for getting local recommendations."""
    zip_code: str = Field(
        ...,
        description="US zip code to get recommendations for",
        min_length=5,
        max_length=10,
        example="94043"
    )
    radius: Optional[int] = Field(
        1500,
        description="Search radius in meters (max 50000)",
        ge=100,
        le=50000,
        example=1500
    )
    category: Optional[str] = Field(
        None,
        description="Filter by place type (e.g., restaurant, cafe, park)",
        example="restaurant"
    )
    keyword: Optional[str] = Field(
        None,
        description="Keyword to match against place names and types",
        example="coffee"
    )
    limit: Optional[int] = Field(
        20,
        description="Maximum number of recommendations to return",
        ge=1,
        le=60,
        example=20
    )
    price_max: Optional[int] = Field(
        None,
        description="Maximum price level (0-4)",
        ge=0,
        le=4,
        example=3
    )
    open_now: Optional[bool] = Field(
        None,
        description="Only return places that are currently open",
        example=True
    )


class ZipRecommendationsRequest(BaseModel):
    """Minimal request model for zip code-based recommendations."""
    zip_code: str = Field(
        ...,
        description="US zip code to search around",
        min_length=5,
        max_length=10,
        example="94043"
    )
    radius: Optional[int] = Field(
        1500,
        description="Search radius in meters (default: 1500, max: 50000)",
        ge=100,
        le=50000,
        example=1500
    )


class TextRecommendationsRequest(BaseModel):
    """Minimal request model for text-based recommendations."""
    query: str = Field(
        ...,
        description="Natural language search query",
        min_length=1,
        max_length=200,
        example="coffee shops in downtown Seattle"
    )


class RecommendationsResponse(BaseModel):
    """Response model for local recommendations."""
    zip_code: Optional[str] = Field(None, description="The searched zip code (if applicable)")
    location: str = Field(..., description="Formatted location info", example="San Jose, CA")
    latitude: Optional[float] = Field(None, description="Search center latitude")
    longitude: Optional[float] = Field(None, description="Search center longitude")
    radius: Optional[int] = Field(None, description="Search radius used in meters")
    total_found: int = Field(..., description="Total number of recommendations found")
    recommendations: List[Recommendation] = Field(..., description="List of local recommendations")
    message: str = Field(..., description="Success message")
