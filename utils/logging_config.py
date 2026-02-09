"""
🐺 Sistema de Logging Profesional
Colores, niveles y formato optimizado para debugging
"""

import logging
import sys
from colorlog import ColoredFormatter
from config import LOG_LEVEL, LOG_FILE

def setup_logger(name: str = 'oraculo') -> logging.Logger:
    """
    Configura un logger con colores y formato profesional
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Evitar duplicados
    if logger.handlers:
        return logger
    
    # ============================================
    # CONSOLE HANDLER (con colores)
    # ============================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    
    console_format = ColoredFormatter(
        '%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s '
        '%(blue)s%(name)s%(reset)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # ============================================
    # FILE HANDLER (sin colores, más detalle)
    # ============================================
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        file_format = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"No se pudo crear el archivo de log: {e}")
    
    return logger


# Logger global para imports rápidos
default_logger = setup_logger()
