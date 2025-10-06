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
                        spot_price: float) -> Dict[str, Dict[str, Any]]:
        """
        Find ATM call and put options for given spot price.
        
        Args:
            underlying_asset: "BTCUSD" or "ETHUSD"
            expiry_timestamp: Expiry timestamp
            spot_price: Current spot price
        
        Returns:
            Dictionary with 'call' and 'put' option details
        """
        try:
            options_chain = self.get_options_chain(underlying_asset, expiry_timestamp)
            
            calls = options_chain['calls']
            puts = options_chain['puts']
            
            if not calls or not puts:
                raise ValueError("No options found for this expiry")
            
            # Find ATM strike (nearest to spot price)
            atm_strike = min(calls, key=lambda x: abs(x['strike_price'] - spot_price))['strike_price']
            
            # Find ATM call and put
            atm_call = next((c for c in calls if c['strike_price'] == atm_strike), None)
            atm_put = next((p for p in puts if p['strike_price'] == atm_strike), None)
            
            if not atm_call or not atm_put:
                raise ValueError(f"Could not find ATM options at strike {atm_strike}")
            
            # Fetch prices for both options
            call_prices = self.get_option_prices(atm_call['product_id'])
            put_prices = self.get_option_prices(atm_put['product_id'])
            
            result = {
                'atm_strike': atm_strike,
                'call': {**atm_call, **call_prices},
                'put': {**atm_put, **put_prices}
            }
            
            logger.info(f"Found ATM options at strike {atm_strike}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to find ATM options: {e}")
            raise
          
