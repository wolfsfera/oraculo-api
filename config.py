"""
🐺 PROYECTO ORÁCULO - Configuración Central
Parámetros globales del sistema de análisis de mercado
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============================================
# CONFIGURACIÓN DE BINANCE
# ============================================
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')

# ============================================
# PARÁMETROS DEL SCANNER
# ============================================
# Umbral de Volumen Relativo (RVol)
RVOL_THRESHOLD = float(os.getenv('RVOL_THRESHOLD', 5.0))

# Período de lookback para volumen promedio (horas)
VOLUME_LOOKBACK_HOURS = int(os.getenv('VOLUME_LOOKBACK_HOURS', 24))

# Mínimo de velas requeridas para análisis confiable
MIN_CANDLES_REQUIRED = int(os.getenv('MIN_CANDLES_REQUIRED', 100))

# Intervalo de tiempo para velas (Binance format)
TIMEFRAME = '1m'  # 1 minuto para detección real-time
TIMEFRAME_DAILY = '1d'  # 1 día para reportes

# ============================================
# FILTROS DE MERCADO
# ============================================
# Quote currencies a escanear
QUOTE_CURRENCIES = os.getenv('QUOTE_CURRENCIES', 'USDT').split(',')

# Volumen mínimo 24h en USD
MIN_VOLUME_USD = float(os.getenv('MIN_VOLUME_USD', 100000))

# Excluir stablecoins y tokens problemáticos
EXCLUDED_SYMBOLS = [
    'BUSD', 'USDC', 'DAI', 'TUSD', 'USDP',  # Stablecoins
    'UP', 'DOWN', 'BEAR', 'BULL'  # Leveraged tokens
]

# ============================================
# PARÁMETROS DE DETECCIÓN
# ============================================
# CVD (Cumulative Volume Delta)
CVD_DIVERGENCE_LOOKBACK = 20  # Velas hacia atrás para buscar divergencias
CVD_THRESHOLD = 0.3  # 30% más compras que ventas

# Bollinger Bands (compresión de volatilidad)
BB_PERIOD = 20
BB_STD = 2
BB_SQUEEZE_THRESHOLD = 0.02  # 2% de ancho

# Order Book Depth
ORDERBOOK_DEPTH_LIMIT = 100  # Niveles del order book a analizar

# ============================================
# SISTEMA DE ALERTAS
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ============================================
# PERFORMANCE & LIMITS
# ============================================
# Intervalo entre escaneos (segundos)
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', 60))

# Máximo de pares a analizar en paralelo
MAX_CONCURRENT_PAIRS = 50

# Timeout para requests (segundos)
REQUEST_TIMEOUT = 10

# Rate limiting (requests por segundo)
RATE_LIMIT_PER_SECOND = 10

# ============================================
# LOGGING
# ============================================
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'
LOG_FILE = 'data/oraculo.log'

# ============================================
# PATHS
# ============================================
REPORTS_DIR = 'data/reports'
DATA_DIR = 'data'
