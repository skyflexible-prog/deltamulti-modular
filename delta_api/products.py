"""Products and tickers API operations."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from config.constants import CONTRACT_TYPE_CALL, CONTRACT_TYPE_PUT, UNDERLYING_SYMBOLS

logger = logging.getLogger(__name__)

class ProductAPI:
    """Handles product and ticker operations."""
    
    def __init__(self, client):
        self.client = client
        self._product_cache = {}
        self._cache_timestamp = {}
    
    def get_products(self, contract_types: Optional[str] = None, 
                    underlying_asset: Optional[str] = None,
                    states: str = "live") -> Dict[str, Any]:
        """
        Get products with optional filters.
        
        Args:
            contract_types: Comma-separated contract types (e.g., "call_options,put_options")
            underlying_asset: Underlying asset symbol (e.g., "BTC", "ETH")
            states: Product states (default: "live")
        
        Returns:
            Products response dictionary
        """
        try:
            params = {'states': states}
            
            if contract_types:
                params['contract_types'] = contract_types
            
            if underlying_asset:
                params['underlying_asset_symbols'] = underlying_asset
            
            response = self.client.get('/v2/products', params=params)
            logger.info(f"Fetched products with filters: {params}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            raise
    
    def get_spot_price(self, symbol: str) -> float:
        """
        Get current spot price for underlying asset.
        
        Args:
            symbol: Symbol like "BTCUSD" or "ETHUSD"
        
        Returns:
            Current spot price as float
        """
        try:
            response = self.client.get(f'/v2/tickers/{symbol}')
            
            if 'result' in response:
                spot_price = float(response['result'].get('spot_price', 0))
                logger.info(f"Spot price for {symbol}: {spot_price}")
                return spot_price
            
            raise ValueError(f"Invalid response format for ticker {symbol}")
        
        except Exception as e:
            logger.error(f"Failed to fetch spot price for {symbol}: {e}")
            raise
    
    def get_tickers(self, contract_types: Optional[str] = None,
                   underlying_asset: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tickers with optional filters.
        
        Args:
            contract_types: Contract types filter
            underlying_asset: Underlying asset symbol
        
        Returns:
            Tickers response dictionary
        """
        try:
            params = {}
            
            if contract_types:
                params['contract_types'] = contract_types
            
            if underlying_asset:
                params['underlying_asset_symbols'] = underlying_asset
            
            response = self.client.get('/v2/tickers', params=params)
            logger.info(f"Fetched tickers with filters: {params}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            raise
    
    def get_available_expiries(self, underlying_asset: str) -> List[Dict[str, Any]]:
        """
        Get all available expiry dates for options on underlying asset.
        
        Args:
            underlying_asset: "BTCUSD" or "ETHUSD"
        
        Returns:
            List of expiry dictionaries sorted by date (ascending)
        """
        try:
            underlying_symbol = UNDERLYING_SYMBOLS.get(underlying_asset)
            if not underlying_symbol:
                raise ValueError(f"Invalid underlying asset: {underlying_asset}")
            
            # Fetch all options products
            response = self.get_products(
                contract_types=f"{CONTRACT_TYPE_CALL},{CONTRACT_TYPE_PUT}",
                underlying_asset=underlying_symbol
            )
            
            # Extract unique expiries
            expiries = {}
            if 'result' in response:
                for product in response['result']:
                    settlement_time = product.get('settlement_time')
                    if settlement_time:
                        # settlement_time is in ISO 8601 format like "2025-10-24T04:00:00Z"
                        # Convert to datetime object
                        try:
                            if isinstance(settlement_time, str):
                                # Parse ISO 8601 format
                                dt = datetime.fromisoformat(settlement_time.replace('Z', '+00:00'))
                                timestamp = int(dt.timestamp())
                            else:
                                # Already a timestamp
                                timestamp = int(settlement_time)
                                dt = datetime.fromtimestamp(timestamp)
                        
                            if timestamp not in expiries:
                                expiries[timestamp] = {
                                    'timestamp': timestamp,
                                    'datetime': dt
                            }
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to parse settlement_time: {settlement_time}, error: {e}")
                            continue
                        
            # Sort by timestamp (ascending)
            sorted_expiries = sorted(expiries.values(), key=lambda x: x['timestamp'])
            
            logger.info(f"Found {len(sorted_expiries)} expiries for {underlying_asset}")
            return sorted_expiries
        
        except Exception as e:
            logger.error(f"Failed to fetch expiries for {underlying_asset}: {e}")
            raise
    
    def get_options_chain(self, underlying_asset: str, 
                         expiry_timestamp: int) -> Dict[str, List[Dict]]:
        """
        Get options chain (all calls and puts) for specific expiry.
        
        Args:
            underlying_asset: "BTCUSD" or "ETHUSD"
            expiry_timestamp: Unix timestamp of expiry
        
        Returns:
            Dictionary with 'calls' and 'puts' lists
        """
        try:
            underlying_symbol = UNDERLYING_SYMBOLS.get(underlying_asset)
            if not underlying_symbol:
                raise ValueError(f"Invalid underlying asset: {underlying_asset}")
            
            # Fetch all options products for this underlying
            response = self.get_products(
                contract_types=f"{CONTRACT_TYPE_CALL},{CONTRACT_TYPE_PUT}",
                underlying_asset=underlying_symbol
            )
            
            calls = []
            puts = []
            
            if 'result' in response:
                for product in response['result']:
                    # Filter by expiry
                    if product.get('settlement_time') == expiry_timestamp:
                        option_data = {
                            'symbol': product.get('symbol'),
                            'product_id': product.get('id'),
                            'strike_price': float(product.get('strike_price', 0)),
                            'contract_type': product.get('contract_type')
                        }
                        
                        if product.get('contract_type') == CONTRACT_TYPE_CALL:
                            calls.append(option_data)
                        elif product.get('contract_type') == CONTRACT_TYPE_PUT:
                            puts.append(option_data)
            
            # Sort by strike price
            calls.sort(key=lambda x: x['strike_price'])
            puts.sort(key=lambda x: x['strike_price'])
            
            logger.info(f"Options chain: {len(calls)} calls, {len(puts)} puts")
            return {'calls': calls, 'puts': puts}
        
        except Exception as e:
            logger.error(f"Failed to fetch options chain: {e}")
            raise
    
    def get_option_prices(self, product_id: int) -> Dict[str, Any]:
        """
        Get current prices for specific option product.
        
        Args:
            product_id: Product ID
        
        Returns:
            Price information dictionary
        """
        try:
            # Fetch all tickers and find matching product
            response = self.get_tickers()
            
            if 'result' in response:
                for ticker in response['result']:
                    if ticker.get('product_id') == product_id:
                        return {
                            'mark_price': float(ticker.get('mark_price', 0)),
                            'best_bid': float(ticker.get('quotes', {}).get('best_bid', 0)),
                            'best_ask': float(ticker.get('quotes', {}).get('best_ask', 0)),
                            'last_price': float(ticker.get('close', 0))
                        }
            
            raise ValueError(f"Product ID {product_id} not found in tickers")
        
        except Exception as e:
            logger.error(f"Failed to fetch option prices for product {product_id}: {e}")
            raise
    
    def find_atm_options(self, underlying_asset: str, expiry_timestamp: int, 
                    spot_price: float) -> Dict[str, Any]:
        """
        Find ATM call and put options for given expiry.
    
        Args:
            underlying_asset: "BTCUSD" or "ETHUSD"
            expiry_timestamp: Unix timestamp of expiry
            spot_price: Current spot price
        
        Returns:
            Dictionary with ATM strike, call and put option details
        """
        try:
            underlying_symbol = UNDERLYING_SYMBOLS.get(underlying_asset)
            if not underlying_symbol:
                raise ValueError(f"Invalid underlying asset: {underlying_asset}")
        
            # Fetch all options products
            response = self.get_products(
                contract_types=f"{CONTRACT_TYPE_CALL},{CONTRACT_TYPE_PUT}",
                underlying_asset=underlying_symbol
            )
        
            if 'result' not in response:
                raise ValueError("Invalid API response")
        
            # Parse expiry datetime from timestamp
            from datetime import datetime, timezone
            expiry_dt = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
            logger.info(f"Looking for options with expiry: {expiry_dt.isoformat()}")
        
            # Filter options for this expiry (with tolerance for time matching)
            calls = []
            puts = []
        
            for product in response['result']:
                settlement_time_str = product.get('settlement_time')
                if not settlement_time_str:
                    continue
            
                try:
                    # Parse settlement time from ISO format
                    product_expiry_dt = datetime.fromisoformat(settlement_time_str.replace('Z', '+00:00'))
                
                    # Check if expiry dates match (compare year, month, day, hour)
                    # Allow some tolerance since timestamps might differ slightly
                    if (product_expiry_dt.year == expiry_dt.year and
                        product_expiry_dt.month == expiry_dt.month and
                        product_expiry_dt.day == expiry_dt.day and
                        product_expiry_dt.hour == expiry_dt.hour):
                    
                        contract_type = product.get('contract_type')
                        strike = float(product.get('strike_price', 0))
                       
                        # Extract prices correctly from product data
                        # Delta Exchange returns mark_price, quotes for bid/ask
                        mark_price = float(product.get('mark_price', 0))
                    
                        # Get bid/ask from quotes if available
                        quotes = product.get('quotes', {})
                        if isinstance(quotes, dict):
                            best_bid = float(quotes.get('best_bid', 0))
                            best_ask = float(quotes.get('best_ask', 0))
                        else:
                            best_bid = 0
                            best_ask = 0
                    
                        option_data = {
                            'product_id': product.get('id'),
                            'symbol': product.get('symbol'),
                            'strike': strike,
                            'mark_price': mark_price,
                            'bid': best_bid,
                            'ask': best_ask
                        }
                        
                        if contract_type == CONTRACT_TYPE_CALL:
                            calls.append(option_data)
                        elif contract_type == CONTRACT_TYPE_PUT:
                            puts.append(option_data)
            
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse settlement time for product {product.get('symbol')}: {e}")
                    continue
        
            logger.info(f"Options chain: {len(calls)} calls, {len(puts)} puts")
        
            if not calls or not puts:
                raise ValueError("No options found for this expiry")
        
            # Find ATM strike (closest to spot price)
            all_strikes = sorted(set([opt['strike'] for opt in calls]))
            atm_strike = min(all_strikes, key=lambda x: abs(x - spot_price))
        
            logger.info(f"ATM strike: {atm_strike} (spot: {spot_price})")
        
            # Get ATM call and put
            atm_call = next((opt for opt in calls if opt['strike'] == atm_strike), None)
            atm_put = next((opt for opt in puts if opt['strike'] == atm_strike), None)
        
            if not atm_call or not atm_put:
                raise ValueError(f"ATM options not found for strike {atm_strike}")
        
            return {
                'strike': atm_strike,
                'spot_price': spot_price,
                'call': atm_call,
                'put': atm_put
            }
    
        except Exception as e:
            logger.error(f"Failed to find ATM options: {e}", exc_info=True)
            raise
