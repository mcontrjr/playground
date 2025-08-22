"""
Request models for the New Places API.
Based on the official Google Maps Platform New Places API specification.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class RankPreference(str, Enum):
    """Ranking preference for nearby search in New Places API."""
    POPULARITY = "POPULARITY"
    DISTANCE = "DISTANCE"


class LanguageCode(str, Enum):
    """Common language codes for requests."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"


class Circle(BaseModel):
    """Defines a circle area for location restriction."""
    center: dict = Field(..., description="Center point with latitude and longitude")
    radius: float = Field(..., description="Radius in meters", ge=0.0, le=50000.0)


class Rectangle(BaseModel):
    """Defines a rectangular area for location restriction."""
    low: dict = Field(..., description="Low point (southwest corner)")
    high: dict = Field(..., description="High point (northeast corner)")


class LocationRestriction(BaseModel):
    """Location restriction for search requests."""
    circle: Optional[Circle] = Field(None, description="Circular area restriction")
    rectangle: Optional[Rectangle] = Field(None, description="Rectangular area restriction")


class LocationBias(BaseModel):
    """Location bias for search requests."""
    circle: Optional[Circle] = Field(None, description="Circular area bias")
    rectangle: Optional[Rectangle] = Field(None, description="Rectangular area bias")


# New Places API Request Models

class PlaceDetailsNewRequest(BaseModel):
    """Request model for Place Details (New) API."""
    fields: List[str] = Field(
        ...,
        description="List of fields to return. Use '*' for all fields",
        example=[
            "id", "displayName", "formattedAddress", "location", 
            "rating", "userRatingCount", "priceLevel", "primaryType",
            "photos", "currentOpeningHours", "paymentOptions"
        ]
    )
    language_code: Optional[str] = Field(
        None,
        description="Language code for localized results",
        example="en"
    )
    region_code: Optional[str] = Field(
        None,
        description="Region code for result bias",
        example="US"
    )
    session_token: Optional[str] = Field(
        None,
        description="Session token for billing grouping"
    )


class NearbySearchNewRequest(BaseModel):
    """Request model for Nearby Search (New) API."""
    fields: List[str] = Field(
        ...,
        description="List of fields to return. Use '*' for all fields",
        example=[
            "places.id", "places.displayName", "places.formattedAddress", 
            "places.location", "places.rating", "places.userRatingCount",
            "places.priceLevel", "places.primaryType", "places.photos"
        ]
    )
    location_restriction: LocationRestriction = Field(
        ...,
        description="Area to search within"
    )
    included_types: Optional[List[str]] = Field(
        None,
        description="Place types to include in results",
        example=["restaurant", "cafe", "bakery"]
    )
    excluded_types: Optional[List[str]] = Field(
        None,
        description="Place types to exclude from results"
    )
    included_primary_types: Optional[List[str]] = Field(
        None,
        description="Primary types to include"
    )
    excluded_primary_types: Optional[List[str]] = Field(
        None,
        description="Primary types to exclude"
    )
    max_result_count: Optional[int] = Field(
        None,
        description="Maximum number of results to return",
        ge=1,
        le=20,
        example=10
    )
    language_code: Optional[str] = Field(
        None,
        description="Language code for localized results",
        example="en"
    )
    region_code: Optional[str] = Field(
        None,
        description="Region code for result bias",
        example="US"
    )
    rank_preference: Optional[RankPreference] = Field(
        None,
        description="Ranking preference for results"
    )


class TextSearchNewRequest(BaseModel):
    """Request model for Text Search (New) API."""
    text_query: str = Field(
        ...,
        description="Text query to search for",
        example="Spicy Vegetarian Food in Sydney, Australia"
    )
    fields: List[str] = Field(
        ...,
        description="List of fields to return. Use '*' for all fields",
        example=[
            "places.id", "places.displayName", "places.formattedAddress", 
            "places.location", "places.rating", "places.userRatingCount",
            "places.priceLevel", "places.primaryType", "places.photos"
        ]
    )
    included_type: Optional[str] = Field(
        None,
        description="Place type to include",
        example="restaurant"
    )
    open_now: Optional[bool] = Field(
        None,
        description="Only return places that are currently open"
    )
    min_rating: Optional[float] = Field(
        None,
        description="Minimum rating to include",
        ge=1.0,
        le=5.0
    )
    max_result_count: Optional[int] = Field(
        None,
        description="Maximum number of results to return",
        ge=1,
        le=20,
        example=10
    )
    price_levels: Optional[List[str]] = Field(
        None,
        description="Price levels to include",
        example=["PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE"]
    )
    strict_type_filtering: Optional[bool] = Field(
        None,
        description="Enable strict type filtering"
    )
    location_bias: Optional[LocationBias] = Field(
        None,
        description="Location bias for results"
    )
    location_restriction: Optional[LocationRestriction] = Field(
        None,
        description="Location restriction for results"
    )
    language_code: Optional[str] = Field(
        None,
        description="Language code for localized results",
        example="en"
    )
    region_code: Optional[str] = Field(
        None,
        description="Region code for result bias",
        example="US"
    )


class PlacePhotoNewRequest(BaseModel):
    """Request model for Place Photo (New) API."""
    max_width_px: Optional[int] = Field(
        None,
        description="Maximum width of the image in pixels",
        ge=1,
        le=4800,
        example=400
    )
    max_height_px: Optional[int] = Field(
        None,
        description="Maximum height of the image in pixels",
        ge=1,
        le=4800,
        example=400
    )
    skip_http_redirect: Optional[bool] = Field(
        False,
        description="Skip HTTP redirect and return raw image data"
    )

    @model_validator(mode='after')
    def validate_dimensions(self):
        """Validate that at least one dimension is provided."""
        if self.max_width_px is None and self.max_height_px is None:
            raise ValueError("At least one of max_width_px or max_height_px must be specified")
        return self
