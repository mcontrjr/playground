"""
Simplified FastAPI routes for local recommendations.
"""
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse

from .places_client import GooglePlacesClient, GooglePlacesAPIError
from .config import get_settings
from .database import get_db_manager
from models import (
    # New Places API models for internal use
    NearbySearchNewRequest,
    TextSearchNewRequest,
    LocationRestriction,
    Circle,
    ZipCodeRequest,
    # Public API models
    Recommendation,
    ZipRecommendationsRequest,
    TextRecommendationsRequest,
    RecommendationsResponse,
    HealthResponse,
    ErrorResponse,
    # User models
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the API and Google Maps service connectivity.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy", "model": ErrorResponse},
    }
)
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    
    try:
        # Test Google Places API connectivity
        async with GooglePlacesClient() as client:
            is_healthy = await client.health_check()
        
        if not is_healthy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "service_unavailable",
                    "message": "Google Maps API is not accessible - health check failed",
                    "status_code": 503,
                    "reason": "Google Maps API connectivity test failed",
                    "details": {"google_maps_api": "unreachable"}
                }
            )
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat() + "Z",
            version=settings.api_version
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "internal_error",
                "message": f"Health check failed - {str(e)}",
                "status_code": 503,
                "reason": "Internal error during health check",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/rec_from_zip",
    response_model=RecommendationsResponse,
    summary="Get Recommendations from Zip Code",
    description="Get local recommendations for a US zip code using Nearby Search (New) API.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful response with local recommendations"},
        400: {"description": "Bad request - invalid zip code or parameters", "model": ErrorResponse},
        403: {"description": "Forbidden - API key issues", "model": ErrorResponse},
        404: {"description": "Zip code not found", "model": ErrorResponse},
        429: {"description": "Too many requests - quota exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def get_recommendations_from_zip(request: ZipRecommendationsRequest = Body(...)):
    """
    Get local recommendations for a zip code using New Places API.
    
    This endpoint converts a zip code to coordinates using Google Geocoding API,
    then searches for nearby places using the New Places API and returns a simplified
    list of recommendations.
    
    Args:
        request: Minimal request with zip code and optional radius
        
    Returns:
        RecommendationsResponse: Response containing local recommendations
    """
    try:
        async with GooglePlacesClient() as client:
            # Step 1: Convert zip code to coordinates
            zip_request = ZipCodeRequest(zip_code=request.zip_code)
            zip_response = await client.lookup_zip_code(zip_request)
            
            if zip_response.status == "not_found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Zip code {request.zip_code} not found - please check the zip code is valid",
                )
            elif zip_response.status == "error":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing zip code lookup - {zip_response.error_message or 'geocoding failed'}",
                )
            
            # Step 2: Search for nearby places using the New Places API
            nearby_request = NearbySearchNewRequest(
                fields=[
                    "places.id", "places.displayName", "places.formattedAddress", 
                    "places.location", "places.rating", "places.userRatingCount",
                    "places.priceLevel", "places.types", "places.currentOpeningHours",
                    "places.nationalPhoneNumber", "places.websiteUri"
                ],
                location_restriction=LocationRestriction(
                    circle=Circle(
                        center={
                            "latitude": zip_response.latitude,
                            "longitude": zip_response.longitude
                        },
                        radius=request.radius or 1500
                    )
                ),
                max_result_count=20,  # Fixed at 20 for simplicity
                language_code="en",
                region_code="US"
            )
            
            places_response = await client.nearby_search_new(nearby_request)
            
            if not places_response.places:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No places found near zip code {request.zip_code}"
                )
            
            # Step 3: Convert places to simplified recommendations
            recommendations = []
            for place in places_response.places:
                # Extract primary category from types
                category = None
                if place.types:
                    # Use the first type that's not a generic type
                    generic_types = {"point_of_interest", "establishment", "food", "store"}
                    for place_type in place.types:
                        if place_type.replace("_", " ") not in generic_types:
                            category = place_type.replace("_", " ").title()
                            break
                    if not category and place.types:
                        category = place.types[0].replace("_", " ").title()
                
                # Get opening status
                is_open = None
                if hasattr(place, 'currentOpeningHours') and place.currentOpeningHours:
                    is_open = getattr(place.currentOpeningHours, 'openNow', None)
                
                # Extract location coordinates
                latitude = None
                longitude = None
                if hasattr(place, 'location') and place.location:
                    if isinstance(place.location, dict):
                        latitude = place.location.get('latitude')
                        longitude = place.location.get('longitude')
                    else:
                        latitude = getattr(place.location, 'latitude', None)
                        longitude = getattr(place.location, 'longitude', None)
                
                # Extract display name safely
                name = "Unknown Place"
                if hasattr(place, 'display_name') and place.display_name:
                    if isinstance(place.display_name, dict):
                        name = place.display_name.get('text', 'Unknown Place')
                    else:
                        name = getattr(place.display_name, 'text', 'Unknown Place')
                elif hasattr(place, 'name') and place.name:
                    name = place.name
                
                # Create recommendation
                recommendation = Recommendation(
                    name=name,
                    place_id=getattr(place, 'id', '') or getattr(place, 'place_id', ''),
                    address=getattr(place, 'formattedAddress', None) or getattr(place, 'formatted_address', None),
                    latitude=latitude,
                    longitude=longitude,
                    rating=getattr(place, 'rating', None),
                    review_count=getattr(place, 'userRatingCount', None) or getattr(place, 'user_ratings_total', None),
                    price_level=getattr(place, 'priceLevel', None) or getattr(place, 'price_level', None),
                    category=category,
                    is_open=is_open,
                    phone=getattr(place, 'nationalPhoneNumber', None) or getattr(place, 'formatted_phone_number', None),
                    website=getattr(place, 'websiteUri', None) or getattr(place, 'website', None)
                )
                recommendations.append(recommendation)
            
            # Create location string
            location_str = f"{zip_response.city or 'Unknown'}, {zip_response.state or 'Unknown'}"
            
            logger.info(f"Generated {len(recommendations)} recommendations for zip code {request.zip_code}")
            
            return RecommendationsResponse(
                zip_code=request.zip_code,
                location=location_str,
                latitude=zip_response.latitude,
                longitude=zip_response.longitude,
                radius=request.radius or 1500,
                total_found=len(recommendations),
                recommendations=recommendations,
                message=f"Found {len(recommendations)} local recommendations for {request.zip_code}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        
        # Map Google API errors to HTTP errors with reasons
        if e.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request parameters - {e.detail}"
            )
        elif e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API access denied - {e.detail}"
            )
        elif e.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded - {e.detail}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google Maps service error - {e.detail}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error - {str(e)}"
        )


@router.post(
    "/rec_from_text",
    response_model=RecommendationsResponse,
    summary="Get Recommendations from Text Query",
    description="Get local recommendations using text search query with Text Search (New) API.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful response with local recommendations"},
        400: {"description": "Bad request - invalid search query or parameters", "model": ErrorResponse},
        403: {"description": "Forbidden - API key issues", "model": ErrorResponse},
        404: {"description": "No results found for search query", "model": ErrorResponse},
        429: {"description": "Too many requests - quota exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def get_text_recommendations(request: TextRecommendationsRequest = Body(...)):
    """
    Get local recommendations based on text search query using New Places API.
    
    This endpoint searches for places using the New Places Text Search API,
    which provides more relevant results based on natural language queries
    and location context.
    
    Args:
        request: Minimal request with search query string
        
    Returns:
        RecommendationsResponse: Response containing local recommendations
    """
    try:
        async with GooglePlacesClient() as client:
            # Construct text search request for New Places API
            text_search_request = TextSearchNewRequest(
                text_query=request.query,
                fields=[
                    "places.id", "places.displayName", "places.formattedAddress", 
                    "places.location", "places.rating", "places.userRatingCount",
                    "places.priceLevel", "places.types", "places.currentOpeningHours",
                    "places.nationalPhoneNumber", "places.websiteUri"
                ],
                max_result_count=20,  # Fixed at 20 for simplicity
                language_code="en",
                region_code="US"
            )
            
            # Perform text search using New Places API
            places_response = await client.text_search_new(text_search_request)
            
            if not places_response.places:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No results found for search query: '{request.query}'"
                )
            
            # Convert places to simplified recommendations
            recommendations = []
            for place in places_response.places:
                # Extract primary category from types
                category = None
                if place.types:
                    # Use the first type that's not a generic type
                    generic_types = {"point_of_interest", "establishment", "food", "store"}
                    for place_type in place.types:
                        if place_type.replace("_", " ") not in generic_types:
                            category = place_type.replace("_", " ").title()
                            break
                    if not category and place.types:
                        category = place.types[0].replace("_", " ").title()
                
                # Get opening status
                is_open = None
                if hasattr(place, 'currentOpeningHours') and place.currentOpeningHours:
                    is_open = getattr(place.currentOpeningHours, 'openNow', None)
                
                # Extract location coordinates
                latitude = None
                longitude = None
                if hasattr(place, 'location') and place.location:
                    if isinstance(place.location, dict):
                        latitude = place.location.get('latitude')
                        longitude = place.location.get('longitude')
                    else:
                        latitude = getattr(place.location, 'latitude', None)
                        longitude = getattr(place.location, 'longitude', None)
                
                # Extract display name safely
                name = "Unknown Place"
                if hasattr(place, 'display_name') and place.display_name:
                    if isinstance(place.display_name, dict):
                        name = place.display_name.get('text', 'Unknown Place')
                    else:
                        name = getattr(place.display_name, 'text', 'Unknown Place')
                elif hasattr(place, 'name') and place.name:
                    name = place.name
                
                # Create recommendation
                recommendation = Recommendation(
                    name=name,
                    place_id=getattr(place, 'id', '') or getattr(place, 'place_id', ''),
                    address=getattr(place, 'formattedAddress', None) or getattr(place, 'formatted_address', None),
                    latitude=latitude,
                    longitude=longitude,
                    rating=getattr(place, 'rating', None),
                    review_count=getattr(place, 'userRatingCount', None) or getattr(place, 'user_ratings_total', None),
                    price_level=getattr(place, 'priceLevel', None) or getattr(place, 'price_level', None),
                    category=category,
                    is_open=is_open,
                    phone=getattr(place, 'nationalPhoneNumber', None) or getattr(place, 'formatted_phone_number', None),
                    website=getattr(place, 'websiteUri', None) or getattr(place, 'website', None)
                )
                recommendations.append(recommendation)
            
            # Calculate center point for response (use first result as reference)
            center_lat = recommendations[0].latitude if recommendations and recommendations[0].latitude else None
            center_lng = recommendations[0].longitude if recommendations and recommendations[0].longitude else None
            
            logger.info(f"Generated {len(recommendations)} recommendations for text query: '{request.query}'")
            
            return RecommendationsResponse(
                zip_code=None,  # Not applicable for text search
                location=f"Results for '{request.query}'",
                latitude=center_lat,
                longitude=center_lng,
                radius=None,  # Not applicable for text search
                total_found=len(recommendations),
                recommendations=recommendations,
                message=f"Found {len(recommendations)} recommendations for '{request.query}'"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        
        # Map Google API errors to HTTP errors with reasons
        if e.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid search query or parameters - {e.detail}"
            )
        elif e.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API access denied - {e.detail}"
            )
        elif e.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded - {e.detail}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google Maps service error - {e.detail}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in text recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error - {str(e)}"
        )


# Legacy recommendations endpoint removed - use /rec_from_zip or /rec_from_text instead


# User CRUD endpoints

@router.post(
    "/users",
    response_model=UserResponse,
    summary="Create User",
    description="Create a new user with phone number and optional starred categories.",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Bad request - invalid input or phone number already exists", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def create_user(request: UserCreate = Body(...)):
    """
    Create a new user.
    
    Args:
        request: User creation data including phone number and optional starred categories
        
    Returns:
        UserResponse: Response containing the created user data
    """
    try:
        db = get_db_manager()
        user_data = db.create_user(
            phone_number=request.phone_number,
            starred_categories=request.starred_categories or []
        )
        
        user = User(**user_data)
        logger.info(f"Created user with ID: {user.id}")
        
        return UserResponse(
            user=user,
            message="User created successfully"
        )
        
    except ValueError as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User creation failed - {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user creation - {str(e)}"
        )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get User",
    description="Get a user by their unique ID.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def get_user(user_id: str):
    """
    Get a user by ID.
    
    Args:
        user_id: The unique user identifier
        
    Returns:
        UserResponse: Response containing the user data
    """
    try:
        db = get_db_manager()
        user_data = db.get_user(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found - no user exists with ID {user_id}"
            )
        
        user = User(**user_data)
        logger.info(f"Retrieved user with ID: {user.id}")
        
        return UserResponse(
            user=user,
            message="User retrieved successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user retrieval - {str(e)}"
        )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List Users",
    description="Get a paginated list of all users.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Users retrieved successfully"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def list_users(
    limit: int = Query(100, description="Maximum number of users to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of users to skip", ge=0)
):
    """
    List all users with pagination.
    
    Args:
        limit: Maximum number of users to return (default: 100, max: 1000)
        offset: Number of users to skip for pagination (default: 0)
        
    Returns:
        UserListResponse: Response containing list of users and pagination info
    """
    try:
        db = get_db_manager()
        users_data = db.list_users(limit=limit, offset=offset)
        total_users = db.count_users()
        
        users = [User(**user_data) for user_data in users_data]
        
        logger.info(f"Retrieved {len(users)} users (limit: {limit}, offset: {offset})")
        
        return UserListResponse(
            users=users,
            total=total_users,
            limit=limit,
            offset=offset,
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user listing - {str(e)}"
        )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update an existing user's information.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User updated successfully"},
        400: {"description": "Bad request - invalid input", "model": ErrorResponse},
        404: {"description": "User not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def update_user(user_id: str, request: UserUpdate = Body(...)):
    """
    Update an existing user.
    
    Args:
        user_id: The unique user identifier
        request: User update data (only provided fields will be updated)
        
    Returns:
        UserResponse: Response containing the updated user data
    """
    try:
        db = get_db_manager()
        
        # Build update dictionary from request, excluding None values
        updates = {}
        if request.phone_number is not None:
            updates['phone_number'] = request.phone_number
        if request.starred_categories is not None:
            updates['starred_categories'] = request.starred_categories
        if request.cached_recommendations is not None:
            updates['cached_recommendations'] = request.cached_recommendations
        if request.bookmarks is not None:
            updates['bookmarks'] = request.bookmarks
        
        user_data = db.update_user(user_id, **updates)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found - no user exists with ID {user_id}"
            )
        
        user = User(**user_data)
        logger.info(f"Updated user with ID: {user.id}")
        
        return UserResponse(
            user=user,
            message="User updated successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error(f"User update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User update failed - {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user update - {str(e)}"
        )


@router.delete(
    "/users/{user_id}",
    summary="Delete User",
    description="Delete a user by their unique ID.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User deleted successfully"},
        404: {"description": "User not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def delete_user(user_id: str):
    """
    Delete a user by ID.
    
    Args:
        user_id: The unique user identifier
        
    Returns:
        Dict: Confirmation message
    """
    try:
        db = get_db_manager()
        deleted = db.delete_user(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found - no user exists with ID {user_id}"
            )
        
        logger.info(f"Deleted user with ID: {user_id}")
        
        return {
            "message": "User deleted successfully",
            "user_id": user_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user deletion - {str(e)}"
        )


@router.get(
    "/users/phone/{phone_number}",
    response_model=UserResponse,
    summary="Get User by Phone",
    description="Get a user by their phone number.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    }
)
async def get_user_by_phone(phone_number: str):
    """
    Get a user by phone number.
    
    Args:
        phone_number: The user's phone number (URL-encoded if needed)
        
    Returns:
        UserResponse: Response containing the user data
    """
    try:
        db = get_db_manager()
        user_data = db.get_user_by_phone(phone_number)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found - no user exists with phone number {phone_number}"
            )
        
        user = User(**user_data)
        logger.info(f"Retrieved user by phone number: {phone_number}")
        
        return UserResponse(
            user=user,
            message="User retrieved successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user by phone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during user phone lookup - {str(e)}"
        )
