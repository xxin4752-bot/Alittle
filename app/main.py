from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import asyncio

from app.database import engine, Base, get_db
from app import models, schemas, crud, auth, crypto_service

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# --- Pages ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    # In a real app, we would check cookie/token here or handle it in frontend
    # For this simple demo, we rely on frontend JS to check token and redirect if needed
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/console", response_class=HTMLResponse)
async def console_page(request: Request):
    return templates.TemplateResponse("console.html", {"request": request})

# --- API ---

@app.post("/api/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/api/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/api/keys", response_model=schemas.ExchangeKey)
def create_key(key: schemas.ExchangeKeyCreate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return crud.create_exchange_key(db=db, key=key, user_id=current_user.id)

@app.get("/api/keys", response_model=list[schemas.ExchangeKey])
def read_keys(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return crud.get_exchange_keys(db=db, user_id=current_user.id)

@app.get("/api/keys/{key_id}/status")
async def check_key_status(key_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    key = crud.get_exchange_key(db=db, key_id=key_id)
    if not key or key.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Key not found")
    
    try:
        # Simple balance check to verify connection
        # We fetch minimal data to be fast
        await crypto_service.fetch_balance_and_value(key.exchange_name, key.api_key, key.secret_key, key.passphrase)
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/refresh")
async def refresh_portfolio(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    keys = crud.get_exchange_keys(db=db, user_id=current_user.id)
    total_balance = 0.0
    
    # Structure:
    # {
    #   "total_usd": float,
    #   "exchanges": {
    #       "binance": { "total_usd": float, "assets": { ... } },
    #       "okx": { "total_usd": float, "assets": { ... } }
    #   },
    #   "assets_aggregation": { ... }
    # }
    
    exchanges_data = {}
    aggregated_assets = {}

    for key in keys:
        try:
            balance, details = await crypto_service.fetch_balance_and_value(key.exchange_name, key.api_key, key.secret_key, key.passphrase)
            total_balance += balance
            
            # Store per-exchange data
            # Handle multiple keys for same exchange? 
            # For simplicity, if multiple keys exist for same exchange, we merge them or use a list.
            # But usually one key per exchange per user. Let's assume merging if same exchange name.
            
            ex_name = key.exchange_name.lower()
            if ex_name not in exchanges_data:
                exchanges_data[ex_name] = {"total_usd": 0.0, "assets": {}}
            
            exchanges_data[ex_name]["total_usd"] += balance
            
            # Merge assets into exchange specific record
            for asset, info in details.items():
                if asset in exchanges_data[ex_name]["assets"]:
                    exchanges_data[ex_name]["assets"][asset]['amount'] += info['amount']
                    exchanges_data[ex_name]["assets"][asset]['value_usd'] += info['value_usd']
                else:
                    exchanges_data[ex_name]["assets"][asset] = info.copy()

                # Merge into global aggregation
                if asset in aggregated_assets:
                    aggregated_assets[asset]['amount'] += info['amount']
                    aggregated_assets[asset]['value_usd'] += info['value_usd']
                else:
                    aggregated_assets[asset] = info.copy()
                    
        except Exception as e:
            print(f"Error refreshing key {key.id}: {e}")
            continue

    final_details = {
        "exchanges": exchanges_data,
        "assets_aggregation": aggregated_assets
    }

    snapshot_data = schemas.AssetSnapshotBase(total_balance_usd=total_balance, details=final_details)
    crud.create_asset_snapshot(db=db, snapshot=snapshot_data, user_id=current_user.id)
    
    return {"status": "success", "total_balance": total_balance, "details": final_details}

@app.get("/api/history", response_model=list[schemas.AssetSnapshot])
def get_history(limit: int = 100, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return crud.get_asset_snapshots(db=db, user_id=current_user.id, limit=limit)
