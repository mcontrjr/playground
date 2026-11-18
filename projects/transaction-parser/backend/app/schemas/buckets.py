"""Pydantic v2 schemas for bucket CRUD."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BucketRead(BaseModel):
    """A category bucket, with how many categories currently belong to it."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{"id": 1, "name": "ESSENTIALS", "category_count": 9}]
        },
    )

    id: int
    name: str
    category_count: int


class BucketCreate(BaseModel):
    """Request body to create a new bucket. The name is stripped and
    uppercased server-side regardless of casing in the request."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Hobbies"}]})

    name: str = Field(min_length=1, max_length=64)


class BucketUpdate(BaseModel):
    """Request body to rename a bucket. OTHER cannot be renamed."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Hobbies & Fun"}]})

    name: str = Field(min_length=1, max_length=64)


class BucketDeleteResult(BaseModel):
    """Result of deleting a bucket: its categories are reassigned to
    another bucket (defaulting to OTHER when none is specified)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"moved_category_count": 3, "reassigned_to_bucket_id": 6}]
        }
    )

    moved_category_count: int = Field(
        description="Number of categories moved off the deleted bucket."
    )
    reassigned_to_bucket_id: int = Field(
        description="Bucket those categories now belong to."
    )
