"""
Models package for cleaned up Places API integration.
"""

# Base types
from .base import (
    PlacesSearchStatus,
    RankBy,
    PriceLevel,
    LatLngLiteral,
    Geometry,
    AddressComponent,
    # New Places API types
    PaymentOptions,
    ParkingOptions,
    FuelOptions,
    EVChargeOptions,
    AccessibilityOptions,
    PlaceAttributes,
    DisplayName,
    PlacePhotoNew,
    RegularSecondaryOpeningHours,
    PlaceSummary,
    ReviewSummary,
)

# Place model (keep for internal use)
from .place import Place

# New Places API Request models
from .requests_new import (
    NearbySearchNewRequest,
    TextSearchNewRequest,
    LocationRestriction,
    Circle,
)

# Response models
from .responses import (
    ErrorResponse,
    HealthResponse,
)

# New Places API Response models
from .responses_new import (
    NearbySearchNewResponse,
    TextSearchNewResponse,
    PlaceDetailsNewResponse,
)

# Geocoding models (keep for zip code conversion)
from .geocoding import (
    GeocodingStatus,
    LocationType,
    GeocodingGeometry,
    GeocodingResult,
    GeocodingResponse,
    GeocodeRequest,
    ZipCodeRequest,
    ZipCodeInfo,
    ZipCodeResponse,
)

# Recommendation models (new simplified API)
from .recommendation import (
    Recommendation,
    ZipRecommendationsRequest,
    TextRecommendationsRequest,
    RecommendationsResponse,
)

# User models
from .user import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)

__all__ = [
    # Base types
    "PlacesSearchStatus", 
    "RankBy",
    "PriceLevel",
    "LatLngLiteral",
    "Geometry",
    "AddressComponent",
    # New Places API types
    "PaymentOptions",
    "ParkingOptions",
    "FuelOptions",
    "EVChargeOptions",
    "AccessibilityOptions",
    "PlaceAttributes",
    "DisplayName",
    "PlacePhotoNew",
    "RegularSecondaryOpeningHours",
    "PlaceSummary",
    "ReviewSummary",
    
    # Place model (internal use)
    "Place",
    
    # New Places API Request models
    "NearbySearchNewRequest",
    "TextSearchNewRequest",
    "LocationRestriction",
    "Circle",
    
    # Response models
    "ErrorResponse",
    "HealthResponse",
    # New Places API Response models
    "NearbySearchNewResponse",
    "TextSearchNewResponse",
    "PlaceDetailsNewResponse",
    
    # Geocoding models
    "GeocodingStatus",
    "LocationType",
    "GeocodingGeometry",
    "GeocodingResult",
    "GeocodingResponse",
    "GeocodeRequest",
    "ZipCodeRequest",
    "ZipCodeInfo",
    "ZipCodeResponse",
    
    # Recommendation models (new simplified API)
    "Recommendation",
    "ZipRecommendationsRequest",
    "TextRecommendationsRequest",
    "RecommendationsResponse",
    
    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
]
