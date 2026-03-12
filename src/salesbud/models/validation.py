"""
Pydantic validation models for SalesBud CLI input validation.
All CLI commands use these to validate inputs before processing.
"""

import re
from typing import Optional

from pydantic import BaseModel, field_validator


def _valid_email(v: str) -> str:
    """Basic RFC-5322-style email validation."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, v.strip()):
        raise ValueError(f"'{v}' is not a valid email address")
    return v.strip().lower()


def _valid_url(v: str) -> str:
    """Ensure URL starts with http(s):// and has a real domain."""
    v = v.strip()
    if not v.startswith(("http://", "https://")):
        v = "https://" + v
    # Must have scheme + domain (something.tld) with no spaces
    if not re.match(r"^https?://[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/\S*)?$", v):
        raise ValueError(f"'{v}' is not a valid URL")
    return v


class AddEmailInput(BaseModel):
    lead_id: int
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _valid_email(v)

    @field_validator("lead_id")
    @classmethod
    def validate_lead_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("lead_id must be a positive integer")
        return v


class SendEmailInput(BaseModel):
    to: str
    subject: str
    body: str

    @field_validator("to")
    @classmethod
    def validate_to(cls, v: str) -> str:
        return _valid_email(v)

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("subject cannot be empty")
        return v.strip()

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("body cannot be empty")
        return v.strip()


class SetCompanyUrlInput(BaseModel):
    lead_id: int
    company_url: str

    @field_validator("lead_id")
    @classmethod
    def validate_lead_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("lead_id must be a positive integer")
        return v

    @field_validator("company_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        return _valid_url(v)


class ScrapeInput(BaseModel):
    query: str
    location: Optional[str] = None
    max: int = 50

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query cannot be empty")
        return v.strip()

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: int) -> int:
        if v < 1 or v > 500:
            raise ValueError("max must be between 1 and 500")
        return v


class ConnectInput(BaseModel):
    max: int = 10
    delay: int = 60

    @field_validator("max")
    @classmethod
    def validate_max(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("max must be between 1 and 100")
        return v

    @field_validator("delay")
    @classmethod
    def validate_delay(cls, v: int) -> int:
        if v < 0:
            raise ValueError("delay must be non-negative")
        return v
