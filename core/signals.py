"""
🐺 SIGNAL DETECTOR
Sistema de señales que combina todos los análisis

Genera:
1. "Las Elegidas" - Acumulación silenciosa (reporte diario)
2. "Disparos de Francotirador" - Alertas real-time
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime
import json

from core.indicators import TechnicalIndicators
from utils.logging_config import setup_logger

logger = setup_logger('signals')


class SignalDetector:
    """
    Motor de señales que combina RVol, CVD y compresión de volatilidad
    
    Puntuación de Señal (0-100):
    - RVol > 5x: +30 puntos
    - Divergencia Alcista CVD: +40 puntos
    - BB Squeeze: +20 puntos
    - Icebergs detectados: +10 puntos
    """
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.signals_history: List[Dict] = []
    
    def calculate_signal_score(
        self,
        rvol_signal: Dict,
        orderflow_analysis: Dict,
        price_df: pd.DataFrame
    ) -> int:
        """
        Calcula puntuación de señal (0-100)
        
        Args:
            rvol_signal: Resultado del scanner (RVol)
            orderflow_analysis: Resultado del order flow analyzer
            price_df: DataFrame con OHLCV
            
        Returns:
            Score 0-100
        """
        score = 0
        
        # ✅ CRITERIO 1: Volumen Relativo Anómalo (30 pts)
        if rvol_signal and rvol_signal.get('rvol', 0) >= 5:
            rvol = rvol_signal['rvol']
            # Más peso si el spike es muy fuerte
            if rvol >= 10:
                score += 30
            elif rvol >= 7:
                score += 25
            else:
                score += 20
        
        # ✅ CRITERIO 2: Divergencia Alcista CVD (40 pts)
        if orderflow_analysis.get('bullish_divergence'):
            score += 40
            
            # Bonus si hay ratio compras/ventas fuerte
            buy_sell_ratio = orderflow_analysis.get('buy_sell_ratio', 1)
            if buy_sell_ratio > 1.5:
                score += 5
        
        # ✅ CRITERIO 3: Compresión de Volatilidad (20 pts)
        if not price_df.empty:
            has_squeeze = self.indicators.detect_bb_squeeze(price_df)
            if has_squeeze:
                score += 20
        
        # ✅ CRITERIO 4: Icebergs en Order Book (10 pts)
        if orderflow_analysis.get('icebergs_detected', 0) > 0:
            score += 10
        
        return min(score, 100)  # Cap a 100
    
    def classify_signal(self, score: int) -> str:
        """
        Clasifica la señal según su puntuación
        
        Args:
            score: Puntuación 0-100
            
        Returns:
            Clasificación de la señal
        """
        if score >= 80:
            return "🔴 DISPARO DE FRANCOTIRADOR"  # Entrada inmediata
        elif score >= 60:
            return "🟡 VIGILANCIA ESTRECHA"  # Monitorear de cerca
        elif score >= 40:
            return "🟢 ACUMULACIÓN SILENCIOSA"  # Las Elegidas
        else:
            return "⚪ RUIDO"  # Ignorar
    
    def generate_signal(
        self,
        symbol: str,
        rvol_data: Dict,
        orderflow_data: Dict,
        price_df: pd.DataFrame
    ) -> Dict:
        """
        Genera señal completa con toda la información
        
        Returns:
            Señal estructurada
        """
        score = self.calculate_signal_score(rvol_data, orderflow_data, price_df)
        classification = self.classify_signal(score)
        
        signal = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'classification': classification,
            'price': rvol_data.get('price', 0) if rvol_data else orderflow_data.get('price', 0),
            'indicators': {
                'rvol': float(rvol_data.get('rvol', 0)) if rvol_data else 0,
                'cvd_divergence': bool(orderflow_data.get('bullish_divergence', False)),
                'buy_sell_ratio': float(orderflow_data.get('buy_sell_ratio', 0)),
                'icebergs': int(orderflow_data.get('icebergs_detected', 0)),
                'bb_squeeze': bool(self.indicators.detect_bb_squeeze(price_df)) if not price_df.empty else False
            },
            'action': self._get_action_recommendation(score)
        }
        
        # Guardar en historial
        self.signals_history.append(signal)
        
        return signal
    
    def _get_action_recommendation(self, score: int) -> str:
        """Genera recomendación de acción según el score"""
        if score >= 80:
            return "COMPRA INMEDIATA - Entrada agresiva con stop loss ajustado"
        elif score >= 60:
            return "PREPARAR ENTRADA - Esperar confirmación en gráfico de 15m"
        elif score >= 40:
            return "ACUMULAR GRADUALMENTE - Ideal para DCA en próximas 24-48h"
        else:
            return "SIN ACCIÓN - Seguir monitoreando"
    
    def get_top_signals(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene las mejores señales del historial
        
        Args:
            limit: Número máximo de señales a retornar
            
        Returns:
            Lista ordenada por score
        """
        sorted_signals = sorted(
            self.signals_history,
            key=lambda x: x['score'],
            reverse=True
        )
        return sorted_signals[:limit]
    
    def save_signals_to_file(self, filename: str = None):
        """Guarda señales en archivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/reports/signals_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.signals_history, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Señales guardadas en {filename}")
        except Exception as e:
            logger.error(f"Error guardando señales: {e}")
    
    def print_signal_alert(self, signal: Dict):
        """Imprime alerta formateada en consola"""
        symbol = signal['symbol']
        score = signal['score']
        classification = signal['classification']
        price = signal['price']
        action = signal['action']
        
        print("\n" + "="*80)
        print(f"{classification}")
        print("="*80)
        print(f"💎 Par: {symbol}")
        print(f"📊 Score: {score}/100")
        print(f"💰 Precio: ${price:.6f}")
        print(f"\n📈 Indicadores:")
        for key, value in signal['indicators'].items():
            print(f"   • {key}: {value}")
        print(f"\n🎯 Acción Recomendada:")
        print(f"   {action}")
        print("="*80 + "\n")
