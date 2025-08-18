"""
Request models for Google Places API.
Based on the official Google Maps Platform OpenAPI specification parameters.
"""
from typing import Optional, List
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


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


class PlaceType(str, Enum):
    """Common place types for filtering."""
    # Accommodation
    LODGING = "lodging"
    
    # Food
    BAKERY = "bakery"
    BAR = "bar"
    CAFE = "cafe"
    MEAL_DELIVERY = "meal_delivery"
    MEAL_TAKEAWAY = "meal_takeaway"
    RESTAURANT = "restaurant"
    
    # Automotive
    CAR_DEALER = "car_dealer"
    CAR_RENTAL = "car_rental"
    CAR_REPAIR = "car_repair"
    CAR_WASH = "car_wash"
    GAS_STATION = "gas_station"
    PARKING = "parking"
    
    # Business
    ATM = "atm"
    BANK = "bank"
    BEAUTY_SALON = "beauty_salon"
    BICYCLE_STORE = "bicycle_store"
    BOOK_STORE = "book_store"
    CLOTHING_STORE = "clothing_store"
    ELECTRONICS_STORE = "electronics_store"
    FURNITURE_STORE = "furniture_store"
    GROCERY_OR_SUPERMARKET = "grocery_or_supermarket"
    HARDWARE_STORE = "hardware_store"
    JEWELRY_STORE = "jewelry_store"
    PHARMACY = "pharmacy"
    SHOE_STORE = "shoe_store"
    SHOPPING_MALL = "shopping_mall"
    STORE = "store"
    SUPERMARKET = "supermarket"
    
    # Entertainment
    AMUSEMENT_PARK = "amusement_park"
    AQUARIUM = "aquarium"
    ART_GALLERY = "art_gallery"
    BOWLING_ALLEY = "bowling_alley"
    CASINO = "casino"
    MOVIE_THEATER = "movie_theater"
    MUSEUM = "museum"
    NIGHT_CLUB = "night_club"
    PARK = "park"
    ZOO = "zoo"
    
    # Health & Medical
    DENTIST = "dentist"
    DOCTOR = "doctor"
    HOSPITAL = "hospital"
    PHYSIOTHERAPIST = "physiotherapist"
    VETERINARY_CARE = "veterinary_care"
    
    # Places of Worship
    CHURCH = "church"
    HINDU_TEMPLE = "hindu_temple"
    MOSQUE = "mosque"
    SYNAGOGUE = "synagogue"
    
    # Services
    ACCOUNTING = "accounting"
    ELECTRICIAN = "electrician"
    INSURANCE_AGENCY = "insurance_agency"
    LAUNDRY = "laundry"
    LAWYER = "lawyer"
    LOCKSMITH = "locksmith"
    MOVING_COMPANY = "moving_company"
    PLUMBER = "plumber"
    REAL_ESTATE_AGENCY = "real_estate_agency"
    ROOFING_CONTRACTOR = "roofing_contractor"
    STORAGE = "storage"
    
    # Transportation
    AIRPORT = "airport"
    BUS_STATION = "bus_station"
    LIGHT_RAIL_STATION = "light_rail_station"
    SUBWAY_STATION = "subway_station"
    TAXI_STAND = "taxi_stand"
    TRAIN_STATION = "train_station"
    TRANSIT_STATION = "transit_station"


class NearbySearchRequest(BaseModel):
    """
    Request model for Google Places Nearby Search.
    Based on the official Google Places API parameters.
    """
    location: str = Field(
        ...,
        description="The point around which to retrieve place information (lat,lng)",
        example="-33.8670522,151.1957362"
    )
    radius: Optional[int] = Field(
        None,
        description="Distance in meters within which to return place results (max 50000)",
        ge=1,
        le=50000,
        example=1500
    )
    rankby: Optional[RankBy] = Field(
        RankBy.PROMINENCE,
        description="Specifies the order in which results are listed"
    )
    keyword: Optional[str] = Field(
        None,
        description="A term to be matched against all content that Google has indexed for this place",
        example="cruise"
    )
    language: Optional[str] = Field(
        None,
        description="Language code for results (IETF language tag)",
        example="en"
    )
    maxprice: Optional[PriceLevel] = Field(
        None,
        description="Maximum price level for results"
    )
    minprice: Optional[PriceLevel] = Field(
        None,
        description="Minimum price level for results"
    )
    name: Optional[str] = Field(
        None,
        description="Equivalent to keyword parameter but specifically restricted to the name field",
        example="Google"
    )
    opennow: Optional[bool] = Field(
        None,
        description="Return only places that are open for business at the time the query is sent"
    )
    pagetoken: Optional[str] = Field(
        None,
        description="Returns up to 20 additional results"
    )
    type: Optional[str] = Field(
        None,
        description="Restricts results to places matching the specified type",
        example="restaurant"
    )

    @validator('location')
    def validate_location(cls, v):
        """Validate location is in correct lat,lng format."""
        try:
            parts = v.split(',')
            if len(parts) != 2:
                raise ValueError("Location must be in format 'lat,lng'")
            
            lat, lng = float(parts[0]), float(parts[1])
            
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lng <= 180):
                raise ValueError("Longitude must be between -180 and 180")
                
            return v
        except (ValueError, IndexError):
            raise ValueError("Location must be in format 'lat,lng' with valid coordinates")

    @validator('radius')
    def validate_radius_with_rankby(cls, v, values):
        """Validate radius constraints based on rankby."""
        if 'rankby' in values:
            if values['rankby'] == RankBy.DISTANCE and v is not None:
                raise ValueError("radius cannot be specified when rankby=distance")
            elif values['rankby'] == RankBy.PROMINENCE and v is None:
                raise ValueError("radius is required when rankby=prominence")
        return v


class TextSearchRequest(BaseModel):
    """
    Request model for Google Places Text Search.
    Based on the official Google Places API parameters.
    """
    query: str = Field(
        ...,
        description="The text string on which to search",
        example="restaurants in Sydney"
    )
    location: Optional[str] = Field(
        None,
        description="The point around which to retrieve place information (lat,lng)",
        example="42.3675294,-71.186966"
    )
    radius: Optional[int] = Field(
        None,
        description="Distance in meters within which to return place results",
        ge=1,
        le=50000,
        example=10000
    )
    language: Optional[str] = Field(
        None,
        description="Language code for results (IETF language tag)",
        example="en"
    )
    maxprice: Optional[PriceLevel] = Field(
        None,
        description="Maximum price level for results"
    )
    minprice: Optional[PriceLevel] = Field(
        None,
        description="Minimum price level for results"
    )
    opennow: Optional[bool] = Field(
        None,
        description="Return only places that are open for business at the time the query is sent"
    )
    pagetoken: Optional[str] = Field(
        None,
        description="Returns up to 20 additional results"
    )
    type: Optional[str] = Field(
        None,
        description="Restricts results to places matching the specified type",
        example="restaurant"
    )
    region: Optional[str] = Field(
        None,
        description="Country code for biasing results (ccTLD format)",
        example="au"
    )

    @validator('location')
    def validate_location(cls, v):
        """Validate location is in correct lat,lng format."""
        if v is None:
            return v
        try:
            parts = v.split(',')
            if len(parts) != 2:
                raise ValueError("Location must be in format 'lat,lng'")
            
            lat, lng = float(parts[0]), float(parts[1])
            
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lng <= 180):
                raise ValueError("Longitude must be between -180 and 180")
                
            return v
        except (ValueError, IndexError):
            raise ValueError("Location must be in format 'lat,lng' with valid coordinates")
