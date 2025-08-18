"""
Base types and shared models for Google Places API.
Based on the official Google Maps Platform OpenAPI specification.
"""
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class BusinessStatus(str, Enum):
    """Business operational status."""
    OPERATIONAL = "OPERATIONAL"
    CLOSED_TEMPORARILY = "CLOSED_TEMPORARILY"
    CLOSED_PERMANENTLY = "CLOSED_PERMANENTLY"


class PlacesSearchStatus(str, Enum):
    """Status codes returned by Places API service."""
    OK = "OK"
    ZERO_RESULTS = "ZERO_RESULTS"
    INVALID_REQUEST = "INVALID_REQUEST"
    OVER_QUERY_LIMIT = "OVER_QUERY_LIMIT"
    REQUEST_DENIED = "REQUEST_DENIED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class LatLngLiteral(BaseModel):
    """A latitude/longitude pair."""
    lat: float = Field(..., description="Latitude in degrees")
    lng: float = Field(..., description="Longitude in degrees")


class Bounds(BaseModel):
    """A rectangle in geographical coordinates."""
    northeast: LatLngLiteral = Field(..., description="The northeast corner of these bounds")
    southwest: LatLngLiteral = Field(..., description="The southwest corner of these bounds")


class Geometry(BaseModel):
    """An object describing the location."""
    location: LatLngLiteral = Field(..., description="The location of the place")
    viewport: Bounds = Field(..., description="The viewport for displaying the place")


class PlusCode(BaseModel):
    """An encoded location reference using Plus Codes."""
    compound_code: Optional[str] = Field(None, description="A 6 character or longer local code with an explicit location")
    global_code: Optional[str] = Field(None, description="A 4 character area code and 6 character or longer local code")


class PlacePhoto(BaseModel):
    """A place photo."""
    height: int = Field(..., description="The maximum height of the image")
    width: int = Field(..., description="The maximum width of the image")
    html_attributions: List[str] = Field(..., description="Contains any required attributions")
    photo_reference: str = Field(..., description="A string used to identify the photo when performing a Photo request")


class PlaceOpeningHours(BaseModel):
    """Opening hours for a place."""
    open_now: Optional[bool] = Field(None, description="Whether the place is currently open")
    periods: Optional[List[dict]] = Field(None, description="Opening periods covering seven days")
    weekday_text: Optional[List[str]] = Field(None, description="An array of strings describing the opening hours")


class AddressComponent(BaseModel):
    """A single address component."""
    long_name: str = Field(..., description="The full text description or name of the address component")
    short_name: str = Field(..., description="An abbreviated textual name for the address component")
    types: List[str] = Field(..., description="An array indicating the type of the address component")


class PlaceEditorialSummary(BaseModel):
    """Editorial summary of a place."""
    overview: str = Field(..., description="A medium-length textual summary of the place")
    language: Optional[str] = Field(None, description="The language of the overview")


class PlaceReview(BaseModel):
    """A review of a place."""
    author_name: str = Field(..., description="The name of the user who submitted the review")
    author_url: Optional[str] = Field(None, description="The URL to the user's profile")
    language: Optional[str] = Field(None, description="An IETF language code indicating the language in which this review is written")
    profile_photo_url: Optional[str] = Field(None, description="The URL to the user's profile photo")
    rating: int = Field(..., description="The user's overall rating for this place", ge=1, le=5)
    relative_time_description: str = Field(..., description="A string of formatted recent time")
    text: str = Field(..., description="The user's review")
    time: int = Field(..., description="The time that the review was submitted, measured in the number of seconds since January 1, 1970 UTC")
