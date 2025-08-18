"""
FastAPI routes for Google Places API backend.
"""
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import JSONResponse

from .places_client import GooglePlacesClient, GooglePlacesAPIError
from .config import get_settings
from models import (
    NearbySearchRequest,
    TextSearchRequest,
    PlacesNearbySearchResponse,
    PlacesTextSearchResponse,
    HealthResponse,
    ErrorResponse,
    Place,
    RankBy,
    PriceLevel,
    ZipCodeRequest,
    ZipCodeResponse,
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
                    "message": "Google Maps API is not accessible",
                    "status_code": 503,
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
                "message": "Health check failed",
                "status_code": 503,
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/nearby",
    response_model=PlacesNearbySearchResponse,
    summary="Nearby Places Search",
    description="Search for places within a specified area using Google Places Nearby Search API.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful response with places data"},
        400: {"description": "Bad request - invalid parameters", "model": ErrorResponse},
        403: {"description": "Forbidden - API key issues", "model": ErrorResponse},
        429: {"description": "Too many requests - quota exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def nearby_search(request: NearbySearchRequest = Body(...)):
    """
    Search for places near a location.
    
    This endpoint implements the Google Places Nearby Search API, allowing you to search 
    for places within a specified area. You can refine your search by supplying keywords 
    or specifying the type of place you are searching for.
    
    Args:
        request: The nearby search request parameters
        
    Returns:
        PlacesNearbySearchResponse: Response containing a list of places
    """
    try:
        async with GooglePlacesClient() as client:
            response = await client.nearby_search(request)
            
        logger.info(f"Nearby search completed successfully. Found {len(response.results)} places.")
        return response
        
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in nearby search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/nearby",
    response_model=PlacesNearbySearchResponse,
    summary="Nearby Places Search (GET)",
    description="Search for places within a specified area using query parameters.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful response with places data"},
        400: {"description": "Bad request - invalid parameters", "model": ErrorResponse},
        403: {"description": "Forbidden - API key issues", "model": ErrorResponse},
        429: {"description": "Too many requests - quota exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def nearby_search_get(
    location: str = Query(..., description="Location as lat,lng", example="-33.8670522,151.1957362"),
    radius: int = Query(None, description="Search radius in meters", ge=1, le=50000, example=1500),
    rankby: RankBy = Query(RankBy.PROMINENCE, description="Ranking preference"),
    keyword: str = Query(None, description="Keyword to match", example="restaurant"),
    language: str = Query(None, description="Language code", example="en"),
    maxprice: PriceLevel = Query(None, description="Maximum price level"),
    minprice: PriceLevel = Query(None, description="Minimum price level"),
    name: str = Query(None, description="Name to match", example="Google"),
    opennow: bool = Query(None, description="Only open places"),
    pagetoken: str = Query(None, description="Page token for additional results"),
    type: str = Query(None, description="Place type to filter", example="restaurant"),
):
    """
    Search for places near a location using GET parameters.
    
    This is an alternative endpoint that accepts the same parameters as the POST version
    but uses query parameters instead of a request body.
    """
    try:
        # Create request object from query parameters
        request = NearbySearchRequest(
            location=location,
            radius=radius,
            rankby=rankby,
            keyword=keyword,
            language=language,
            maxprice=maxprice,
            minprice=minprice,
            name=name,
            opennow=opennow,
            pagetoken=pagetoken,
            type=type
        )
        
        async with GooglePlacesClient() as client:
            response = await client.nearby_search(request)
            
        logger.info(f"Nearby search (GET) completed successfully. Found {len(response.results)} places.")
        return response
        
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in nearby search (GET): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/search",
    response_model=PlacesTextSearchResponse,
    summary="Text Search",
    description="Search for places based on a text string using Google Places Text Search API.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful response with places data"},
        400: {"description": "Bad request - invalid parameters", "model": ErrorResponse},
        403: {"description": "Forbidden - API key issues", "model": ErrorResponse},
        429: {"description": "Too many requests - quota exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def text_search(request: TextSearchRequest = Body(...)):
    """
    Search for places using a text query.
    
    The Google Places API Text Search Service returns information about a set of places 
    based on a string — for example "pizza in New York" or "shoe stores near Ottawa".
    The service is especially useful for making ambiguous address queries.
    
    Args:
        request: The text search request parameters
        
    Returns:
        PlacesTextSearchResponse: Response containing a list of places
    """
    try:
        async with GooglePlacesClient() as client:
            response = await client.text_search(request)
            
        logger.info(f"Text search completed successfully. Found {len(response.results)} places.")
        return response
        
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in text search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# Simple endpoint to get just the places from a nearby search
@router.get(
    "/places/nearby",
    response_model=List[Place],
    summary="Get Nearby Places (Simple)",
    description="Get a simple list of nearby places without metadata.",
    status_code=status.HTTP_200_OK,
)
async def get_nearby_places(
    location: str = Query(..., description="Location as lat,lng", example="-33.8670522,151.1957362"),
    radius: int = Query(1500, description="Search radius in meters", ge=1, le=50000),
    type: str = Query(None, description="Place type to filter", example="restaurant"),
    keyword: str = Query(None, description="Keyword to match", example="cafe"),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=60),
):
    """
    Get a simple list of nearby places.
    
    This endpoint returns only the places array without the additional metadata
    from the Google Places API response.
    """
    try:
        request = NearbySearchRequest(
            location=location,
            radius=radius,
            type=type,
            keyword=keyword,
            rankby=RankBy.PROMINENCE
        )
        
        async with GooglePlacesClient() as client:
            response = await client.nearby_search(request)
            
        # Return only the places, limited to the requested amount
        places = response.results[:limit]
        
        logger.info(f"Simple nearby places search completed. Returning {len(places)} places.")
        return places
        
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in simple nearby places: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/zip",
    response_model=ZipCodeResponse,
    summary="Zip Code Lookup",
    description="Look up information about a US zip code using Google Geocoding API.",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful response with zip code information"},
        400: {"description": "Bad request - invalid zip code", "model": ErrorResponse},
        403: {"description": "Forbidden - API key issues", "model": ErrorResponse},
        404: {"description": "Zip code not found", "model": ErrorResponse},
        429: {"description": "Too many requests - quota exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    }
)
async def lookup_zip_code(request: ZipCodeRequest = Body(...)):
    """
    Look up information about a US zip code.
    
    This endpoint uses the Google Geocoding API to retrieve detailed information
    about a zip code including city, state, coordinates, and other location data.
    
    Args:
        request: The zip code request with zip_code and optional country
        
    Returns:
        ZipCodeResponse: Response containing zip code information and coordinates
    """
    try:
        async with GooglePlacesClient() as client:
            response = await client.lookup_zip_code(request)
            
        if response.status == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.error_message or "Zip code not found"
            )
        elif response.status == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error_message or "Error processing zip code lookup"
            )
            
        logger.info(f"Zip code lookup completed successfully for {request.zip_code}.")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except GooglePlacesAPIError as e:
        logger.error(f"Google Places API error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in zip code lookup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
