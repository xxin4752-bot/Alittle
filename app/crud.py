from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
import json

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_exchange_key(db: Session, key: schemas.ExchangeKeyCreate, user_id: int):
    # Check if key already exists for this exchange (optional logic, allowing multiple for now)
    db_key = models.ExchangeKey(**key.dict(), user_id=user_id)
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

def get_exchange_keys(db: Session, user_id: int):
    return db.query(models.ExchangeKey).filter(models.ExchangeKey.user_id == user_id).all()

def get_exchange_key(db: Session, key_id: int):
    return db.query(models.ExchangeKey).filter(models.ExchangeKey.id == key_id).first()

def create_asset_snapshot(db: Session, snapshot: schemas.AssetSnapshotBase, user_id: int):
    db_snapshot = models.AssetSnapshot(
        user_id=user_id,
        total_balance_usd=snapshot.total_balance_usd,
        details=snapshot.details
    )
    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot

def get_asset_snapshots(db: Session, user_id: int, limit: int = 100):
    return db.query(models.AssetSnapshot).filter(models.AssetSnapshot.user_id == user_id).order_by(models.AssetSnapshot.timestamp.asc()).limit(limit).all()

def get_latest_asset_snapshot(db: Session, user_id: int):
    return db.query(models.AssetSnapshot).filter(models.AssetSnapshot.user_id == user_id).order_by(models.AssetSnapshot.timestamp.desc()).first()
