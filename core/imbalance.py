"""
🐺 ORDER BOOK IMBALANCE ANALYZER
Analiza el desequilibrio de liquidez en el order book

Detecta:
- Ratio Bids/Asks en el 1% más cercano al precio
- Muros de compra/venta (walls)
- Desequilibrios que predicen movimiento de precio
"""

import ccxt.async_support as ccxt
import numpy as np
from typing import Dict, Tuple
from utils.logging_config import setup_logger

logger = setup_logger('imbalance')


class OrderBookImbalanceAnalyzer:
    """
    Analiza el desequilibrio del order book para predecir presión de precio
    
    Formula:
    Imbalance % = (Total_Bids - Total_Asks) / (Total_Bids + Total_Asks) * 100
    
    Interpretación:
    - Imbalance > +20%: Presión de COMPRA (probable subida)
    - Imbalance < -20%: Presión de VENTA (probable bajada)
    - Imbalance [-20%, +20%]: Neutral
    """
    
    def __init__(self):
        self.exchange = ccxt.binance({'enableRateLimit': True})
    
    async def get_orderbook_imbalance(
        self, 
        symbol: str, 
        depth_percentage: float = 1.0
    ) -> Dict:
        """
        Calcula el imbalance del order book
        
        Args:
            symbol: Par a analizar (ej: 'BTC/USDT')
            depth_percentage: % de profundidad desde el precio actual
            
        Returns:
            Dict con imbalance metrics
        """
        try:
            # Obtener order book profundo
            orderbook = await self.exchange.fetch_order_book(symbol, limit=100)
            
            if not orderbook.get('bids') or not orderbook.get('asks'):
                return {'symbol': symbol, 'status': 'no_data'}
            
            # Precio medio (mid price)
            best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
            best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0
            mid_price = (best_bid + best_ask) / 2
            
            # Calcular rango de profundidad (1% por defecto)
            price_range = mid_price * (depth_percentage / 100)
            upper_bound = mid_price + price_range
            lower_bound = mid_price - price_range
            
            # Filtrar bids/asks dentro del rango
            relevant_bids = [
                [price, amount] for price, amount in orderbook['bids']
                if price >= lower_bound
            ]
            
            relevant_asks = [
                [price, amount] for price, amount in orderbook['asks']
                if price <= upper_bound
            ]
            
            # Sumar volumen total
            total_bid_volume = sum(amount for _, amount in relevant_bids)
            total_ask_volume = sum(amount for _, amount in relevant_asks)
            
            # Calcular imbalance
            total_volume = total_bid_volume + total_ask_volume
            
            if total_volume == 0:
                imbalance_pct = 0
            else:
                imbalance_pct = ((total_bid_volume - total_ask_volume) / total_volume) * 100
            
            # Calcular spread
            spread_pct = ((best_ask - best_bid) / mid_price) * 100 if mid_price > 0 else 0
            
            # Detectar muros (walls)
            bid_wall = self._detect_wall(orderbook['bids'], total_bid_volume)
            ask_wall = self._detect_wall(orderbook['asks'], total_ask_volume)
            
            result = {
                'symbol': symbol,
                'mid_price': mid_price,
                'imbalance_pct': round(imbalance_pct, 2),
                'spread_pct': round(spread_pct, 4),
                'total_bid_volume': total_bid_volume,
                'total_ask_volume': total_ask_volume,
                'bid_wall_detected': bid_wall is not None,
                'ask_wall_detected': ask_wall is not None,
                'bid_wall': bid_wall,
                'ask_wall': ask_wall,
                'pressure': self._interpret_pressure(imbalance_pct)
            }
            
            # Log si hay desequilibrio significativo
            if abs(imbalance_pct) > 20:
                logger.info(
                    f"⚖️  {symbol}: Imbalance {imbalance_pct:+.1f}% - "
                    f"Presión de {'COMPRA' if imbalance_pct > 0 else 'VENTA'}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando order book de {symbol}: {e}")
            return {'symbol': symbol, 'status': 'error', 'error': str(e)}
    
    def _detect_wall(self, orders: list, total_volume: float, threshold: float = 0.3) -> dict:
        """
        Detecta muros (walls) en el order book
        
        Un wall es una orden que representa > 30% del volumen total
        
        Args:
            orders: Lista de [price, amount]
            total_volume: Volumen total del lado
            threshold: % mínimo para considerar wall
            
        Returns:
            Dict con info del wall o None
        """
        if not orders or total_volume == 0:
            return None
        
        for price, amount in orders[:10]:  # Solo primeros 10 niveles
            volume_pct = (amount / total_volume) * 100
            
            if volume_pct >= (threshold * 100):
                return {
                    'price': price,
                    'amount': amount,
                    'volume_pct': round(volume_pct, 2)
                }
        
        return None
    
    def _interpret_pressure(self, imbalance_pct: float) -> str:
        """
        Interpreta la presión del mercado según el imbalance
        
        Args:
            imbalance_pct: % de imbalance
            
        Returns:
            Clasificación de presión
        """
        if imbalance_pct > 30:
            return "🟢 COMPRA FUERTE"
        elif imbalance_pct > 10:
            return "🟢 COMPRA MODERADA"
        elif imbalance_pct < -30:
            return "🔴 VENTA FUERTE"
        elif imbalance_pct < -10:
            return "🔴 VENTA MODERADA"
        else:
            return "⚪ NEUTRAL"
    
    async def close(self):
        """Cierra el exchange"""
        await self.exchange.close()
