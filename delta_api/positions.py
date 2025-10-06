"""Position management API."""
import logging
from typing import Dict, Any, List, Optional

from delta_api.client import DeltaClient

logger = logging.getLogger(__name__)

class PositionAPI:
    """Handles position-related API calls."""
    
    def __init__(self, client: DeltaClient):
        """
        Initialize Position API.
        
        Args:
            client: Delta Exchange API client
        """
        self.client = client
    
    def get_positions(self, product_id: Optional[int] = None, 
                     underlying_asset: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        According to Delta Exchange API docs, you must provide either:
        - product_id: Specific product ID
        - underlying_asset_symbol: Like "BTC" or "ETH"
        
        Args:
            product_id: Optional product ID to filter by
            underlying_asset: Optional underlying asset symbol (BTC, ETH)
        
        Returns:
            List of position dictionaries
        """
        try:
            # Build query parameters
            params = {}
            
            if product_id:
                params['product_id'] = product_id
            elif underlying_asset:
                params['underlying_asset_symbol'] = underlying_asset
            else:
                # If no filter provided, get all positions for BTC and ETH
                # We'll call the API twice and combine results
                btc_positions = self.get_positions(underlying_asset='BTC')
                eth_positions = self.get_positions(underlying_asset='ETH')
                return btc_positions + eth_positions
            
            response = self.client.get('/v2/positions', params=params)
            
            if 'result' in response:
                positions = response['result']
                logger.info(f"Fetched {len(positions)} positions")
                return positions
            
            logger.warning("No positions found in response")
            return []
        
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}", exc_info=True)
            raise
    
    def get_position_by_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get position for specific product.
        
        Args:
            product_id: Product ID
        
        Returns:
            Position dictionary or None
        """
        try:
            positions = self.get_positions(product_id=product_id)
            return positions[0] if positions else None
        
        except Exception as e:
            logger.error(f"Failed to fetch position for product {product_id}: {e}")
            return None
    
    def close_position(self, product_id: int, close_on_trigger: bool = False) -> Dict[str, Any]:
        """
        Close position for specific product.
        
        Args:
            product_id: Product ID
            close_on_trigger: Whether to close on trigger
        
        Returns:
            Response dictionary
        """
        try:
            data = {
                'product_id': product_id,
                'close_on_trigger': close_on_trigger
            }
            
            response = self.client.post('/v2/positions/close_all', data=data)
            logger.info(f"Closed position for product {product_id}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to close position: {e}", exc_info=True)
            raise
            
