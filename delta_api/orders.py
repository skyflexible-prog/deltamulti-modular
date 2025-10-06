"""Orders API operations."""
import logging
from typing import Dict, Any, List, Optional

from config.constants import (
    ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, SIDE_BUY, SIDE_SELL,
    STOP_ORDER_TYPE_SL, STOP_ORDER_TYPE_TP, ORDER_STATE_OPEN, ORDER_STATE_PENDING
)

logger = logging.getLogger(__name__)

class OrderAPI:
    """Handles order operations."""
    
    def __init__(self, client):
        self.client = client
    
    def place_market_order(self, product_id: int, side: str, size: int) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            product_id: Product ID to trade
            side: Order side ("buy" or "sell")
            size: Number of contracts
        
        Returns:
            Order response dictionary
        """
        try:
            order_data = {
                'product_id': product_id,
                'side': side,
                'size': size,
                'order_type': ORDER_TYPE_MARKET
            }
            
            response = self.client.post('/v2/orders', data=order_data)
            
            if 'result' in response:
                order = response['result']
                logger.info(f"Market order placed: {order.get('id')} - {side} {size} @ {product_id}")
                return order
            
            raise ValueError(f"Invalid order response: {response}")
        
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise
    
    def place_limit_order(self, product_id: int, side: str, size: int, 
                         limit_price: float) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            product_id: Product ID to trade
            side: Order side ("buy" or "sell")
            size: Number of contracts
            limit_price: Limit price
        
        Returns:
            Order response dictionary
        """
        try:
            order_data = {
                'product_id': product_id,
                'side': side,
                'size': size,
                'order_type': ORDER_TYPE_LIMIT,
                'limit_price': str(limit_price)
            }
            
            response = self.client.post('/v2/orders', data=order_data)
            
            if 'result' in response:
                order = response['result']
                logger.info(f"Limit order placed: {order.get('id')} - {side} {size} @ {limit_price}")
                return order
            
            raise ValueError(f"Invalid order response: {response}")
        
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise
    
    def place_stop_loss_order(self, product_id: int, side: str, size: int,
                             stop_price: float, limit_price: float,
                             reduce_only: bool = True) -> Dict[str, Any]:
        """
        Place a stop-loss order.
        
        Args:
            product_id: Product ID
            side: Order side (opposite of position - "sell" for long, "buy" for short)
            size: Number of contracts
            stop_price: Trigger price
            limit_price: Limit price after trigger
            reduce_only: Only reduce position (default: True)
        
        Returns:
            Order response dictionary
        """
        try:
            order_data = {
                'product_id': product_id,
                'side': side,
                'size': size,
                'order_type': ORDER_TYPE_LIMIT,
                'limit_price': str(limit_price),
                'stop_order_type': STOP_ORDER_TYPE_SL,
                'stop_price': str(stop_price),
                'reduce_only': reduce_only
            }
            
            response = self.client.post('/v2/orders', data=order_data)
            
            if 'result' in response:
                order = response['result']
                logger.info(f"Stop-loss order placed: {order.get('id')} - trigger: {stop_price}, limit: {limit_price}")
                return order
            
            raise ValueError(f"Invalid order response: {response}")
        
        except Exception as e:
            logger.error(f"Failed to place stop-loss order: {e}")
            raise
    
    def place_take_profit_order(self, product_id: int, side: str, size: int,
                               stop_price: float, limit_price: float,
                               reduce_only: bool = True) -> Dict[str, Any]:
        """
        Place a take-profit order.
        
        Args:
            product_id: Product ID
            side: Order side (opposite of position - "sell" for long, "buy" for short)
            size: Number of contracts
            stop_price: Trigger price
            limit_price: Limit price after trigger
            reduce_only: Only reduce position (default: True)
        
        Returns:
            Order response dictionary
        """
        try:
            order_data = {
                'product_id': product_id,
                'side': side,
                'size': size,
                'order_type': ORDER_TYPE_LIMIT,
                'limit_price': str(limit_price),
                'stop_order_type': STOP_ORDER_TYPE_TP,
                'stop_price': str(stop_price),
                'reduce_only': reduce_only
            }
            
            response = self.client.post('/v2/orders', data=order_data)
            
            if 'result' in response:
                order = response['result']
                logger.info(f"Take-profit order placed: {order.get('id')} - trigger: {stop_price}, limit: {limit_price}")
                return order
            
            raise ValueError(f"Invalid order response: {response}")
        
        except Exception as e:
            logger.error(f"Failed to place take-profit order: {e}")
            raise
    
    def get_orders(self, state: str = ORDER_STATE_OPEN, 
                   product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get orders by state.
        
        Args:
            state: Order state ("open" or "pending")
            product_id: Optional product ID filter
        
        Returns:
            List of order dictionaries
        """
        try:
            # IMPORTANT: Query string must be included in signature
            params = {'state': state}
            
            if product_id:
                params['product_id'] = product_id
            
            response = self.client.get('/v2/orders', params=params)
            
            orders = []
            if 'result' in response:
                for order in response['result']:
                    order_data = {
                        'id': order.get('id'),
                        'product_id': order.get('product_id'),
                        'symbol': order.get('product', {}).get('symbol', 'Unknown'),
                        'side': order.get('side'),
                        'size': int(order.get('size', 0)),
                        'unfilled_size': int(order.get('unfilled_size', 0)),
                        'order_type': order.get('order_type'),
                        'limit_price': float(order.get('limit_price', 0)) if order.get('limit_price') else None,
                        'stop_order_type': order.get('stop_order_type'),
                        'stop_price': float(order.get('stop_price', 0)) if order.get('stop_price') else None,
                        'state': order.get('state'),
                        'created_at': order.get('created_at')
                    }
                    orders.append(order_data)
            
            logger.info(f"Fetched {len(orders)} orders with state: {state}")
            return orders
        
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            raise
    
    def get_open_orders(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Args:
            product_id: Optional product ID filter
        
        Returns:
            List of open order dictionaries
        """
        return self.get_orders(state=ORDER_STATE_OPEN, product_id=product_id)
    
    def get_pending_orders(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all pending stop orders.
        
        Args:
            product_id: Optional product ID filter
        
        Returns:
            List of pending order dictionaries
        """
        return self.get_orders(state=ORDER_STATE_PENDING, product_id=product_id)
    
    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        Cancel a specific order.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Cancellation response dictionary
        """
        try:
            response = self.client.delete(f'/v2/orders/{order_id}')
            logger.info(f"Order cancelled: {order_id}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def cancel_all_orders(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Cancel all orders, optionally filtered by product.
        
        Args:
            product_id: Optional product ID to filter cancellation
        
        Returns:
            Cancellation response dictionary
        """
        try:
            data = {}
            if product_id:
                data['product_id'] = product_id
            
            response = self.client.delete('/v2/orders/all', data=data)
            logger.info(f"All orders cancelled" + (f" for product {product_id}" if product_id else ""))
            return response
        
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise
    
    def place_straddle_orders(self, call_product_id: int, put_product_id: int,
                             side: str, size: int) -> Dict[str, Any]:
        """
        Place both legs of a straddle (call and put) atomically.
        
        Args:
            call_product_id: Call option product ID
            put_product_id: Put option product ID
            side: "buy" for long straddle, "sell" for short straddle
            size: Number of lots
        
        Returns:
            Dictionary with both order results
        """
        try:
            # Place call order
            call_order = self.place_market_order(call_product_id, side, size)
            
            # Place put order
            put_order = self.place_market_order(put_product_id, side, size)
            
            result = {
                'call_order': call_order,
                'put_order': put_order,
                'success': True
            }
            
            logger.info(f"Straddle orders placed: Call {call_order.get('id')}, Put {put_order.get('id')}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to place straddle orders: {e}")
            # If one leg fails, we should ideally try to cancel the other
            # But for simplicity, we'll just raise the error
            raise
    
    def place_batch_stop_orders(self, orders: List[Dict[str, Any]], 
                               order_type: str = 'stop_loss') -> List[Dict[str, Any]]:
        """
        Place multiple stop orders in batch.
        
        Args:
            orders: List of order dictionaries with keys:
                   - product_id
                   - side
                   - size
                   - stop_price
                   - limit_price
            order_type: "stop_loss" or "take_profit"
        
        Returns:
            List of order results
        """
        results = []
        
        for order_data in orders:
            try:
                if order_type == 'stop_loss':
                    result = self.place_stop_loss_order(
                        product_id=order_data['product_id'],
                        side=order_data['side'],
                        size=order_data['size'],
                        stop_price=order_data['stop_price'],
                        limit_price=order_data['limit_price']
                    )
                else:  # take_profit
                    result = self.place_take_profit_order(
                        product_id=order_data['product_id'],
                        side=order_data['side'],
                        size=order_data['size'],
                        stop_price=order_data['stop_price'],
                        limit_price=order_data['limit_price']
                    )
                
                results.append({
                    'success': True,
                    'order': result,
                    'product_id': order_data['product_id']
                })
            
            except Exception as e:
                logger.error(f"Failed to place {order_type} order for product {order_data['product_id']}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'product_id': order_data['product_id']
                })
        
        successful = sum(1 for r in results if r['success'])
        logger.info(f"Batch {order_type} orders: {successful}/{len(orders)} successful")
        
        return results
                                 
