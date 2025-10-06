"""Authentication and signature generation for Delta Exchange API."""
import hmac
import hashlib
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class DeltaAuth:
    """Handles authentication and signature generation for Delta Exchange API."""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Delta Exchange authentication.
        
        Args:
            api_key: Delta Exchange API key
            api_secret: Delta Exchange API secret key
        """
        self.api_key = api_key
        self.api_secret = api_secret
        logger.debug(f"DeltaAuth initialized with API key: {api_key[:10]}...")
    
    def generate_signature(self, method: str, timestamp: str, path: str, 
                          query_string: str = "", payload: str = "") -> str:
        """
        Generate HMAC-SHA256 signature for Delta Exchange API.
        
        Signature format: method + timestamp + path + query_string + payload
        Example: GET1633024800/v2/positions (no query string or payload for GET)
        Example: GET1633024800/v2/orders?state=open (with query string)
        
        Args:
            method: HTTP method (GET, POST, DELETE, PUT, etc.)
            timestamp: Current Unix timestamp in seconds as string
            path: API endpoint path (e.g., "/v2/positions")
            query_string: Query string WITH ? prefix for GET requests (e.g., "?state=open")
            payload: JSON payload string for POST/PUT requests (empty for GET)
        
        Returns:
            Hexadecimal HMAC-SHA256 signature string
        """
        # Build signature data string
        signature_data = method + timestamp + path + query_string + payload
        
        logger.debug(f"Signature components:")
        logger.debug(f"  Method: {method}")
        logger.debug(f"  Timestamp: {timestamp}")
        logger.debug(f"  Path: {path}")
        logger.debug(f"  Query String: {query_string}")
        logger.debug(f"  Payload: {payload[:50] if payload else '(empty)'}")
        logger.debug(f"  Full signature data: {signature_data}")
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Generated signature: {signature}")
        
        return signature
    
    def get_headers(self, method: str, path: str, query_string: str = "", 
                   payload: str = "") -> Dict[str, str]:
        """
        Generate complete headers for Delta Exchange API request.
        
        Args:
            method: HTTP method (GET, POST, DELETE, PUT)
            path: API endpoint path (e.g., "/v2/positions")
            query_string: Query string WITH ? prefix (e.g., "?state=open") - EMPTY for no params
            payload: JSON payload string for POST/PUT - EMPTY for GET requests
        
        Returns:
            Dictionary of headers including authentication
        """
        # Generate current timestamp
        timestamp = str(int(time.time()))
        
        # Generate signature
        signature = self.generate_signature(method, timestamp, path, query_string, payload)
        
        # Build headers
        headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'DeltaTradingBot/1.0',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Generated headers: {self._mask_headers(headers)}")
        
        return headers
    
    def _mask_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive information in headers for logging."""
        masked = headers.copy()
        if 'api-key' in masked:
            masked['api-key'] = masked['api-key'][:10] + '...'
        if 'signature' in masked:
            masked['signature'] = masked['signature'][:10] + '...'
        return masked
        
