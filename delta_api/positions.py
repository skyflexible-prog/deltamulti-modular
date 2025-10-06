"""Positions API operations."""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PositionAPI:
    """Handles position operations."""
    
    def __init__(self, client):
        self.client = client
    
    def get_positions(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Args:
            product_id: Optional product ID to filter positions
        
        Returns:
            List of position dictionaries
        """
        try:
            # CRITICAL: Do NOT pass any query parameters to positions endpoint
            # Delta Exchange positions API does not accept query parameters
            response = self.client.get('/v2/positions')
            
            positions = []
            if 'result' in response:
                for position in response['result']:
                    # Skip positions with zero size
                    size = int(position.get('size', 0))
                    if size == 0:
                        continue
                    
                    # Filter by product_id if specified
                    if product_id and position.get('product_id') != product_id:
                        continue
                    
                    position_data = {
                        'product_id': position.get('product_id'),
                        'symbol': position.get('product', {}).get('symbol', 'Unknown'),
                        'size': size,
                        'entry_price': float(position.get('entry_price', 0)),
                        'mark_price': float(position.get('mark_price', 0)),
                        'liquidation_price': float(position.get('liquidation_price', 0)),
                        'unrealized_pnl': float(position.get('unrealized_pnl', 0)),
                        'realized_pnl': float(position.get('realized_pnl', 0)),
                        'margin': float(position.get('margin', 0))
                    }
                    
                    positions.append(position_data)
            
            logger.info(f"Fetched {len(positions)} open positions")
            return positions
        
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            raise
    
    def get_position_by_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific position by product ID.
        
        Args:
            product_id: Product ID
        
        Returns:
            Position dictionary or None if not found
        """
        try:
            positions = self.get_positions(product_id=product_id)
            return positions[0] if positions else None
        
        except Exception as e:
            logger.error(f"Failed to fetch position for product {product_id}: {e}")
            raise
          
