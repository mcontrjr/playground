"""
Google Places API client implementation.
Based on the official Google Maps Platform API documentation.
"""
import httpx
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException

from .config import get_settings
from models import (
    # Geocoding models (needed for zip code lookup)
    GeocodeRequest,
    GeocodingResponse,
    GeocodingStatus,
    ZipCodeRequest,
    ZipCodeInfo,
    ZipCodeResponse,
    LocationType,
    Place,
    # New Places API models
    NearbySearchNewRequest,
    TextSearchNewRequest,
    LocationRestriction,
    Circle,
    NearbySearchNewResponse,
    TextSearchNewResponse,
    PlaceDetailsNewResponse,
)
# Import additional New Places API models
from models.requests_new import (
    PlaceDetailsNewRequest,
    PlacePhotoNewRequest,
)
from models.responses_new import (
    PlacePhotoNewResponse,
)

logger = logging.getLogger(__name__)


class GooglePlacesAPIError(HTTPException):
    """Custom exception for Google Places API errors."""

    def __init__(self, status_code: int, message: str, places_status: Optional[str] = None):
        super().__init__(status_code=status_code, detail=message)
        self.places_status = places_status


class GooglePlacesClient:
    """
    Client for interacting with Google Places API.
    Implements the official Google Maps Places API specification.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the Google Places API client."""
        self.settings = get_settings()
        self.api_key = api_key or self.settings.google_maps_api_key
        self.base_url = base_url or self.settings.google_maps_base_url

        self.client = httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        if not self.api_key:
            raise ValueError("Google Maps API key is required")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def _build_params(self, request_data: Dict[str, Any]) -> Dict[str, str]:
        """Build query parameters for API request."""
        params = {"key": self.api_key}

        for key, value in request_data.items():
            if value is not None:
                if isinstance(value, bool):
                    params[key] = str(value).lower()
                elif isinstance(value, (int, float)):
                    params[key] = str(value)
                elif hasattr(value, 'value'):  # Handle enum types
                    params[key] = str(value.value)
                elif isinstance(value, list):
                    # Handle lists like 'components' which need to be pipe-separated
                    params[key] = '|'.join(str(item) for item in value)
                else:
                    params[key] = str(value)

        return params

    # Legacy methods removed - using only New Places API

    async def geocode(self, request: GeocodeRequest) -> GeocodingResponse:
        """
        Perform geocoding using the Google Geocoding API.

        Args:
            request: The geocoding request parameters

        Returns:
            GeocodingResponse: The API response with geocoding data

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = self._build_params(request.model_dump(exclude_none=True))

        logger.info(f"Making geocoding request to {url}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            response_data = response.json()
            logger.info(f"Geocoding API response status: {response_data.get('status')}")

            # Handle API-level errors for geocoding
            status = response_data.get("status", "UNKNOWN_ERROR")
            if status not in [GeocodingStatus.OK, GeocodingStatus.ZERO_RESULTS]:
                error_message = response_data.get("error_message", f"Geocoding API returned status: {status}")

                # Map Geocoding API status codes to HTTP status codes
                status_code_map = {
                    GeocodingStatus.INVALID_REQUEST: 400,
                    GeocodingStatus.OVER_DAILY_LIMIT: 429,
                    GeocodingStatus.OVER_QUERY_LIMIT: 429,
                    GeocodingStatus.REQUEST_DENIED: 403,
                    GeocodingStatus.UNKNOWN_ERROR: 500,
                }

                http_status = status_code_map.get(status, 500)
                logger.error(f"Geocoding API error: {status} - {error_message}")
                raise GooglePlacesAPIError(
                    status_code=http_status,
                    message=error_message,
                    places_status=status
                )

            # Parse and return the response
            return GeocodingResponse(**response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during geocoding: {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during geocoding: {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    async def lookup_zip_code(self, request: ZipCodeRequest) -> ZipCodeResponse:
        """
        Look up zip code information using the Google Geocoding API.

        Args:
            request: The zip code request parameters

        Returns:
            ZipCodeResponse: Simplified zip code information

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        try:
            # Create geocoding request for zip code lookup
            geocode_request = GeocodeRequest(
                components=[f"postal_code:{request.zip_code}", f"country:{request.country}"]
            )
            logger.info(f"Looking up zip code: {request.zip_code} in country: {request.country}")

            # Make the geocoding request
            geocoding_response = await self.geocode(geocode_request)

            if geocoding_response.status == GeocodingStatus.ZERO_RESULTS:
                return ZipCodeResponse(
                    status="not_found",
                    error_message=f"No results found for zip code {request.zip_code}"
                )

            if not geocoding_response.results:
                return ZipCodeResponse(
                    status="error",
                    error_message="No geocoding results returned"
                )

            # Use the first result (most relevant)
            result = geocoding_response.results[0]

            # Extract address components
            city = None
            state = None
            state_full = None
            country = None
            country_code = None
            zip_code_found = None

            for component in result.address_components:
                if "locality" in component.types:
                    city = component.long_name
                elif "administrative_area_level_1" in component.types:
                    state = component.short_name
                    state_full = component.long_name
                elif "country" in component.types:
                    country = component.long_name
                    country_code = component.short_name
                elif "postal_code" in component.types:
                    zip_code_found = component.long_name

            # Create simplified response
            zip_info = ZipCodeInfo(
                zip_code=zip_code_found or request.zip_code,
                city=city,
                state=state,
                state_full=state_full,
                country=country,
                country_code=country_code,
                latitude=result.geometry.location.lat,
                longitude=result.geometry.location.lng,
                location_type=result.geometry.location_type,
                formatted_address=result.formatted_address,
                place_id=result.place_id
            )

            return ZipCodeResponse(
                status="ok",
                zip_code=zip_info.zip_code,
                city=zip_info.city,
                state=zip_info.state,
                state_full=zip_info.state_full,
                country=zip_info.country,
                country_code=zip_info.country_code,
                latitude=zip_info.latitude,
                longitude=zip_info.longitude,
                location_type=zip_info.location_type,
                formatted_address=zip_info.formatted_address,
                place_id=zip_info.place_id
            )

        except GooglePlacesAPIError:
            # Re-raise API errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during zip code lookup: {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    # New Places API Methods

    async def place_details_new(self, place_id: str, request: PlaceDetailsNewRequest) -> Place:
        """
        Get place details using the New Places API.

        Args:
            place_id: The place ID to get details for
            request: Request parameters including fields to return

        Returns:
            Place: The place details

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        
        # Build field mask
        fields_param = ",".join(request.fields)
        params = {"fields": fields_param, "key": self.api_key}
        
        if request.language_code:
            params["languageCode"] = request.language_code
        if request.region_code:
            params["regionCode"] = request.region_code
        if request.session_token:
            params["sessionToken"] = request.session_token

        logger.info(f"Making Place Details (New) request to {url}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Place Details (New) response received")

            # Parse and return the place
            return Place(**response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during place details (new): {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during place details (new): {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during place details (new): {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    async def nearby_search_new(self, request: NearbySearchNewRequest) -> NearbySearchNewResponse:
        """
        Perform a nearby search using the New Places API.

        Args:
            request: The nearby search request parameters

        Returns:
            NearbySearchNewResponse: The API response with places data

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = "https://places.googleapis.com/v1/places:searchNearby"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(request.fields)
        }
        
        # Build request body
        body = request.model_dump(exclude_none=True, exclude={"fields"})

        logger.info(f"Making Nearby Search (New) request to {url}")
        logger.debug(f"Request body: {body}")

        try:
            response = await self.client.post(url, json=body, headers=headers)
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Nearby Search (New) response received with {len(response_data.get('places', []))} places")

            # Parse and return the response
            return NearbySearchNewResponse(**response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during nearby search (new): {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during nearby search (new): {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during nearby search (new): {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    async def text_search_new(self, request: TextSearchNewRequest) -> TextSearchNewResponse:
        """
        Perform a text search using the New Places API.

        Args:
            request: The text search request parameters

        Returns:
            TextSearchNewResponse: The API response with places data

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = "https://places.googleapis.com/v1/places:searchText"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(request.fields)
        }
        
        # Build request body
        body = request.model_dump(exclude_none=True, exclude={"fields"})

        logger.info(f"Making Text Search (New) request to {url}")
        logger.debug(f"Request body: {body}")

        try:
            response = await self.client.post(url, json=body, headers=headers)
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Text Search (New) response received with {len(response_data.get('places', []))} places")

            # Parse and return the response
            return TextSearchNewResponse(**response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during text search (new): {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during text search (new): {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during text search (new): {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    async def place_photo_new(self, photo_name: str, request: PlacePhotoNewRequest) -> bytes:
        """
        Get a place photo using the New Places API.

        Args:
            photo_name: The photo resource name
            request: Photo request parameters

        Returns:
            bytes: The photo image data

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = f"https://places.googleapis.com/v1/{photo_name}/media"
        
        params = {"key": self.api_key}
        if request.max_width_px:
            params["maxWidthPx"] = str(request.max_width_px)
        if request.max_height_px:
            params["maxHeightPx"] = str(request.max_height_px)
        if request.skip_http_redirect:
            params["skipHttpRedirect"] = str(request.skip_http_redirect).lower()

        logger.info(f"Making Place Photo (New) request to {url}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            logger.debug(f"Place Photo (New) response received, content-type: {response.headers.get('content-type')}")

            # Return the image data
            return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during place photo (new): {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during place photo (new): {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during place photo (new): {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    async def health_check(self) -> bool:
        """
        Perform a health check by making a simple geocoding request.

        Returns:
            bool: True if the API is accessible, False otherwise
        """
        try:
            # Make a simple geocoding request to check API connectivity
            # Use a well-known address that should always work
            test_request = GeocodeRequest(
                address="New York, NY, USA"
            )
            
            # Just check if we can reach the geocoding service
            response = await self.geocode(test_request)
            
            # If we get here without exception, the service is accessible
            return True

        except GooglePlacesAPIError as e:
            # API errors (403, 429) mean the service is reachable but may have auth/quota issues
            # These still indicate the service is "healthy" from a connectivity standpoint
            if e.status_code in [403, 429]:
                return True
            logger.error(f"Health check failed with API error: {e.detail}")
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
