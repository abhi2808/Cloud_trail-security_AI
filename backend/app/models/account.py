from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class AccountCreate(BaseModel):
    nickname: str = Field(..., max_length=30)
    region: str = Field(default="us-east-1")
    access_key_id: str = Field(..., min_length=20, max_length=20)
    secret_access_key: str = Field(..., min_length=40)

    @field_validator('access_key_id')
    @classmethod
    def validate_access_key(cls, v: str):
        if not (v.startswith("AKIA") or v.startswith("ASIA")):
            raise ValueError("Access Key ID must start with AKIA or ASIA")
        return v

class AccountResponse(BaseModel):
    id: str
    nickname: str
    region: str
    created_at: datetime
    last_verified: Optional[datetime] = None

class AccountTestResult(BaseModel):
    success: bool
    message: str
    account_id: Optional[str] = None
