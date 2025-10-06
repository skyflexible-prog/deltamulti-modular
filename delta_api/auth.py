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
        self.api_key = api_key
        self.api_secret = api_secret
    
    def generate_signature(self, method: str, timestamp: str, path: str, 
                          query_string: str = "", payload: str = "") -> str:
        """
        Generate HMAC-SHA256 signature for Delta Exchange API.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            timestamp: Current Unix timestamp in seconds
            path: API endpoint path (e.g., "/v2/orders")
            query_string: Query string with ? prefix for GET requests (e.g., "?state=open")
            payload: JSON payload string for POST/PUT requests
        
        Returns:
            Hexadecimal signature string
        """
        # Signature format: method + timestamp + path + query_string + payload
        signature_data = method + timestamp + path + query_string + payload
        
        logger.debug(f"Generating signature for: {signature_data[:100]}...")
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def get_headers(self, method: str, path: str, query_string: str = "", 
                   payload: str = "") -> Dict[str, str]:
        """
        Generate headers for Delta Exchange API request.
        
        Args:
            method: HTTP method
            path: API endpoint path
            query_string: Query string with ? prefix for GET requests
            payload: JSON payload string for POST/PUT requests
        
        Returns:
            Dictionary of headers
        """
        timestamp = str(int(time.time()))
        signature = self.generate_signature(method, timestamp, path, query_string, payload)
        
        headers = {
            'api-key': self.api_key,
            'signature': signature,
            'timestamp': timestamp,
            'User-Agent': 'python-rest-client',
            'Content-Type': 'application/json'
        }
        
        return headers
                     
