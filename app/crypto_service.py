import ccxt.async_support as ccxt
import asyncio

async def fetch_balance_and_value(exchange_id: str, api_key: str, secret: str, passphrase: str = None):
    exchange_class = getattr(ccxt, exchange_id)
    config = {
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
    }
    
    # OKX requires a password (passphrase)
    if exchange_id.lower() == 'okx' and passphrase:
        config['password'] = passphrase
        
    exchange = exchange_class(config)

    total_usd_value = 0.0
    asset_details = {}

    try:
        # Load markets to get price data capabilities
        # await exchange.load_markets() 
        # For simplicity, we might just fetch balance and then prices for held assets
        
        balance = await exchange.fetch_balance()
        
        # Filter for non-zero assets
        non_zero_assets = {k: v for k, v in balance['total'].items() if v > 0}
        
        if not non_zero_assets:
            await exchange.close()
            return 0.0, {}

        # Fetch tickers for all relevant symbols to get USD price
        # Note: This is a simplified approach. In production, need to handle stablecoins (USDT, USDC) = 1 USD
        # and find XXX/USDT pairs.
        
        for symbol, amount in non_zero_assets.items():
            usd_value = 0.0
            if symbol in ['USDT', 'USDC', 'DAI', 'BUSD', 'USD']:
                usd_value = amount
            else:
                try:
                    # Try to find a USDT pair
                    ticker = await exchange.fetch_ticker(f"{symbol}/USDT")
                    price = ticker['last']
                    usd_value = amount * price
                except Exception:
                    # Fallback or ignore if no USDT pair
                    # Try USDC
                     try:
                        ticker = await exchange.fetch_ticker(f"{symbol}/USDC")
                        price = ticker['last']
                        usd_value = amount * price
                     except:
                         pass

            total_usd_value += usd_value
            asset_details[symbol] = {
                'amount': amount,
                'value_usd': usd_value
            }

    except Exception as e:
        print(f"Error fetching data from {exchange_id}: {e}")
        raise e
    finally:
        await exchange.close()

    return total_usd_value, asset_details
