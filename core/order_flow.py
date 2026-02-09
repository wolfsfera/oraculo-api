"""
🐺 TAREA 2: ORDER FLOW ANALYZER
Análisis de flujo de órdenes con CVD (Cumulative Volume Delta)

Detecta:
1. Divergencias alcistas (precio baja, CVD sube) = Absorción pasiva
2. Icebergs (órdenes grandes ocultas que se rellenan repetidamente)
"""

import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime

from config import (
    CVD_DIVERGENCE_LOOKBACK,
    CVD_THRESHOLD,
    ORDERBOOK_DEPTH_LIMIT
)
from utils.logging_config import setup_logger

logger = setup_logger('order_flow')


class OrderFlowAnalyzer:
    """
    Analizador de flujo de órdenes para detectar acumulación institucional
    
    CVD Formula:
    CVD = Σ(Buy Volume - Sell Volume)
    
    Divergencia Alcista:
    - Precio hace Lower Low
    - CVD hace Higher Low o Higher High
    → Smart Money acumulando en debilidad
    """
    
    def __init__(self):
        self.exchange = ccxt.binance({  'enableRateLimit': True
        })
    
    async def fetch_trades(self, symbol: str, limit: int = 500) -> pd.DataFrame:
        """
        Obtiene trades recientes y clasifica como compras/ventas
        
        Args:
            symbol: Par a analizar
            limit: Número de trades a obtener
            
        Returns:
            DataFrame con trades clasificados
        """
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=limit)
            
            df = pd.DataFrame(trades)
            
            if df.empty:
                return df
            
            # Clasificar trades: si 'side' == 'buy' -> market buy (agresivo)
            # En Binance, 'side' indica quién fue el taker
            df['is_buy'] = df['side'] == 'buy'
            df['volume_delta'] = np.where(
                df['is_buy'],
                df['amount'],  # Compra agresiva
                -df['amount']  # Venta agresiva
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'price', 'amount', 'is_buy', 'volume_delta']]
            
        except Exception as e:
            logger.error(f"Error obteniendo trades de {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_cvd(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula Cumulative Volume Delta
        
        CVD[i] = CVD[i-1] + (BuyVolume[i] - SellVolume[i])
        
        Args:
            df: DataFrame con columna 'volume_delta'
            
        Returns:
            Serie con CVD acumulativo
        """
        if df.empty:
            return pd.Series()
        
        # Suma acumulativa del delta
        cvd = df['volume_delta'].cumsum()
        return cvd
    
    def detect_bullish_divergence(
        self,
        price_series: pd.Series,
        cvd_series: pd.Series,
        lookback: int = CVD_DIVERGENCE_LOOKBACK
    ) -> bool:
        """
        Detecta divergencia alcista clásica
        
        Condición:
        - Precio: Low[n] < Low[n-lookback] (nuevo mínimo)
        - CVD: CVD[n] > CVD[n-lookback] (mínimo más alto)
        
        Args:
            price_series: Serie de precios
            cvd_series: Serie de CVD
            lookback: Velas hacia atrás para comparar
            
        Returns:
            True si hay divergencia alcista
        """
        if len(price_series) < lookback + 1:
            return False
        
        # Precio actual vs precio hace N velas
        current_price = price_series.iloc[-1]
        past_price = price_series.iloc[-lookback]
        
        # CVD actual vs CVD hace N velas
        current_cvd = cvd_series.iloc[-1]
        past_cvd = cvd_series.iloc[-lookback]
        
        # Divergencia: precio baja, CVD sube
        price_lower = current_price < past_price
        cvd_higher = current_cvd > past_cvd
        
        return price_lower and cvd_higher
    
    async def detect_iceberg_orders(self, symbol: str) -> List[Dict]:
        """
        Detecta órdenes iceberg en el order book
        
        Iceberg = Orden grande que se muestra en pequeñas cantidades
        y se rellena constantemente al mismo precio
        
        Heurística:
        - Nivel de precio que se mantiene constante
        - Volumen que se rellena repetidamente
        - Cantidad >> promedio del order book
        
        Args:
            symbol: Par a analizar
            
        Returns:
            Lista de niveles sospechosos de iceberg
        """
        try:
            # Obtener order book profundo
            orderbook = await self.exchange.fetch_order_book(
                symbol,
                limit=ORDERBOOK_DEPTH_LIMIT
            )
            
            icebergs = []
            
            # Analizar lado de compras (bids)
            bids = pd.DataFrame(orderbook['bids'], columns=['price', 'amount'])
            
            if not bids.empty:
                # Volumen promedio en el book
                avg_amount = bids['amount'].mean()
                std_amount = bids['amount'].std()
                
                # Buscar órdenes > 3 desviaciones estándar
                threshold = avg_amount + (3 * std_amount)
                
                large_bids = bids[bids['amount'] > threshold]
                
                for _, row in large_bids.iterrows():
                    icebergs.append({
                        'side': 'BID',
                        'price': row['price'],
                        'amount': row['amount'],
                        'ratio_vs_avg': row['amount'] / avg_amount
                    })
            
            # Analizar lado de ventas (asks)
            asks = pd.DataFrame(orderbook['asks'], columns=['price', 'amount'])
            
            if not asks.empty:
                avg_amount = asks['amount'].mean()
                std_amount = asks['amount'].std()
                threshold = avg_amount + (3 * std_amount)
                
                large_asks = asks[asks['amount'] > threshold]
                
                for _, row in large_asks.iterrows():
                    icebergs.append({
                        'side': 'ASK',
                        'price': row['price'],
                        'amount': row['amount'],
                        'ratio_vs_avg': row['amount'] / avg_amount
                    })
            
            if icebergs:
                logger.info(f"🧊 {symbol}: {len(icebergs)} posibles icebergs detectados")
            
            return icebergs
            
        except Exception as e:
            logger.error(f"Error detectando icebergs en {symbol}: {e}")
            return []
    
    async def analyze_pair(self, symbol: str) -> Dict:
        """
        Análisis completo de order flow para un par
        
        Args:
            symbol: Par a analizar
            
        Returns:
            Diccionario con resultados del análisis
        """
        try:
            logger.info(f"📊 Analizando order flow de {symbol}...")
            
            # 1. Obtener trades y calcular CVD
            trades_df = await self.fetch_trades(symbol, limit=500)
            
            if trades_df.empty:
                return {'symbol': symbol, 'status': 'no_data'}
            
            cvd = self.calculate_cvd(trades_df)
            
            # 2. Detectar divergencia alcista
            has_divergence = self.detect_bullish_divergence(
                trades_df['price'],
                cvd
            )
            
            # 3. Buscar icebergs
            icebergs = await self.detect_iceberg_orders(symbol)
            
            # 4. Calcular ratio compras/ventas
            total_buys = trades_df[trades_df['is_buy']]['amount'].sum()
            total_sells = trades_df[~trades_df['is_buy']]['amount'].sum()
            buy_sell_ratio = total_buys / total_sells if total_sells > 0 else 0
            
            result = {
                'symbol': symbol,
                'cvd_current': cvd.iloc[-1] if not cvd.empty else 0,
                'bullish_divergence': has_divergence,
                'buy_sell_ratio': round(buy_sell_ratio, 2),
                'icebergs_detected': len(icebergs),
                'icebergs': icebergs[:3],  # Top 3 más grandes
                'timestamp': datetime.now()
            }
            
            # ✅ SEÑAL FUERTE si hay divergencia + ratio favorable
            if has_divergence and buy_sell_ratio > (1 + CVD_THRESHOLD):
                logger.warning(
                    f"🚨 DIVERGENCIA ALCISTA: {symbol} | "
                    f"Buy/Sell Ratio: {buy_sell_ratio:.2f}"
                )
                result['signal_strength'] = 'STRONG_BUY'
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return {'symbol': symbol, 'status': 'error', 'error': str(e)}
    
    async def close(self):
        """Cierra el exchange"""
        await self.exchange.close()
