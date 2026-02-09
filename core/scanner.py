"""
🐺 TAREA 1: MARKET SCANNER
Motor de escaneo en tiempo real con detección de Volumen Relativo Anómalo (RVol)

Conecta a Binance WebSockets y detecta pares con volumen > 5x promedio
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from typing import List, Dict, Set
from datetime import datetime, timedelta

from config import (
    RVOL_THRESHOLD,
    VOLUME_LOOKBACK_HOURS,
    MIN_CANDLES_REQUIRED,
    QUOTE_CURRENCIES,
    MIN_VOLUME_USD,
    EXCLUDED_SYMBOLS,
    TIMEFRAME
)
from utils.logging_config import setup_logger

logger = setup_logger('scanner')


class MarketScanner:
    """
    Scanner de mercado que detecta anomalías de volumen en tiempo real
    
    Algoritmo:
    1. Obtén todos los pares USDT de Binance
    2. Filtra por volumen mínimo y excluye stablecoins
    3. Descarga velas históricas (24h)
    4. Calcula SMA de volumen
    5. Detecta cuando Volumen_actual > 5 * SMA_Volumen_24h
    """
    
    def __init__(self):
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.active_pairs: Set[str] = set()
        self.volume_cache: Dict[str, pd.DataFrame] = {}
        
    async def initialize(self):
        """Inicializa el exchange y carga pares disponibles"""
        try:
            logger.info("🔄 Inicializando MarketScanner...")
            await self.exchange.load_markets()
            await self._load_tradable_pairs()
            logger.info(f"✅ Scanner inicializado con {len(self.active_pairs)} pares")
        except Exception as e:
            logger.error(f"❌ Error inicializando scanner: {e}")
            raise
    
    async def _load_tradable_pairs(self):
        """Carga pares que cumplen los filtros de volumen y quote currency"""
        try:
            tickers = await self.exchange.fetch_tickers()
            
            for symbol, ticker in tickers.items():
                # Filtrar por quote currency (ej: USDT)
                if not any(symbol.endswith(f'/{quote}') for quote in QUOTE_CURRENCIES):
                    continue
                
                # Excluir stablecoins y leveraged tokens
                base = symbol.split('/')[0]
                if any(excluded in base for excluded in EXCLUDED_SYMBOLS):
                    continue
                
                # Filtrar por volumen mínimo
                volume_usd = ticker.get('quoteVolume', 0)
                if volume_usd < MIN_VOLUME_USD:
                    continue
                
                self.active_pairs.add(symbol)
            
            logger.info(f"📊 {len(self.active_pairs)} pares activos tras filtros")
            
        except Exception as e:
            logger.error(f"Error cargando pares: {e}")
    
    async def fetch_historical_volume(self, symbol: str) -> pd.DataFrame:
        """
        Descarga velas históricas para calcular volumen promedio
        
        Args:
            symbol: Par a analizar (ej: 'BTC/USDT')
            
        Returns:
            DataFrame con columnas: timestamp, volume
        """
        try:
            # Calcular cuántas velas necesitamos
            # 1m timeframe -> 1440 velas en 24h
            limit = VOLUME_LOOKBACK_HOURS * 60
            
            # Fetch OHLCV
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=TIMEFRAME,
                limit=min(limit, 1000)  # Binance max 1000
            )
            
            if len(ohlcv) < MIN_CANDLES_REQUIRED:
                logger.warning(f"⚠️  {symbol}: Solo {len(ohlcv)} velas (mínimo {MIN_CANDLES_REQUIRED})")
                return pd.DataFrame()
            
            # Convertir a DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.error(f"Error descargando velas de {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_rvol(self, df: pd.DataFrame) -> float:
        """
        Calcula Relative Volume (RVol)
        
        Fórmula: RVol = Volumen_Actual / SMA_Volumen_24h
        
        Args:
            df: DataFrame con columna 'volume'
            
        Returns:
            Ratio de volumen relativo
        """
        if df.empty or len(df) < 2:
            return 0.0
        
        # Volumen de la última vela (actual)
        current_volume = df['volume'].iloc[-1]
        
        # SMA de volumen (excluir vela actual)
        volume_sma = df['volume'].iloc[:-1].mean()
        
        if volume_sma == 0:
            return 0.0
        
        rvol = current_volume / volume_sma
        return round(rvol, 2)
    
    async def scan_pair(self, symbol: str) -> Dict:
        """
        Escanea un par individual buscando anomalías de volumen
        
        Args:
            symbol: Par a escanear
            
        Returns:
            Dict con resultado del escaneo o None si no hay señal
        """
        try:
            # Obtener datos históricos
            df = await self.fetch_historical_volume(symbol)
            
            if df.empty:
                return None
            
            # Calcular RVol
            rvol = self.calculate_rvol(df)
            
            # ✅ DETECCIÓN DE SEÑAL
            if rvol >= RVOL_THRESHOLD:
                current_price = df['close'].iloc[-1]
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].iloc[:-1].mean()
                
                signal = {
                    'symbol': symbol,
                    'rvol': rvol,
                    'price': current_price,
                    'volume_current': current_volume,
                    'volume_avg_24h': avg_volume,
                    'timestamp': datetime.now(),
                    'alert_type': 'UNUSUAL_VOLUME'
                }
                
                logger.info(
                    f"🔥 SEÑAL DETECTADA: {symbol} | "
                    f"RVol: {rvol}x | Precio: ${current_price:.4f}"
                )
                
                return signal
            
            return None
            
        except Exception as e:
            logger.debug(f"Error escaneando {symbol}: {e}")
            return None
    
    async def scan_all_pairs(self) -> List[Dict]:
        """
        Escanea todos los pares activos en paralelo
        
        Returns:
            Lista de señales detectadas
        """
        logger.info(f"🔍 Iniciando escaneo de {len(self.active_pairs)} pares...")
        
        # Ejecutar escaneo en paralelo (asyncio)
        tasks = [self.scan_pair(symbol) for symbol in self.active_pairs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar señales válidas
        signals = [r for r in results if isinstance(r, dict) and r is not None]
        
        logger.info(f"✅ Escaneo completado: {len(signals)} señales encontradas")
        return signals
    
    async def close(self):
        """Cierra el exchange limpiamente"""
        await self.exchange.close()
        logger.info("Scanner cerrado")
