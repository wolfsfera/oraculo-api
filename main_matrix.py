"""
🐺 PROYECTO ORÁCULO - Matrix Dashboard Mode
Versión con visualización tipo Matrix en terminal

Uso:
    python main_matrix.py
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Dict

from core.scanner import MarketScanner
from core.order_flow import OrderFlowAnalyzer
from core.imbalance import OrderBookImbalanceAnalyzer
from core.signals import SignalDetector
from utils.dashboard import MatrixDashboard
from config import SCAN_INTERVAL
from utils.logging_config import setup_logger

logger = setup_logger('matrix')


class OraculoMatrixEngine:
    """
    Motor del Oráculo con Dashboard Visual tipo Matrix
    """
    
    def __init__(self):
        self.scanner = MarketScanner()
        self.order_flow = OrderFlowAnalyzer()
        self.imbalance_analyzer = OrderBookImbalanceAnalyzer()
        self.signal_detector = SignalDetector()
        self.dashboard = MatrixDashboard()
        self.running = False
    
    async def initialize(self):
        """Inicializa todos los componentes"""
        # Mostrar animación de inicio
        self.dashboard.show_startup_animation()
        
        try:
            await self.scanner.initialize()
        except Exception as e:
            logger.critical(f"❌ Error fatal en inicialización: {e}")
            raise
    
    async def scan_cycle_with_imbalance(self) -> List[Dict]:
        """
        Ciclo de escaneo que incluye análisis de imbalance
        
        Returns:
            Lista de señales con todos los datos
        """
        try:
            # PASO 1: Detectar volumen anómalo
            rvol_signals = await self.scanner.scan_all_pairs()
            
            if not rvol_signals:
                return []
            
            all_signals = []
            
            # PASO 2: Analizar cada par detectado
            for rvol_signal in rvol_signals[:10]:  # Top 10 para dashboard
                symbol = rvol_signal['symbol']
                
                # Order Flow (CVD + Divergencias)
                orderflow_data = await self.order_flow.analyze_pair(symbol)
                
                # Order Book Imbalance
                imbalance_data = await self.imbalance_analyzer.get_orderbook_imbalance(symbol)
                
                # Precio histórico
                price_df = await self.scanner.fetch_historical_volume(symbol)
                
                # Generar señal completa
                signal = self.signal_detector.generate_signal(
                    symbol=symbol,
                    rvol_data=rvol_signal,
                    orderflow_data=orderflow_data,
                    price_df=price_df
                )
                
                # Añadir datos de imbalance
                signal['imbalance'] = imbalance_data
                
                all_signals.append(signal)
            
            # Ordenar por score
            all_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            return all_signals
            
        except Exception as e:
            logger.error(f"Error en ciclo de escaneo: {e}")
            return []
    
    async def run_matrix_mode(self):
        """
        Ejecuta el Oráculo en modo Matrix (Dashboard visual)
        """
        self.running = True
        
        try:
            while self.running:
                # Escanear mercado
                signals = await self.scan_cycle_with_imbalance()
                
                # Actualizar dashboard
                self.dashboard.update_signals(signals)
                
                # Esperar próximo ciclo
                await asyncio.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            self.dashboard.clear_screen()
            print("\n🛑 Oráculo detenido por el usuario\n")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Cierra todos los componentes"""
        await self.scanner.close()
        await self.order_flow.close()
        await self.imbalance_analyzer.close()


# ============================================
# PUNTO DE ENTRADA
# ============================================
async def main():
    """Entry point para modo Matrix"""
    engine = OraculoMatrixEngine()
    
    try:
        await engine.initialize()
        await engine.run_matrix_mode()
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
