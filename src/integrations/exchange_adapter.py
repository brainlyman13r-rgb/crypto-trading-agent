"""CCXT Exchange Adapter - Abstraction layer for multiple crypto exchanges."""

import logging
from typing import Optional, List, Dict
import ccxt

logger = logging.getLogger(__name__)


class ExchangeAdapter:
    """Unified CCXT adapter for Binance, Bybit, Blofin, etc."""
    
    def __init__(
        self,
        exchange_name: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        sandbox: bool = True,
    ):
        """
        Initialize exchange adapter.
        
        Args:
            exchange_name: Exchange name ("binance", "bybit", "blofin")
            api_key: API key
            api_secret: API secret
            sandbox: Use testnet/sandbox mode
        """
        self.exchange_name = exchange_name.lower()
        self.sandbox = sandbox
        
        # Initialize exchange
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key or '',
            'secret': api_secret or '',
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
        
        logger.info(f"Exchange adapter initialized: {exchange_name} (sandbox={sandbox})")
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
    ) -> Optional[List[List]]:
        """
        Fetch OHLCV candle data.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe ("15m", "1h", "4h")
            limit: Number of candles to fetch
        
        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.debug(f"Fetched {len(candles)} {timeframe} candles for {symbol}")
            return candles
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    def fetch_balance(self) -> Optional[Dict]:
        """Fetch account balance."""
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
    
    def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
    ) -> Optional[Dict]:
        """
        Create market order.
        
        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            amount: Order amount
        
        Returns:
            Order response
        """
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            logger.info(f"Market order created: {side} {amount} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            return None
    
    def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
    ) -> Optional[Dict]:
        """
        Create limit order.
        
        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            amount: Order amount
            price: Order price
        
        Returns:
            Order response
        """
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            logger.info(f"Limit order created: {side} {amount} {symbol} @ {price}")
            return order
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            return None
    
    def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
    ) -> Optional[Dict]:
        """
        Create stop-loss order.
        
        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            amount: Order amount
            stop_price: Trigger price
        
        Returns:
            Order response
        """
        try:
            params = {
                'stopPrice': stop_price,
                'type': 'stop_market',
            }
            order = self.exchange.create_order(symbol, 'market', side, amount, params=params)
            logger.info(f"Stop-loss order created: {side} {amount} {symbol} @ {stop_price}")
            return order
        except Exception as e:
            logger.error(f"Error creating stop-loss order: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Cancel an order."""
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return None
    
    def fetch_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Fetch order status."""
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return None
