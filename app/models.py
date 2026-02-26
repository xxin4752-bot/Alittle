from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    keys = relationship("ExchangeKey", back_populates="owner")
    snapshots = relationship("AssetSnapshot", back_populates="owner")

class ExchangeKey(Base):
    __tablename__ = "exchange_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exchange_name = Column(String) # binance, okx
    api_key = Column(String)
    secret_key = Column(String)
    passphrase = Column(String, nullable=True) # Added for OKX
    # Consider encrypting secret_key in a real app, storing plain text for simplicity in this demo

    owner = relationship("User", back_populates="keys")

class AssetSnapshot(Base):
    __tablename__ = "asset_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_balance_usd = Column(Float)
    details = Column(JSON) # Store breakdown like {"BTC": 0.5, "ETH": 10}

    owner = relationship("User", back_populates="snapshots")
