"""
🐺 ORÁCULO API SERVER
FastAPI backend con REST + WebSocket

Endpoints:
- GET /api/signals - Últimas señales
- GET /api/signals/top - Top señales por score
- GET /api/stats - Estadísticas
- WebSocket /ws - Updates en tiempo real
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.scanner import MarketScanner
from core.order_flow import OrderFlowAnalyzer
from core.imbalance import OrderBookImbalanceAnalyzer
from core.signals import SignalDetector
from database.models import SignalsDatabase
from utils.logging_config import setup_logger
from config import SCAN_INTERVAL

logger = setup_logger('api')

# Estado global
scanner_engine = None
db = SignalsDatabase()
connected_clients: List[WebSocket] = []
latest_signals: List[Dict] = []


class OraculoAPIEngine:
    """Motor del Oráculo para API"""
    
    def __init__(self):
        self.scanner = MarketScanner()
        self.order_flow = OrderFlowAnalyzer()
        self.imbalance = OrderBookImbalanceAnalyzer()
        self.signal_detector = SignalDetector()
        self.running = False
    
    async def initialize(self):
        """Inicializa el scanner"""
        await self.scanner.initialize()
        logger.info(f"✅ Scanner inicializado con {len(self.scanner.active_pairs)} pares")
    
    async def scan_and_save(self):
        """Escanea y guarda en DB"""
        global latest_signals
        
        try:
            # Escanear
            rvol_signals = await self.scanner.scan_all_pairs()
            
            if not rvol_signals:
                return []
            
            all_signals = []
            
            # Analizar top 20
            for rvol_signal in rvol_signals[:20]:
                symbol = rvol_signal['symbol']
                
                # Order flow
                orderflow_data = await self.order_flow.analyze_pair(symbol)
                
                # Imbalance
                imbalance_data = await self.imbalance.get_orderbook_imbalance(symbol)
                
                # Precio
                price_df = await self.scanner.fetch_historical_volume(symbol)
                
                # Generar señal
                signal = self.signal_detector.generate_signal(
                    symbol=symbol,
                    rvol_data=rvol_signal,
                    orderflow_data=orderflow_data,
                    price_df=price_df
                )
                
                signal['imbalance'] = imbalance_data
                
                # Guardar en DB
                db.save_signal(signal)
                
                all_signals.append(signal)
            
            # Actualizar cache
            latest_signals = sorted(all_signals, key=lambda x: x.get('score', 0), reverse=True)
            
            # Notificar clientes WebSocket
            await broadcast_signals(latest_signals)
            
            logger.info(f"✅ {len(all_signals)} señales procesadas y guardadas")
            
            return latest_signals
            
        except Exception as e:
            logger.error(f"Error en scan_and_save: {e}")
            return []
    
    async def run_continuous(self):
        """Loop de escaneo continuo"""
        self.running = True
        
        while self.running:
            await self.scan_and_save()
            await asyncio.sleep(SCAN_INTERVAL)
    
    async def shutdown(self):
        """Cierra conexiones"""
        self.running = False
        await self.scanner.close()
        await self.order_flow.close()
        await self.imbalance.close()


# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la app"""
    global scanner_engine
    
    # Startup
    logger.info("🚀 Iniciando Oráculo API...")
    scanner_engine = OraculoAPIEngine()
    await scanner_engine.initialize()
    
    # Iniciar scanner en background
    asyncio.create_task(scanner_engine.run_continuous())
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando Oráculo API...")
    await scanner_engine.shutdown()


# FastAPI App
app = FastAPI(
    title="Oráculo API",
    description="Sistema de detección de oportunidades cripto en tiempo real",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://www.wolfsfera.com",
        "https://wolfsfera.com",
        "https://wolfsfera-hub.vercel.app", 
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ENDPOINTS REST
# ============================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "name": "Oráculo API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/signals")
async def get_signals(limit: int = 10):
    """
    Obtiene las últimas señales
    
    Args:
        limit: Número máximo de señales
    """
    if latest_signals:
        return {
            "success": True,
            "count": len(latest_signals[:limit]),
            "signals": latest_signals[:limit],
            "timestamp": datetime.now().isoformat()
        }
    
    # Si no hay en cache, obtener de DB
    signals = db.get_latest_signals(limit)
    return {
        "success": True,
        "count": len(signals),
        "signals": signals,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/signals/top")
async def get_top_signals(limit: int = 10, hours: int = 24):
    """
    Obtiene las mejores señales
    
    Args:
        limit: Número máximo
        hours: Horas hacia atrás
    """
    signals = db.get_top_signals(limit, hours)
    return {
        "success": True,
        "count": len(signals),
        "signals": signals,
        "period_hours": hours,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Obtiene estadísticas del sistema"""
    stats = db.get_stats_summary()
    
    # Añadir info en tiempo real
    stats.update({
        "pairs_monitored": len(scanner_engine.scanner.active_pairs) if scanner_engine else 0,
        "active_signals": len(latest_signals),
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "stats": stats
    }


# ============================================
# WEBSOCKET
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para updates en tiempo real
    
    Envía señales cuando se detectan nuevas
    """
    await websocket.accept()
    connected_clients.append(websocket)
    
    logger.info(f"🔌 Cliente WebSocket conectado ({len(connected_clients)} activos)")
    
    try:
        # Enviar señales actuales al conectar
        await websocket.send_json({
            "type": "initial",
            "signals": latest_signals,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener conexión
        while True:
            # Esperar mensajes del cliente (ping/pong)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"🔌 Cliente WebSocket desconectado ({len(connected_clients)} activos)")


async def broadcast_signals(signals: List[Dict]):
    """
    Envía señales a todos los clientes WebSocket conectados
    
    Args:
        signals: Lista de señales a enviar
    """
    if not connected_clients:
        return
    
    message = {
        "type": "update",
        "signals": signals,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = []
    
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.error(f"Error enviando a cliente: {e}")
            disconnected.append(client)
    
    # Limpiar clientes desconectados
    for client in disconnected:
        connected_clients.remove(client)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
