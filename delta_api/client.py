"""Core Delta Exchange API client with connection pooling."""
import requests
import time
import logging
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from .auth import DeltaAuth

logger = logging.getLogger(__name__)

class DeltaClient:
    """Core client for Delta Exchange API with connection pooling and retry logic."""
    
    def __init__(self, api_key: str, api_secret: str):
        self.base_url = settings.DELTA_BASE_URL
        self.auth = DeltaAuth(api_key, api_secret)
        self.session = self._create_session()
        self.last_request_time = 0
    
    def _create_session(self) -> requests.Session:
        """Create requests session with connection pooling and retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=settings.POOL_CONNECTIONS,
            pool_maxsize=settings.POOL_MAXSIZE,
            max_retries=retry_strategy
        )
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _rate_limit(self):
        """Enforce minimum interval between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < settings.MIN_REQUEST_INTERVAL:
            sleep_time = settings.MIN_REQUEST_INTERVAL - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, path: str, query_params: Optional[Dict] = None,
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to Delta Exchange API.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API endpoint path
            query_params: Query parameters dict for GET requests
            data: Request body dict for POST/PUT requests
        
        Returns:
            JSON response as dictionary
        """
        self._rate_limit()
        
        url = f"{self.base_url}{path}"
        
        # Build query string for signature
        query_string = ""
        if query_params:
            query_string = "?" + "&".join([f"{k}={v}" for k, v in query_params.items()])
        
        # Build payload for signature
        payload = ""
        if data:
            import json
            payload = json.dumps(data, separators=(',', ':'))
        
        # Get authentication headers
        headers = self.auth.get_headers(method, path, query_string, payload)

        # Add User-Agent if not present
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'DeltaTradingBot/1.0'
        
        # Log request details (mask sensitive data)
        logger.info(f"{method} {path}{query_string}")
        logger.debug(f"Headers: {self._mask_headers(headers)}")
        if data:
            logger.debug(f"Payload: {payload[:200]}...")
        
        try:
            # Don't pass params if None or empty
            request_params = query_params if query_params else None
          
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=query_params,
                json=data,
                timeout=settings.REQUEST_TIMEOUT
            )
            
            # Log response
            logger.info(f"Response: {response.status_code}")

            # Log response body for debugging
            try:
                response_body = response.json()
                if response.status_code >= 400:
                    logger.error(f"Error Response Body: {response_body}")
            except:
                logger.error(f"Response Text: {response.text}")
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            return response_body
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            try:
                error_details = e.response.json()
                logger.error(f"Error Details: {error_details}")
            except:
                logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {e}")
            raise
    
    def _mask_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive data in headers for logging."""
        masked = headers.copy()
        if 'api-key' in masked:
            masked['api-key'] = masked['api-key'][:8] + '***'
        if 'signature' in masked:
            masked['signature'] = masked['signature'][:8] + '***'
        return masked
    
    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request('GET', path, query_params=params)
    
    def post(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request('POST', path, data=data)
    
    def delete(self, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request('DELETE', path, data=data)
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
                       
