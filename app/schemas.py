"""Request / response models for the HTTP API."""

from datetime import datetime, timezone
from pydantic import BaseModel , Field, field_validator
from .validation import validate_alias, validate_url

class CreateLinkRequest(BaseModel):
    url:str = Field(description = "The long URL to shorten (http or https).")
    alias: str | None = Field(
        default=None,
        description = "Optional custom code, 3-32 chars of letters,digits,'-' or '_'.",  
    )
    expires_at: datetime | None=Field(
        default = None,
        description = "Optional ISO-8601 expiry. Times without a UTC offset are treated as UTC.",
    )

    @field_validator("url")
    @classmethod
    def _check_url(cls,v:str)->str:
        return validate_url(v)

    @field_validator("alias")
    @classmethod
    def _check_alias(cls, v:str| None)->str|None:
        return None if v is None else validate_alias(v)

    @field_validator("expires_at")
    @classmethod
    def _assume_utc(cls,v:datetime | None)->datetime| None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class LinkResponse(BaseModel):
        code:str
        short_url:str
        original_url: str
        created_at:datetime
        expires_at: datetime | None

class LinkStatsResponse(BaseModel):
        code:str
        original_url: str
        total_clicks: int
        last_clicked_at: datetime|None
        created_at:datetime
        expires_at:datetime | None
        is_expired:bool


class ErrorDetail(BaseModel):
    field: str
    message:str

class ErrorResponse(BaseModel):
    error:str = Field(description = "Stable machine-readable error code.")
    message: str = Field(description = "Human-readable explanation.")
    details: list[ErrorDetail] | None = None