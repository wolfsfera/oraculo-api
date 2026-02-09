"""
🐺 WebSocket Manager con Reconexión Automática
Gestión robusta de conexiones WebSocket a Binance
"""

import asyncio
import json
import websockets
from typing import Callable, Optional
from utils.logging_config import setup_logger

logger = setup_logger('websocket')


class WebSocketManager:
    """
    Gestor de WebSocket con auto-reconexión y manejo de errores
    """
    
    def __init__(
        self,
        url: str,
        on_message: Callable,
        on_error: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        max_reconnect_attempts: int = 5,
        reconnect_delay: int = 5
    ):
        """
        Args:
            url: URL del WebSocket
            on_message: Callback para mensajes recib

idos
            on_error: Callback para errores (opcional)
            on_close: Callback para cierre (opcional)
            max_reconnect_attempts: Intentos máximos de reconexión
            reconnect_delay: Segundos entre intentos
        """
        self.url = url
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        self.ws = None
        self.running = False
        self.reconnect_count = 0
    
    async def connect(self):
        """Establece conexión WebSocket con retry logic"""
        while self.reconnect_count < self.max_reconnect_attempts:
            try:
                logger.info(f"Conectando a {self.url}...")
                self.ws = await websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=10
                )
                logger.info("✅ Conexión WebSocket establecida")
                self.reconnect_count = 0  # Reset contador
                return True
                
            except Exception as e:
                self.reconnect_count += 1
                logger.error(
                    f"❌ Error de conexión (intento {self.reconnect_count}/"
                    f"{self.max_reconnect_attempts}): {e}"
                )
                
                if self.reconnect_count < self.max_reconnect_attempts:
                    logger.info(f"⏳ Reintentando en {self.reconnect_delay}s...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    logger.critical("🚨 Máximo de reintentos alcanzado. Abortando.")
                    return False
        
        return False
    
    async def listen(self):
        """Loop principal de escucha de mensajes"""
        self.running = True
        
        while self.running:
            try:
                # Intentar conectar si no hay conexión
                if not self.ws or self.ws.closed:
                    if not await self.connect():
                        break
                
                # Recibir mensaje
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Callback con el mensaje
                await self.on_message(data)
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️  Conexión cerrada. Reconectando...")
                self.ws = None
                await asyncio.sleep(self.reconnect_delay)
                
            except json.JSONDecodeError as e:
                logger.error(f"Error decodificando JSON: {e}")
                
            except Exception as e:
                logger.error(f"Error en WebSocket: {e}")
                if self.on_error:
                    await self.on_error(e)
                
                # Forzar reconexión
                self.ws = None
                await asyncio.sleep(self.reconnect_delay)
    
    async def send(self, data: dict):
        """Envía datos por el WebSocket"""
        if self.ws and not self.ws.closed:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Error enviando datos: {e}")
        else:
            logger.warning("No se puede enviar. WebSocket no conectado.")
    
    async def close(self):
        """Cierra la conexión limpiamente"""
        self.running = False
        if self.ws and not self.ws.closed:
            await self.ws.close()
            logger.info("WebSocket cerrado correctamente")
            
            if self.on_close:
                await self.on_close()
