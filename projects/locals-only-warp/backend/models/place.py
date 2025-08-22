"""
Place model based on Google Places API schema.
Based on the official Google Maps Platform OpenAPI specification.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from .base import (
    BusinessStatus,
    Geometry,
    PlacePhoto,
    PlaceOpeningHours,
    AddressComponent,
    PlaceEditorialSummary,
    PlaceReview,
    PlusCode,
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


class Place(BaseModel):
    """
    A place object containing information about a location.
    Based on the official Google Places API Place schema.
    """
    # Core identification
    place_id: Optional[str] = Field(
        None, 
        description="A textual identifier that uniquely identifies a place",
        example="ChIJN1t_tDeuEmsRUsoyG83frY4"
    )
    name: Optional[str] = Field(
        None,
        description="Contains the human-readable name for the returned result",
        example="Google Workplace 6"
    )
    
    # Location and geometry
    geometry: Optional[Geometry] = Field(None, description="Contains the location and viewport for the location")
    formatted_address: Optional[str] = Field(
        None,
        alias="formattedAddress",
        description="A string containing the human-readable address of this place",
        example="48 Pirrama Rd, Pyrmont NSW 2009, Australia"
    )
    address_components: Optional[List[AddressComponent]] = Field(
        None,
        description="An array containing the separate components applicable to this address"
    )
    vicinity: Optional[str] = Field(
        None,
        description="Contains a simplified address for the place",
        example="48 Pirrama Road, Pyrmont"
    )
    
    # Business information
    business_status: Optional[BusinessStatus] = Field(
        None,
        description="Indicates the operational status of the place, if it is a business"
    )
    types: Optional[List[str]] = Field(
        None,
        description="Contains an array of feature types describing the given result",
        example=["point_of_interest", "establishment"]
    )
    
    # Contact information
    formatted_phone_number: Optional[str] = Field(
        None,
        description="Contains the place's phone number in its local format",
        example="(02) 9374 4000"
    )
    international_phone_number: Optional[str] = Field(
        None,
        description="Contains the place's phone number in international format",
        example="+61 2 9374 4000"
    )
    website: Optional[str] = Field(
        None,
        description="The authoritative website for this place",
        example="http://google.com"
    )
    url: Optional[str] = Field(
        None,
        description="Contains the URL of the official Google page for this place",
        example="https://maps.google.com/?cid=10281119596374313554"
    )
    
    # Ratings and reviews
    rating: Optional[float] = Field(
        None,
        description="Contains the place's rating, from 1.0 to 5.0, based on aggregated user reviews",
        example=4.1,
        ge=1.0,
        le=5.0
    )
    user_ratings_total: Optional[int] = Field(
        None,
        description="The total number of reviews, with or without text, for this place",
        example=931
    )
    reviews: Optional[List[PlaceReview]] = Field(
        None,
        description="A JSON array of up to five reviews"
    )
    
    # Pricing
    price_level: Optional[int] = Field(
        None,
        description="The price level of the place, on a scale of 0 to 4",
        ge=0,
        le=4
    )
    
    # Operating hours
    opening_hours: Optional[PlaceOpeningHours] = Field(
        None,
        description="Contains the regular hours of operation"
    )
    current_opening_hours: Optional[PlaceOpeningHours] = Field(
        None,
        description="Contains the hours of operation for the next seven days"
    )
    secondary_opening_hours: Optional[List[PlaceOpeningHours]] = Field(
        None,
        description="Contains an array of entries for the next seven days including information about secondary hours"
    )
    
    # Photos (New Places API format)
    photos: Optional[List[PlacePhotoNew]] = Field(
        None,
        description="An array of photo objects in New Places API format"
    )
    
    # Additional information
    adr_address: Optional[str] = Field(
        None,
        description="A representation of the place's address in the adr microformat"
    )
    editorial_summary: Optional[PlaceEditorialSummary] = Field(
        None,
        description="Contains a summary of the place"
    )
    icon: Optional[str] = Field(
        None,
        description="Contains the URL of a suggested icon",
        example="https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/generic_business-71.png"
    )
    icon_background_color: Optional[str] = Field(
        None,
        description="Contains the default HEX color code for the place's category"
    )
    icon_mask_base_uri: Optional[str] = Field(
        None,
        description="Contains the URL of a recommended icon, minus the file type extension"
    )
    plus_code: Optional[PlusCode] = Field(
        None,
        description="An encoded location reference, derived from latitude and longitude coordinates"
    )
    utc_offset: Optional[int] = Field(
        None,
        description="Contains the number of minutes this place's current timezone is offset from UTC",
        example=600
    )
    
    # Service options (for restaurants/businesses)
    curbside_pickup: Optional[bool] = Field(None, description="Specifies if the business supports curbside pickup")
    delivery: Optional[bool] = Field(None, description="Specifies if the business supports delivery")
    dine_in: Optional[bool] = Field(None, description="Specifies if the business supports indoor or outdoor seating")
    reservable: Optional[bool] = Field(None, description="Specifies if the place supports reservations")
    takeout: Optional[bool] = Field(None, description="Specifies if the business supports takeout")
    
    # Food service options
    serves_beer: Optional[bool] = Field(None, description="Specifies if the place serves beer")
    serves_breakfast: Optional[bool] = Field(None, description="Specifies if the place serves breakfast")
    serves_brunch: Optional[bool] = Field(None, description="Specifies if the place serves brunch")
    serves_dinner: Optional[bool] = Field(None, description="Specifies if the place serves dinner")
    serves_lunch: Optional[bool] = Field(None, description="Specifies if the place serves lunch")
    serves_vegetarian_food: Optional[bool] = Field(None, description="Specifies if the place serves vegetarian food")
    serves_wine: Optional[bool] = Field(None, description="Specifies if the place serves wine")
    
    # Accessibility
    wheelchair_accessible_entrance: Optional[bool] = Field(
        None,
        description="Specifies if the place has an entrance that is wheelchair-accessible"
    )
    
    # New Places API fields
    
    # New identification and naming
    id: Optional[str] = Field(None, description="New Places API place ID")
    display_name: Optional[DisplayName] = Field(None, alias="displayName", description="Display name with language")
    short_formatted_address: Optional[str] = Field(
        None,
        alias="shortFormattedAddress",
        description="Short, human-readable address"
    )
    primary_type: Optional[str] = Field(
        None,
        description="Primary type of the place",
        example="restaurant"
    )
    primary_type_display_name: Optional[DisplayName] = Field(
        None,
        description="Display name of the primary type"
    )
    
    # New operational details
    regular_secondary_opening_hours: Optional[List[RegularSecondaryOpeningHours]] = Field(
        None,
        description="Secondary opening hours for specific operations"
    )
    
    # New options and amenities
    payment_options: Optional[PaymentOptions] = Field(
        None,
        description="Payment options accepted by the place"
    )
    parking_options: Optional[ParkingOptions] = Field(
        None,
        description="Parking options provided by the place"
    )
    fuel_options: Optional[FuelOptions] = Field(
        None,
        description="Fuel options available (for gas stations)"
    )
    ev_charge_options: Optional[EVChargeOptions] = Field(
        None,
        description="EV charging options available"
    )
    
    # New accessibility options
    accessibility_options: Optional[AccessibilityOptions] = Field(
        None,
        description="Accessibility options for the place"
    )
    
    # New attributes
    place_attributes: Optional[PlaceAttributes] = Field(
        None,
        description="Additional place attributes"
    )
    
    
    # AI-powered summaries
    place_summary: Optional[PlaceSummary] = Field(
        None,
        description="AI-powered place summary"
    )
    review_summary: Optional[ReviewSummary] = Field(
        None,
        description="AI-powered review summary"
    )
    
    # Sub-destinations (for complex places like airports)
    sub_destinations: Optional[List[dict]] = Field(
        None,
        description="Related sub-destinations"
    )
    
    # Location information
    location: Optional[dict] = Field(
        None,
        description="Location coordinates in New Places API format"
    )
    viewport: Optional[dict] = Field(
        None,
        description="Viewport for displaying the place"
    )
    
    # Deprecated fields (kept for compatibility)
    permanently_closed: Optional[bool] = Field(
        None,
        deprecated=True,
        description="Use business_status to get the operational status of businesses"
    )
    reference: Optional[str] = Field(None, deprecated=True, description="Deprecated field")
    scope: Optional[str] = Field(None, deprecated=True, description="Deprecated field")
