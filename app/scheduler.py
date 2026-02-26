from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app import crud, models, crypto_service, schemas
from app.database import SessionLocal
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def update_all_portfolios():
    """
    Background task to update portfolio values for all users.
    """
    logger.info("Starting scheduled portfolio update...")
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(models.User).all()
        
        for user in users:
            keys = crud.get_exchange_keys(db=db, user_id=user.id)
            if not keys:
                continue
                
            logger.info(f"Updating portfolio for user {user.username}")
            
            total_balance = 0.0
            exchanges_data = {}
            aggregated_assets = {}
            
            for key in keys:
                try:
                    balance, details = await crypto_service.fetch_balance_and_value(
                        key.exchange_name, key.api_key, key.secret_key, key.passphrase
                    )
                    total_balance += balance
                    
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
                    logger.error(f"Error fetching data for key {key.id}: {e}")
                    continue
            
            final_details = {
                "exchanges": exchanges_data,
                "assets_aggregation": aggregated_assets
            }
            
            # Create snapshot
            snapshot_data = schemas.AssetSnapshotBase(total_balance_usd=total_balance, details=final_details)
            crud.create_asset_snapshot(db=db, snapshot=snapshot_data, user_id=user.id)
            
        logger.info("Scheduled portfolio update completed.")
        
    except Exception as e:
        logger.error(f"Error in scheduled update: {e}")
    finally:
        db.close()

def start_scheduler():
    # Schedule to run every 1 hour (3600 seconds)
    scheduler.add_job(
        update_all_portfolios, 
        trigger=IntervalTrigger(hours=1), 
        id='portfolio_update_job', 
        replace_existing=True
    )
    if not scheduler.running:
        scheduler.start()
