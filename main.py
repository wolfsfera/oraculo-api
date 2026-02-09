"""
🐺 PROYECTO ORÁCULO - Main Entry Point
Sistema de detección de oportunidades cripto antes que el mercado

Ejecuta:
1. MarketScanner - Detecta volumen anómalo
2. OrderFlowAnalyzer - Analiza CVD y divergencias
3. SignalDetector - Genera señales puntuadas

Uso:
    python main.py
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Dict

from core.scanner import MarketScanner
from core.order_flow import OrderFlowAnalyzer
from core.signals import SignalDetector
from config import SCAN_INTERVAL
from utils.logging_config import setup_logger

logger = setup_logger('main')


class OraculoEngine:
    """
    Motor principal del Oráculo
    Coordina todos los componentes del sistema
    """
    
    def __init__(self):
        self.scanner = MarketScanner()
        self.order_flow = OrderFlowAnalyzer()
        self.signal_detector = SignalDetector()
        self.running = False
    
    async def initialize(self):
        """Inicializa todos los componentes"""
        logger.info("🐺 Inicializando PROYECTO ORÁCULO...")
        logger.info("="*80)
        
        try:
            await self.scanner.initialize()
            logger.info("✅ Todos los sistemas operativos")
        except Exception as e:
            logger.critical(f"❌ Error fatal en inicialización: {e}")
            raise
    
    async def scan_cycle(self):
        """
        Un ciclo completo de escaneo
        
        Pasos:
        1. Scanner detecta pares con RVol > 5x
        2. Para cada par detectado, analiza order flow
        3. Genera señal con puntuación
        4. Alerta si score > 60
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 NUEVO CICLO DE ESCANEO - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'='*80}\n")
        
        try:
            # ============================================
            # PASO 1: DETECTAR VOLUMEN ANÓMALO
            # ============================================
            rvol_signals = await self.scanner.scan_all_pairs()
            
            if not rvol_signals:
                logger.info("ℹ️  No se detectaron anomalías de volumen en este ciclo")
                return
            
            logger.info(f"📊 {len(rvol_signals)} pares con volumen anómalo detectados")
            
            # ============================================
            # PASO 2: ANALIZAR ORDER FLOW EN PARES DETECTADOS
            # ============================================
            for rvol_signal in rvol_signals:
                symbol = rvol_signal['symbol']
                
                logger.info(f"\n🔬 Analizando order flow de {symbol}...")
                
                # Análisis profundo
                orderflow_data = await self.order_flow.analyze_pair(symbol)
                
                # Obtener precio actualizado
                price_df = await self.scanner.fetch_historical_volume(symbol)
                
                # ============================================
                # PASO 3: GENERAR SEÑAL
                # ============================================
                signal = self.signal_detector.generate_signal(
                    symbol=symbol,
                    rvol_data=rvol_signal,
                    orderflow_data=orderflow_data,
                    price_df=price_df
                )
                
                # ============================================
                # PASO 4: ALERTAR SI ES SEÑAL FUERTE
                # ============================================
                if signal['score'] >= 60:
                    self.signal_detector.print_signal_alert(signal)
                else:
                    logger.info(f"   Score: {signal['score']}/100 - {signal['classification']}")
        
        except Exception as e:
            logger.error(f"❌ Error en ciclo de escaneo: {e}", exc_info=True)
    
    async def run_continuous(self):
        """
        Ejecuta el scanner en modo continuo
        Escanea cada X segundos (configurable)
        """
        self.running = True
        logger.info(f"🚀 ORÁCULO ACTIVADO - Escaneando cada {SCAN_INTERVAL}s")
        logger.info("   Presiona Ctrl+C para detener")
        
        try:
            while self.running:
                await self.scan_cycle()
                
                logger.info(f"\n⏸️  Esperando {SCAN_INTERVAL}s hasta próximo escaneo...\n")
                await asyncio.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupción detectada. Cerrando...")
        finally:
            await self.shutdown()
    
    async def run_single_scan(self):
        """Ejecuta un único escaneo (modo test)"""
        logger.info("🔍 Ejecutando escaneo único...")
        await self.scan_cycle()
        
        # Mostrar resumen
        top_signals = self.signal_detector.get_top_signals(limit=5)
        
        if top_signals:
            logger.info(f"\n📊 TOP 5 SEÑALES DEL ESCANEO:")
            for i, signal in enumerate(top_signals, 1):
                logger.info(
                    f"   {i}. {signal['symbol']} - "
                    f"Score: {signal['score']}/100 - "
                    f"{signal['classification']}"
                )
        
        # Guardar señales
        self.signal_detector.save_signals_to_file()
        
        await self.shutdown()
    
    async def generate_daily_report(self):
        """
        TAREA 3: Genera reporte diario "Las Elegidas"
        
        Busca patrones de:
        - Compresión de volatilidad (BB Squeeze)
        - Volumen decreciente
        - Acumulación silenciosa
        """
        logger.info("📋 GENERANDO REPORTE DIARIO - LAS ELEGIDAS")
        logger.info("="*80)
        
        all_signals = []
        
        # Escanear todos los pares
        for symbol in list(self.scanner.active_pairs)[:50]:  # Limitar para demo
            try:
                # Obtener datos
                price_df = await self.scanner.fetch_historical_volume(symbol)
                
                if price_df.empty:
                    continue
                
                # Detectar compresión de Bollinger Bands
                from core.indicators import TechnicalIndicators
                indicators = TechnicalIndicators()
                
                has_squeeze = indicators.detect_bb_squeeze(price_df)
                
                # Si hay squeeze, analizar más profundo
                if has_squeeze:
                    orderflow = await self.order_flow.analyze_pair(symbol)
                    
                    signal = {
                        'symbol': symbol,
                        'price': price_df['close'].iloc[-1],
                        'bb_squeeze': True,
                        'buy_sell_ratio': orderflow.get('buy_sell_ratio', 0),
                        'timestamp': datetime.now()
                    }
                    
                    all_signals.append(signal)
                    logger.info(f"✅ {symbol} - Compresión detectada")
                    
            except Exception as e:
                logger.debug(f"Error procesando {symbol}: {e}")
        
        # Ordenar por ratio compras/ventas
        all_signals.sort(key=lambda x: x.get('buy_sell_ratio', 0), reverse=True)
        
        # Mostrar top 10
        logger.info(f"\n🏆 TOP 10 'LAS ELEGIDAS' - Acumulación Silenciosa:")
        for i, sig in enumerate(all_signals[:10], 1):
            logger.info(
                f"   {i}. {sig['symbol']} - "
                f"Precio: ${sig['price']:.6f} - "
                f"Buy/Sell: {sig.get('buy_sell_ratio', 0):.2f}"
            )
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"data/reports/las_elegidas_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(all_signals[:10], f, indent=2, default=str)
        
        logger.info(f"\n💾 Reporte guardado en: {filename}")
        
        await self.shutdown()
    
    async def shutdown(self):
        """Cierra todos los componentes limpiamente"""
        logger.info("🔌 Cerrando conexiones...")
        await self.scanner.close()
        await self.order_flow.close()
        logger.info("✅ Shutdown completado")


# ============================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================
async def main():
    """Entry point"""
    engine = OraculoEngine()
    
    try:
        await engine.initialize()
        
        # Parsear argumentos
        if len(sys.argv) > 1:
            mode = sys.argv[1]
            
            if mode == 'continuous':
                await engine.run_continuous()
            elif mode == 'report':
                await engine.generate_daily_report()
            elif mode == 'single':
                await engine.run_single_scan()
            else:
                logger.error(f"Modo desconocido: {mode}")
                logger.info("Modos disponibles: continuous | single | report")
        else:
            # Por defecto: escaneo único
            await engine.run_single_scan()
            
    except Exception as e:
        logger.critical(f"💥 Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║                                                   ║
    ║           🐺  PROYECTO ORÁCULO  🐺                ║
    ║                                                   ║
    ║   Sistema de Detección de Oportunidades Cripto   ║
    ║        Antes que el Mercado las Vea              ║
    ║                                                   ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    # Ejecutar
    asyncio.run(main())
