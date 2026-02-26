from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True

class ExchangeKeyBase(BaseModel):
    exchange_name: str
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None # Added for OKX

class ExchangeKeyCreate(ExchangeKeyBase):
    pass

class ExchangeKey(ExchangeKeyBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class AssetSnapshotBase(BaseModel):
    total_balance_usd: float
    details: Dict[str, Any]

class AssetSnapshot(AssetSnapshotBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
