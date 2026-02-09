"""
🐺 DASHBOARD CLI TIPO MATRIX
Visualización en terminal con actualización en vivo

Muestra tabla actualizable con señales en tiempo real
"""

import os
import sys
from typing import List, Dict
from datetime import datetime
from tabulate import tabulate
from colorama import Fore, Back, Style, init

# Inicializar colorama
init(autoreset=True)


class MatrixDashboard:
    """
    Dashboard tipo Matrix que se actualiza sin parpadeos
    """
    
    def __init__(self):
        self.signals_cache: List[Dict] = []
    
    def clear_screen(self):
        """Limpia la pantalla según el OS"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self):
        """Imprime el header del dashboard"""
        width = 120
        
        print(Fore.CYAN + "="*width)
        print(Fore.GREEN + Style.BRIGHT + """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║            🐺  PROYECTO ORÁCULO - LIVE SCANNER  🐺             ║
    ║                                                               ║
    ║         Sistema de Detección de Oportunidades Cripto         ║
    ║                  Vigilancia en Tiempo Real                   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
        """ + Style.RESET_ALL)
        print(Fore.CYAN + "="*width)
        print(f"{Fore.WHITE}⏱  Última Actualización: {Fore.YELLOW}{datetime.now().strftime('%H:%M:%S')}")
        print(Fore.CYAN + "="*width + "\n")
    
    def update_signals(self, signals: List[Dict]):
        """
        Actualiza el dashboard con nuevas señales
        
        Args:
            signals: Lista de señales detectadas
        """
        self.signals_cache = signals
        self.render()
    
    def render(self):
        """Renderiza el dashboard completo"""
        self.clear_screen()
        self.print_header()
        
        if not self.signals_cache:
            print(f"{Fore.YELLOW}⏳ Esperando señales del mercado...")
            return
        
        # Preparar datos para la tabla
        table_data = []
        headers = [
            "SÍMBOLO",
            "PRECIO",
            "RVol",
            "CVD Δ",
            "IMBALANCE",
            "SCORE",
            "SEÑAL",
            "ACCIÓN"
        ]
        
        for signal in self.signals_cache:
            # Colores según score
            score = signal.get('score', 0)
            symbol = signal.get('symbol', 'N/A')
            price = signal.get('price', 0)
            
            # Clasificación con colores
            if score >= 80:
                signal_color = Fore.RED + Style.BRIGHT
                signal_text = "🔴 FRANCOTIRADOR"
            elif score >= 60:
                signal_color = Fore.YELLOW + Style.BRIGHT
                signal_text = "🟡 VIGILANCIA"
            elif score >= 40:
                signal_color = Fore.GREEN
                signal_text = "🟢 ACUMULACIÓN"
            else:
                signal_color = Fore.WHITE
                signal_text = "⚪ RUIDO"
            
            # Obtener indicadores
            indicators = signal.get('indicators', {})
            rvol = indicators.get('rvol', 0)
            cvd_div = "✓" if indicators.get('cvd_divergence', False) else "✗"
            
            # Imbalance (si existe)
            imbalance_data = signal.get('imbalance', {})
            imbalance_pct = imbalance_data.get('imbalance_pct', 0)
            
            # Color para imbalance
            if imbalance_pct > 20:
                imbalance_str = f"{Fore.GREEN}+{imbalance_pct:.1f}%"
            elif imbalance_pct < -20:
                imbalance_str = f"{Fore.RED}{imbalance_pct:.1f}%"
            else:
                imbalance_str = f"{Fore.WHITE}{imbalance_pct:.1f}%"
            
            # Acción
            action = signal.get('action', 'N/A')
            action_short = action.split('-')[0][:15] + "..." if len(action) > 15 else action
            
            row = [
                f"{Fore.CYAN}{symbol}",
                f"{Fore.WHITE}${price:.6f}",
                f"{Fore.MAGENTA}{rvol:.1f}x",
                f"{Fore.CYAN}{cvd_div}",
                imbalance_str,
                f"{signal_color}{score}/100",
                signal_text,
                f"{Fore.WHITE}{action_short}"
            ]
            
            table_data.append(row)
        
        # Imprimir tabla
        print(tabulate(
            table_data,
            headers=[f"{Fore.YELLOW}{h}" for h in headers],
            tablefmt="fancy_grid",
            stralign="center"
        ))
        
        # Footer con estadísticas
        self.print_footer()
    
    def print_footer(self):
        """Imprime estadísticas del footer"""
        total_signals = len(self.signals_cache)
        
        high_score = sum(1 for s in self.signals_cache if s.get('score', 0) >= 80)
        medium_score = sum(1 for s in self.signals_cache if 60 <= s.get('score', 0) < 80)
        low_score = sum(1 for s in self.signals_cache if 40 <= s.get('score', 0) < 60)
        
        print("\n" + Fore.CYAN + "="*120)
        print(f"{Fore.WHITE}📊 ESTADÍSTICAS:")
        print(f"   Total Señales: {Fore.YELLOW}{total_signals}")
        print(f"   🔴 Alta Prioridad (>80): {Fore.RED}{high_score}")
        print(f"   🟡 Media Prioridad (60-79): {Fore.YELLOW}{medium_score}")
        print(f"   🟢 Baja Prioridad (40-59): {Fore.GREEN}{low_score}")
        print(Fore.CYAN + "="*120)
        print(f"{Fore.WHITE}💡 Presiona {Fore.RED}Ctrl+C{Fore.WHITE} para detener")
    
    def show_startup_animation(self):
        """Animación de inicio tipo Matrix"""
        import time
        
        self.clear_screen()
        
        matrix_lines = [
            "Inicializando Oráculo...",
            "Conectando a Binance WebSocket...",
            "Cargando pares de trading...",
            "Activando análisis de flujo de órdenes...",
            "Calibrando detectores de anomalías...",
            "Sistema operativo."
        ]
        
        for line in matrix_lines:
            print(f"{Fore.GREEN}>>> {line}")
            time.sleep(0.3)
        
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.GREEN + Style.BRIGHT}✅ ORÁCULO ACTIVADO")
        print(f"{Fore.CYAN}{'='*50}\n")
        time.sleep(1)
