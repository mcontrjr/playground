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
    NearbySearchRequest,
    TextSearchRequest,
    PlacesNearbySearchResponse,
    PlacesTextSearchResponse,
    PlacesSearchStatus,
    GeocodeRequest,
    GeocodingResponse,
    GeocodingStatus,
    ZipCodeRequest,
    ZipCodeInfo,
    ZipCodeResponse,
    LocationType,
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

    def _handle_api_response(self, response_data: Dict[str, Any]) -> None:
        """Handle API response and raise appropriate exceptions for errors."""
        status = response_data.get("status", "UNKNOWN_ERROR")

        if status == PlacesSearchStatus.OK:
            return

        error_message = response_data.get("error_message", f"API returned status: {status}")

        # Map Places API status codes to HTTP status codes
        status_code_map = {
            PlacesSearchStatus.ZERO_RESULTS: 200,  # Not an error, just no results
            PlacesSearchStatus.INVALID_REQUEST: 400,
            PlacesSearchStatus.OVER_QUERY_LIMIT: 429,
            PlacesSearchStatus.REQUEST_DENIED: 403,
            PlacesSearchStatus.UNKNOWN_ERROR: 500,
        }

        http_status = status_code_map.get(status, 500)

        if status == PlacesSearchStatus.ZERO_RESULTS:
            # ZERO_RESULTS is not an error, just return without raising
            return

        logger.error(f"Google Places API error: {status} - {error_message}")
        raise GooglePlacesAPIError(
            status_code=http_status,
            message=error_message,
            places_status=status
        )

    async def nearby_search(self, request: NearbySearchRequest) -> PlacesNearbySearchResponse:
        """
        Perform a nearby search using the Google Places API.

        Args:
            request: The nearby search request parameters

        Returns:
            PlacesNearbySearchResponse: The API response with places data

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = f"{self.base_url}/nearbysearch/json"
        params = self._build_params(request.dict(exclude_none=True))

        logger.info(f"Making nearby search request to {url}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"API response status: {response_data.get('status')}")

            # Handle API-level errors
            self._handle_api_response(response_data)

            # Parse and return the response
            return PlacesNearbySearchResponse(**response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during nearby search: {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during nearby search: {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during nearby search: {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

    async def text_search(self, request: TextSearchRequest) -> PlacesTextSearchResponse:
        """
        Perform a text search using the Google Places API.

        Args:
            request: The text search request parameters

        Returns:
            PlacesTextSearchResponse: The API response with places data

        Raises:
            GooglePlacesAPIError: If the API request fails
        """
        url = f"{self.base_url}/textsearch/json"
        params = self._build_params(request.dict(exclude_none=True))

        logger.info(f"Making text search request to {url}")
        logger.debug(f"Request parameters: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"API response status: {response_data.get('status')}")

            # Handle API-level errors
            self._handle_api_response(response_data)

            # Parse and return the response
            return PlacesTextSearchResponse(**response_data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during text search: {e}")
            raise GooglePlacesAPIError(
                status_code=e.response.status_code,
                message=f"HTTP error: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error during text search: {e}")
            raise GooglePlacesAPIError(
                status_code=503,
                message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during text search: {e}")
            raise GooglePlacesAPIError(
                status_code=500,
                message=f"Unexpected error: {str(e)}"
            )

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
        params = self._build_params(request.dict(exclude_none=True))

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

    async def health_check(self) -> bool:
        """
        Perform a health check by making a simple API request.

        Returns:
            bool: True if the API is accessible, False otherwise
        """
        try:
            # Make a simple nearby search request to check API connectivity
            test_request = NearbySearchRequest(
                location="0,0",  # Equator, should be valid
                radius=1000
            )

            # Don't need to process the response, just check if we can reach the API
            url = f"{self.base_url}/nearbysearch/json"
            params = self._build_params(test_request.dict(exclude_none=True))

            response = await self.client.get(url, params=params)

            # Check if we got a response (even if it's an API error, it means we reached the service)
            return response.status_code in [200, 400, 403, 429]  # Valid HTTP responses from the API

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
