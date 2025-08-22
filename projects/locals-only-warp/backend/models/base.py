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


class RankBy(str, Enum):
    """Ranking preference for nearby search."""
    PROMINENCE = "prominence"
    DISTANCE = "distance"


class PriceLevel(str, Enum):
    """Price level values."""
    FREE = "0"
    INEXPENSIVE = "1" 
    MODERATE = "2"
    EXPENSIVE = "3"
    VERY_EXPENSIVE = "4"


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


# New Places API Enums and Types

class PaymentOption(str, Enum):
    """Payment options accepted by a place."""
    CREDIT_CARD = "ACCEPTS_CREDIT_CARDS"
    DEBIT_CARD = "ACCEPTS_DEBIT_CARDS"
    CASH_ONLY = "ACCEPTS_CASH_ONLY"
    NFC = "ACCEPTS_NFC"


class ParkingOption(str, Enum):
    """Parking options provided by a place."""
    FREE_PARKING_LOT = "FREE_PARKING_LOT"
    PAID_PARKING_LOT = "PAID_PARKING_LOT"
    FREE_STREET_PARKING = "FREE_STREET_PARKING"
    VALET_PARKING = "VALET_PARKING"
    FREE_GARAGE_PARKING = "FREE_GARAGE_PARKING"
    PAID_GARAGE_PARKING = "PAID_GARAGE_PARKING"


class FuelOption(str, Enum):
    """Fuel options available at a gas station."""
    DIESEL = "DIESEL"
    REGULAR_UNLEADED = "REGULAR_UNLEADED"
    MIDGRADE = "MIDGRADE"
    PREMIUM = "PREMIUM"
    SP91 = "SP91"
    SP91_E10 = "SP91_E10"
    SP92 = "SP92"
    SP95_E10 = "SP95_E10"
    SP98 = "SP98"
    SP99 = "SP99"
    SP100 = "SP100"
    LPG = "LPG"
    E80 = "E80"
    E85 = "E85"
    METHANE = "METHANE"
    BIODIESEL = "BIODIESEL"
    TRUCK_DIESEL = "TRUCK_DIESEL"


class PaymentOptions(BaseModel):
    """Payment options accepted by a place."""
    accepts_credit_cards: Optional[bool] = Field(None, description="Place accepts credit cards")
    accepts_debit_cards: Optional[bool] = Field(None, description="Place accepts debit cards")
    accepts_cash_only: Optional[bool] = Field(None, description="Place accepts cash only")
    accepts_nfc: Optional[bool] = Field(None, description="Place accepts NFC payments")


class ParkingOptions(BaseModel):
    """Parking options provided by a place."""
    free_parking_lot: Optional[bool] = Field(None, description="Place provides free parking lot")
    paid_parking_lot: Optional[bool] = Field(None, description="Place provides paid parking lot")
    free_street_parking: Optional[bool] = Field(None, description="Place provides free street parking")
    valet_parking: Optional[bool] = Field(None, description="Place provides valet parking")
    free_garage_parking: Optional[bool] = Field(None, description="Place provides free garage parking")
    paid_garage_parking: Optional[bool] = Field(None, description="Place provides paid garage parking")


class FuelOptions(BaseModel):
    """Fuel options available at a gas station."""
    diesel: Optional[bool] = Field(None, description="Station provides diesel")
    regular_unleaded: Optional[bool] = Field(None, description="Station provides regular unleaded")
    midgrade: Optional[bool] = Field(None, description="Station provides midgrade")
    premium: Optional[bool] = Field(None, description="Station provides premium")
    sp91: Optional[bool] = Field(None, description="Station provides SP91")
    sp91_e10: Optional[bool] = Field(None, description="Station provides SP91 E10")
    sp92: Optional[bool] = Field(None, description="Station provides SP92")
    sp95_e10: Optional[bool] = Field(None, description="Station provides SP95 E10")
    sp98: Optional[bool] = Field(None, description="Station provides SP98")
    sp99: Optional[bool] = Field(None, description="Station provides SP99")
    sp100: Optional[bool] = Field(None, description="Station provides SP100")
    lpg: Optional[bool] = Field(None, description="Station provides LPG")
    e80: Optional[bool] = Field(None, description="Station provides E80")
    e85: Optional[bool] = Field(None, description="Station provides E85")
    methane: Optional[bool] = Field(None, description="Station provides methane")
    biodiesel: Optional[bool] = Field(None, description="Station provides biodiesel")
    truck_diesel: Optional[bool] = Field(None, description="Station provides truck diesel")


class EVChargeOptions(BaseModel):
    """Electric vehicle charging options."""
    connector_count: Optional[int] = Field(None, description="Number of EV chargers available")
    connector_aggregation: Optional[List[dict]] = Field(None, description="EV charging connector details")



class AccessibilityOptions(BaseModel):
    """Accessibility options for a place."""
    wheelchair_accessible_parking: Optional[bool] = Field(None, description="Place offers wheelchair-accessible parking")
    wheelchair_accessible_entrance: Optional[bool] = Field(None, description="Place has wheelchair-accessible entrance")
    wheelchair_accessible_restroom: Optional[bool] = Field(None, description="Place has wheelchair-accessible restroom")
    wheelchair_accessible_seating: Optional[bool] = Field(None, description="Place has wheelchair-accessible seating")


class PlaceAttributes(BaseModel):
    """Additional attributes for a place."""
    outdoor_seating: Optional[bool] = Field(None, description="Place provides outdoor seating")
    live_music: Optional[bool] = Field(None, description="Place provides live music")
    menu_for_children: Optional[bool] = Field(None, description="Place has a children's menu")
    serves_cocktails: Optional[bool] = Field(None, description="Place serves cocktails")
    serves_dessert: Optional[bool] = Field(None, description="Place serves dessert")
    serves_coffee: Optional[bool] = Field(None, description="Place serves coffee")
    good_for_children: Optional[bool] = Field(None, description="Place is good for children")
    allows_dogs: Optional[bool] = Field(None, description="Place allows dogs")
    restroom: Optional[bool] = Field(None, description="Place has a restroom")
    good_for_groups: Optional[bool] = Field(None, description="Place accommodates groups")
    good_for_watching_sports: Optional[bool] = Field(None, description="Place is suitable for watching sports")


class DisplayName(BaseModel):
    """Display name with language code."""
    text: str = Field(..., description="The display name text")
    language_code: Optional[str] = Field(None, description="The language code")


class PlacePhotoNew(BaseModel):
    """New Places API photo model."""
    name: str = Field(..., description="Photo resource name for fetching the photo")
    width_px: int = Field(..., description="The maximum available width in pixels")
    height_px: int = Field(..., description="The maximum available height in pixels")
    author_attributions: Optional[List[dict]] = Field(None, description="Author attribution information")


class RegularSecondaryOpeningHours(BaseModel):
    """Secondary opening hours for specific operations."""
    open_now: Optional[bool] = Field(None, description="Whether the place is currently open for secondary operations")
    periods: Optional[List[dict]] = Field(None, description="Opening periods for secondary operations")
    weekday_text: Optional[List[str]] = Field(None, description="Formatted secondary opening hours")
    secondary_hours_type: Optional[str] = Field(None, description="Type of secondary hours (e.g., DRIVE_THROUGH, DELIVERY)")


class PlaceSummary(BaseModel):
    """AI-powered place summary."""
    overview: Optional[str] = Field(None, description="Overview summary of the place")
    language_code: Optional[str] = Field(None, description="Language code of the summary")


class ReviewSummary(BaseModel):
    """AI-powered review summary."""
    overview: Optional[str] = Field(None, description="Summary of reviews")
    language_code: Optional[str] = Field(None, description="Language code of the summary")
