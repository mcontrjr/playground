"""
Configuration management for the FastAPI backend.
"""
import os
from typing import Optional
from functools import lru_cache
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Maps API configuration
    google_maps_api_key: str = Field(..., env="GOOGLE_MAPS_API_KEY")
    google_maps_base_url: str = Field(
        "https://maps.googleapis.com/maps/api/place",
        env="GOOGLE_MAPS_BASE_URL"
    )
    
    # API configuration
    api_title: str = Field("Google Places API Backend", env="API_TITLE")
    api_description: str = Field(
        "FastAPI backend for Google Maps Places API integration", 
        env="API_DESCRIPTION"
    )
    api_version: str = Field("1.0.0", env="API_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # Server configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Request configuration
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Convenience function to get the current settings
def get_google_maps_api_key() -> str:
    """Get the Google Maps API key."""
    return get_settings().google_maps_api_key


def get_google_maps_base_url() -> str:
    """Get the Google Maps API base URL."""
    return get_settings().google_maps_base_url
