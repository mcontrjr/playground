"""
User model for the Google Places API backend.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """Model for creating a new user."""
    phone_number: str = Field(
        ..., 
        description="User's phone number",
        example="+1234567890"
    )
    starred_categories: Optional[List[str]] = Field(
        default_factory=list,
        description="List of starred place categories/types",
        example=["restaurant", "cafe", "gym"]
    )

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        """Basic phone number validation."""
        # Remove common formatting characters
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        
        # Basic validation - should start with + and have 10-15 digits
        if not cleaned.startswith('+'):
            raise ValueError('Phone number must start with country code (+)')
        
        digits_only = cleaned[1:]  # Remove the +
        if not (10 <= len(digits_only) <= 15):
            raise ValueError('Phone number must have 10-15 digits after country code')
        
        return cleaned


class UserUpdate(BaseModel):
    """Model for updating an existing user."""
    phone_number: Optional[str] = Field(
        None, 
        description="User's phone number",
        example="+1234567890"
    )
    starred_categories: Optional[List[str]] = Field(
        None,
        description="List of starred place categories/types",
        example=["restaurant", "cafe", "gym"]
    )
    cached_recommendations: Optional[List[str]] = Field(
        None,
        description="List of cached place IDs for recommendations",
        example=["ChIJN1t_tDeuEmsRUsoyG83frY4"]
    )
    bookmarks: Optional[List[str]] = Field(
        None,
        description="List of bookmarked place IDs",
        example=["ChIJN1t_tDeuEmsRUsoyG83frY4"]
    )

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        """Basic phone number validation."""
        if v is None:
            return v
            
        # Remove common formatting characters
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        
        # Basic validation - should start with + and have 10-15 digits
        if not cleaned.startswith('+'):
            raise ValueError('Phone number must start with country code (+)')
        
        digits_only = cleaned[1:]  # Remove the +
        if not (10 <= len(digits_only) <= 15):
            raise ValueError('Phone number must have 10-15 digits after country code')
        
        return cleaned


class User(BaseModel):
    """Complete user model."""
    id: str = Field(
        ...,
        description="Unique user identifier (UUID)",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    phone_number: str = Field(
        ..., 
        description="User's phone number",
        example="+1234567890"
    )
    starred_categories: List[str] = Field(
        default_factory=list,
        description="List of starred place categories/types",
        example=["restaurant", "cafe", "gym"]
    )
    cached_recommendations: List[str] = Field(
        default_factory=list,
        description="List of cached place IDs for recommendations",
        example=["ChIJN1t_tDeuEmsRUsoyG83frY4"]
    )
    bookmarks: List[str] = Field(
        default_factory=list,
        description="List of bookmarked place IDs",
        example=["ChIJN1t_tDeuEmsRUsoyG83frY4"]
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Timestamp when user was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when user was last updated"
    )

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        """Basic phone number validation."""
        # Remove common formatting characters
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        
        # Basic validation - should start with + and have 10-15 digits
        if not cleaned.startswith('+'):
            raise ValueError('Phone number must start with country code (+)')
        
        digits_only = cleaned[1:]  # Remove the +
        if not (10 <= len(digits_only) <= 15):
            raise ValueError('Phone number must have 10-15 digits after country code')
        
        return cleaned

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "phone_number": "+1234567890",
                "starred_categories": ["restaurant", "cafe", "gym"],
                "cached_recommendations": ["ChIJN1t_tDeuEmsRUsoyG83frY4"],
                "bookmarks": ["ChIJrTLr-GyuEmsRBfy61i59si0"],
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }
    }


class UserResponse(BaseModel):
    """Response model for user operations."""
    user: User
    message: str = "User operation completed successfully"

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "phone_number": "+1234567890",
                    "starred_categories": ["restaurant", "cafe"],
                    "cached_recommendations": [],
                    "bookmarks": [],
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z"
                },
                "message": "User created successfully"
            }
        }
    }


class UserListResponse(BaseModel):
    """Response model for listing users."""
    users: List[User]
    total: int
    limit: int
    offset: int
    message: str = "Users retrieved successfully"

    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "phone_number": "+1234567890",
                        "starred_categories": ["restaurant", "cafe"],
                        "cached_recommendations": [],
                        "bookmarks": [],
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 100,
                "offset": 0,
                "message": "Users retrieved successfully"
            }
        }
    }
