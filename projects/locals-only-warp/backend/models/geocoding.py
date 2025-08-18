"""
Geocoding models based on Google Maps Geocoding API schema.
Based on the official Google Maps Platform OpenAPI specification.
"""
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from .base import (
    LatLngLiteral,
    Bounds,
    AddressComponent,
    PlusCode,
)


class GeocodingStatus(str, Enum):
    """Status codes returned by Geocoding API service."""
    OK = "OK"
    INVALID_REQUEST = "INVALID_REQUEST"
    OVER_DAILY_LIMIT = "OVER_DAILY_LIMIT"
    OVER_QUERY_LIMIT = "OVER_QUERY_LIMIT"
    REQUEST_DENIED = "REQUEST_DENIED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    ZERO_RESULTS = "ZERO_RESULTS"


class LocationType(str, Enum):
    """Location type precision indicators."""
    ROOFTOP = "ROOFTOP"
    RANGE_INTERPOLATED = "RANGE_INTERPOLATED"
    GEOMETRIC_CENTER = "GEOMETRIC_CENTER"
    APPROXIMATE = "APPROXIMATE"


class GeocodingGeometry(BaseModel):
    """An object describing the location from geocoding."""
    location: LatLngLiteral = Field(..., description="The location coordinates")
    location_type: LocationType = Field(..., description="The precision of the location")
    viewport: Bounds = Field(..., description="The viewport for displaying the location")
    bounds: Optional[Bounds] = Field(None, description="The bounding box for the location")


class GeocodingResult(BaseModel):
    """A single geocoding result."""
    address_components: List[AddressComponent] = Field(
        ...,
        description="An array containing the separate components applicable to this address"
    )
    formatted_address: str = Field(
        ...,
        description="The human-readable address of this location"
    )
    geometry: GeocodingGeometry = Field(..., description="The location information")
    place_id: str = Field(..., description="A unique identifier for the place")
    plus_code: Optional[PlusCode] = Field(None, description="Plus code for the location")
    types: List[str] = Field(
        ...,
        description="Array indicating the type of the returned result"
    )
    postcode_localities: Optional[List[str]] = Field(
        None,
        description="An array denoting all the localities contained in a postal code"
    )
    partial_match: Optional[bool] = Field(
        None,
        description="Indicates that the geocoder did not return an exact match"
    )


class GeocodingResponse(BaseModel):
    """
    Response from Google Geocoding API.
    Based on the official GeocodingResponse schema.
    """
    status: GeocodingStatus = Field(..., description="Status of the geocoding request")
    results: List[GeocodingResult] = Field(..., description="Array of geocoding results")
    plus_code: Optional[PlusCode] = Field(None, description="Plus code for the location")
    error_message: Optional[str] = Field(
        None,
        description="A short description of the error"
    )


# Request models
class GeocodeRequest(BaseModel):
    """Request for geocoding an address."""
    address: Optional[str] = Field(
        None,
        description="The street address that you want to geocode"
    )
    components: Optional[List[str]] = Field(
        None,
        description="A components filter with pipe-separated elements"
    )
    bounds: Optional[str] = Field(
        None,
        description="The bounding box of the viewport within which to bias geocode results"
    )
    language: Optional[str] = Field(
        None,
        description="Language code for results (IETF language tag)",
        example="en"
    )
    region: Optional[str] = Field(
        None,
        description="Country code for biasing results (ccTLD format)",
        example="us"
    )


class ZipCodeRequest(BaseModel):
    """Request for zip code geocoding."""
    zip_code: str = Field(
        ...,
        description="US zip code to geocode",
        min_length=5,
        max_length=10,
        example="94043"
    )
    country: Optional[str] = Field(
        "US",
        description="Country code (defaults to US)",
        example="US"
    )


class ZipCodeInfo(BaseModel):
    """Simplified zip code information response."""
    zip_code: str = Field(..., description="The zip code")
    city: Optional[str] = Field(None, description="Primary city name")
    state: Optional[str] = Field(None, description="State abbreviation")
    state_full: Optional[str] = Field(None, description="Full state name")
    country: Optional[str] = Field(None, description="Country name")
    country_code: Optional[str] = Field(None, description="Country code")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    location_type: LocationType = Field(..., description="Precision of the location")
    formatted_address: str = Field(..., description="Formatted address string")
    place_id: str = Field(..., description="Google Place ID")


class ZipCodeResponse(BaseModel):
    """Response for zip code lookup."""
    status: str = Field(..., description="Request status")
    # Flattened fields for successful responses (when status == 'ok')
    zip_code: Optional[str] = Field(None, description="The zip code")
    city: Optional[str] = Field(None, description="Primary city name")
    state: Optional[str] = Field(None, description="State abbreviation")
    state_full: Optional[str] = Field(None, description="Full state name")
    country: Optional[str] = Field(None, description="Country name")
    country_code: Optional[str] = Field(None, description="Country code")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    location_type: Optional[LocationType] = Field(None, description="Precision of the location")
    formatted_address: Optional[str] = Field(None, description="Formatted address string")
    place_id: Optional[str] = Field(None, description="Google Place ID")
    # Error field
    error_message: Optional[str] = Field(None, description="Error message if request failed")
