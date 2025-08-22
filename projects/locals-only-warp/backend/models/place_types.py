"""
Google Places API Place Types

This module defines all the place types supported by the Google Places API.
Based on: https://developers.google.com/maps/documentation/places/web-service/place-types

These types are used for filtering places in nearby search and text search requests.
"""

from typing import List, Set, Dict
from enum import Enum

class PlaceTypeCategory(Enum):
    """Categories for organizing place types"""
    ESTABLISHMENT = "establishment"
    FOOD_AND_DRINK = "food_and_drink"
    HEALTH_AND_WELLNESS = "health_and_wellness"
    LODGING = "lodging"
    SHOPPING = "shopping"
    TRANSPORTATION = "transportation"
    AUTOMOTIVE = "automotive"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    GOVERNMENT = "government"
    RELIGIOUS = "religious"
    SERVICES = "services"
    GEOGRAPHY = "geography"

# Complete list of Google Places API place types
PLACE_TYPES: List[str] = [
    # Establishment types
    "accounting",
    "airport",
    "amusement_park", 
    "aquarium",
    "art_gallery",
    "atm",
    "bakery",
    "bank",
    "bar",
    "beauty_salon",
    "bicycle_store",
    "book_store",
    "bowling_alley",
    "bus_station",
    "cafe",
    "campground",
    "car_dealer",
    "car_rental",
    "car_repair",
    "car_wash",
    "casino",
    "cemetery",
    "church",
    "city_hall",
    "clothing_store",
    "convenience_store",
    "courthouse",
    "dentist",
    "department_store",
    "doctor",
    "drugstore",
    "electrician",
    "electronics_store",
    "embassy",
    "establishment",
    "finance",
    "fire_station",
    "florist",
    "food",
    "funeral_home",
    "furniture_store",
    "gas_station",
    "gym",
    "hair_care",
    "hardware_store",
    "health",
    "hindu_temple",
    "home_goods_store",
    "hospital",
    "insurance_agency",
    "jewelry_store",
    "laundry",
    "lawyer",
    "library",
    "light_rail_station",
    "liquor_store",
    "local_government_office",
    "locksmith",
    "lodging",
    "meal_delivery",
    "meal_takeaway",
    "mosque",
    "movie_rental",
    "movie_theater",
    "moving_company",
    "museum",
    "night_club",
    "painter",
    "park",
    "parking",
    "pet_store",
    "pharmacy",
    "physiotherapist",
    "plumber",
    "point_of_interest",
    "police",
    "post_office",
    "primary_school",
    "real_estate_agency",
    "restaurant",
    "roofing_contractor",
    "rv_park",
    "school",
    "secondary_school",
    "shoe_store",
    "shopping_mall",
    "spa",
    "stadium",
    "storage",
    "store",
    "subway_station",
    "supermarket",
    "synagogue",
    "taxi_stand",
    "tourist_attraction",
    "train_station",
    "transit_station",
    "travel_agency",
    "university",
    "veterinary_care",
    "zoo",
    
    # Additional types from newer API versions
    "administrative_area_level_1",
    "administrative_area_level_2", 
    "administrative_area_level_3",
    "administrative_area_level_4",
    "administrative_area_level_5",
    "archipelago",
    "colloquial_area",
    "continent",
    "country",
    "floor",
    "geocode",
    "intersection",
    "locality",
    "natural_feature",
    "neighborhood",
    "plus_code",
    "political",
    "postal_code",
    "postal_code_prefix",
    "postal_code_suffix",
    "postal_town",
    "premise",
    "room",
    "route",
    "street_address",
    "street_number",
    "sublocality",
    "sublocality_level_1",
    "sublocality_level_2", 
    "sublocality_level_3",
    "sublocality_level_4",
    "sublocality_level_5",
    "subpremise",
    "town_square",
]

# Categorized place types for better organization
PLACE_TYPE_CATEGORIES: Dict[PlaceTypeCategory, List[str]] = {
    PlaceTypeCategory.FOOD_AND_DRINK: [
        "bakery", "bar", "cafe", "food", "meal_delivery", "meal_takeaway", 
        "restaurant", "liquor_store"
    ],
    
    PlaceTypeCategory.SHOPPING: [
        "bicycle_store", "book_store", "clothing_store", "convenience_store",
        "department_store", "electronics_store", "florist", "furniture_store",
        "hardware_store", "home_goods_store", "jewelry_store", "pet_store",
        "shoe_store", "shopping_mall", "store", "supermarket"
    ],
    
    PlaceTypeCategory.HEALTH_AND_WELLNESS: [
        "beauty_salon", "dentist", "doctor", "drugstore", "gym", "hair_care",
        "health", "hospital", "pharmacy", "physiotherapist", "spa", "veterinary_care"
    ],
    
    PlaceTypeCategory.TRANSPORTATION: [
        "airport", "bus_station", "car_rental", "light_rail_station", "parking",
        "subway_station", "taxi_stand", "train_station", "transit_station"
    ],
    
    PlaceTypeCategory.AUTOMOTIVE: [
        "car_dealer", "car_repair", "car_wash", "gas_station"
    ],
    
    PlaceTypeCategory.ENTERTAINMENT: [
        "amusement_park", "aquarium", "art_gallery", "bowling_alley", "casino",
        "movie_theater", "museum", "night_club", "stadium", "tourist_attraction", "zoo"
    ],
    
    PlaceTypeCategory.LODGING: [
        "campground", "lodging", "rv_park"
    ],
    
    PlaceTypeCategory.EDUCATION: [
        "library", "primary_school", "school", "secondary_school", "university"
    ],
    
    PlaceTypeCategory.GOVERNMENT: [
        "city_hall", "courthouse", "embassy", "fire_station", "local_government_office",
        "police", "post_office"
    ],
    
    PlaceTypeCategory.RELIGIOUS: [
        "cemetery", "church", "funeral_home", "hindu_temple", "mosque", "synagogue"
    ],
    
    PlaceTypeCategory.SERVICES: [
        "accounting", "atm", "bank", "electrician", "finance", "insurance_agency",
        "laundry", "lawyer", "locksmith", "moving_company", "painter", "plumber",
        "real_estate_agency", "roofing_contractor", "storage", "travel_agency"
    ],
    
    PlaceTypeCategory.GEOGRAPHY: [
        "administrative_area_level_1", "administrative_area_level_2", "country",
        "locality", "natural_feature", "neighborhood", "park", "point_of_interest",
        "political", "postal_code"
    ]
}

# Popular/common place types for quick reference
POPULAR_PLACE_TYPES: List[str] = [
    "restaurant", "cafe", "bar", "hospital", "pharmacy", "gas_station",
    "bank", "atm", "supermarket", "shopping_mall", "gym", "park",
    "school", "university", "library", "museum", "movie_theater",
    "hotel", "airport", "train_station", "bus_station"
]

# Set for fast lookups
PLACE_TYPES_SET: Set[str] = set(PLACE_TYPES)


def validate_place_type(place_type: str) -> bool:
    """
    Validate if a place type is supported by Google Places API.
    
    Args:
        place_type: The place type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return place_type.lower() in PLACE_TYPES_SET


def get_place_types_by_category(category: PlaceTypeCategory) -> List[str]:
    """
    Get all place types for a specific category.
    
    Args:
        category: The category to get types for
        
    Returns:
        List[str]: List of place types in the category
    """
    return PLACE_TYPE_CATEGORIES.get(category, [])


def suggest_place_types(partial: str, limit: int = 10) -> List[str]:
    """
    Suggest place types based on partial input.
    
    Args:
        partial: Partial place type string
        limit: Maximum number of suggestions to return
        
    Returns:
        List[str]: List of matching place types
    """
    partial_lower = partial.lower()
    suggestions = []
    
    # Exact matches first
    if partial_lower in PLACE_TYPES_SET:
        suggestions.append(partial_lower)
    
    # Partial matches
    for place_type in PLACE_TYPES:
        if partial_lower in place_type and place_type not in suggestions:
            suggestions.append(place_type)
            if len(suggestions) >= limit:
                break
    
    return suggestions


def get_category_for_place_type(place_type: str) -> PlaceTypeCategory:
    """
    Get the category for a specific place type.
    
    Args:
        place_type: The place type to categorize
        
    Returns:
        PlaceTypeCategory: The category the place type belongs to
    """
    for category, types in PLACE_TYPE_CATEGORIES.items():
        if place_type in types:
            return category
    
    return PlaceTypeCategory.ESTABLISHMENT  # Default category


def format_place_types_help() -> str:
    """
    Format place types for command-line help display.
    
    Returns:
        str: Formatted help string showing available place types by category
    """
    help_text = "Available place types by category:\n\n"
    
    for category, types in PLACE_TYPE_CATEGORIES.items():
        help_text += f"{category.value.replace('_', ' ').title()}:\n"
        help_text += f"  {', '.join(sorted(types))}\n\n"
    
    help_text += f"Popular types: {', '.join(POPULAR_PLACE_TYPES)}\n"
    help_text += f"Total available types: {len(PLACE_TYPES)}"
    
    return help_text
