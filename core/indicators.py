"""
🐺 INDICADORES TÉCNICOS
Cálculos vectorizados para análisis técnico

Incluye:
- Bollinger Bands (compresión de volatilidad)
- SMA/EMA
- RSI
- ATR
"""

import pandas as pd
import numpy as np
from typing import Tuple

from config import BB_PERIOD, BB_STD, BB_SQUEEZE_THRESHOLD


class TechnicalIndicators:
    """
    Colección de indicadores técnicos optimizados con numpy
    """
    
    @staticmethod
    def bollinger_bands(
        df: pd.DataFrame,
        period: int = BB_PERIOD,
        std_dev: float = BB_STD
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula Bollinger Bands
        
        Args:
            df: DataFrame con columna 'close'
            period: Período para SMA
            std_dev: Multiplicador de desviación estándar
            
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def detect_bb_squeeze(
        df: pd.DataFrame,
        threshold: float = BB_SQUEEZE_THRESHOLD
    ) -> bool:
        """
        Detecta compresión de Bollinger Bands
        
        Squeeze = Bandas muy estrechas → Explosión inminente
        
        Formula:
        Ancho de Banda = (Upper - Lower) / Middle
        Si Ancho < Threshold → Squeeze
        
        Args:
            df: DataFrame con columna 'close'
            threshold: Umbral de compresión (default 2%)
            
        Returns:
            True si hay squeeze (compresión)
        """
        if len(df) < BB_PERIOD:
            return False
        
        upper, middle, lower = TechnicalIndicators.bollinger_bands(df)
        
        # Ancho de banda normalizado
        bandwidth = (upper - lower) / middle
        
        # Último valor
        current_bandwidth = bandwidth.iloc[-1]
        
        return current_bandwidth < threshold
    
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(window=period).mean()
    
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index
        
        Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Avg Gain / Avg Loss
        """
        delta = series.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range
        
        Mide volatilidad real del mercado
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def volume_profile(df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
        """
        Volume Profile - Distribución de volumen por nivel de precio
        
        Identifica zonas de alto volumen (POC - Point of Control)
        """
        if df.empty:
            return pd.DataFrame()
        
        # Crear bins de precio
        price_range = df['high'].max() - df['low'].min()
        bin_size = price_range / bins
        
        df['price_bin'] = ((df['close'] - df['low'].min()) / bin_size).astype(int)
        
        # Agrupar volumen por bin
        volume_profile = df.groupby('price_bin')['volume'].sum().sort_values(ascending=False)
        
        return volume_profile
