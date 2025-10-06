"""Wallet and balance API operations."""
import logging
from typing import Dict, Any, Optional
from .client import DeltaClient

logger = logging.getLogger(__name__)

class WalletAPI:
    """Handles wallet and balance operations."""
    
    def __init__(self, client: DeltaClient):
        self.client = client
    
    def get_balances(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """
        Get wallet balances.
        
        Args:
            asset: Optional asset symbol to filter (e.g., "USDT")
        
        Returns:
            Balance information dictionary
        """
        try:
            params = {}
            if asset:
                params['asset'] = asset
            
            response = self.client.get('/v2/wallet/balances', params=params)
            logger.info(f"Successfully fetched wallet balances")
            return response
        
        except Exception as e:
            logger.error(f"Failed to fetch wallet balances: {e}")
            raise
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account summary with margin and equity information.
        
        Returns:
            Account summary dictionary
        """
        try:
            balances = self.get_balances()
            
            # Extract key information
            summary = {
                'available_balance': 0,
                'margin_used': 0,
                'total_equity': 0,
                'unrealized_pnl': 0
            }
            
            if 'result' in balances:
                for balance in balances['result']:
                    summary['available_balance'] += float(balance.get('available_balance', 0))
                    summary['margin_used'] += float(balance.get('order_margin', 0)) + float(balance.get('position_margin', 0))
                    summary['total_equity'] += float(balance.get('balance', 0))
                    summary['unrealized_pnl'] += float(balance.get('unrealized_pnl', 0))
            
            return summary
        
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            raise
          
