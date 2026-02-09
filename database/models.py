"""
🐺 BASE DE DATOS - Modelos SQLite
Almacena señales históricas y estadísticas
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SignalsDatabase:
    """
    Base de datos para almacenar señales del Oráculo
    """
    
    def __init__(self, db_path: str = "database/oraculo.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Inicializa las tablas si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de señales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                price REAL,
                score INTEGER,
                classification TEXT,
                rvol REAL,
                cvd_divergence BOOLEAN,
                buy_sell_ratio REAL,
                icebergs INTEGER,
                bb_squeeze BOOLEAN,
                imbalance_pct REAL,
                action TEXT,
                indicators_json TEXT
            )
        """)
        
        # Tabla de estadísticas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_pairs_scanned INTEGER,
                signals_detected INTEGER,
                high_score_signals INTEGER,
                avg_score REAL
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON signals(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON signals(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON signals(score)")
        
        conn.commit()
        conn.close()
    
    def save_signal(self, signal: Dict) -> int:
        """
        Guarda una señal en la base de datos
        
        Args:
            signal: Dict con datos de la señal
            
        Returns:
            ID de la señal insertada
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indicators = signal.get('indicators', {})
        
        cursor.execute("""
            INSERT INTO signals (
                symbol, price, score, classification,
                rvol, cvd_divergence, buy_sell_ratio,
                icebergs, bb_squeeze, imbalance_pct,
                action, indicators_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.get('symbol'),
            signal.get('price'),
            signal.get('score'),
            signal.get('classification'),
            indicators.get('rvol'),
            indicators.get('cvd_divergence'),
            indicators.get('buy_sell_ratio'),
            indicators.get('icebergs'),
            indicators.get('bb_squeeze'),
            signal.get('imbalance', {}).get('imbalance_pct'),
            signal.get('action'),
            json.dumps(signal, default=str)  # Usar default=str para manejar datetime y otros tipos
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return signal_id
    
    def get_latest_signals(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene las últimas señales
        
        Args:
            limit: Número máximo de señales
            
        Returns:
            Lista de señales
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, timestamp, price, score, classification,
                   rvol, cvd_divergence, buy_sell_ratio, icebergs,
                   bb_squeeze, imbalance_pct, action
            FROM signals
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'symbol': row[1],
                'timestamp': row[2],
                'price': row[3],
                'score': row[4],
                'classification': row[5],
                'indicators': {
                    'rvol': row[6],
                    'cvd_divergence': bool(row[7]),
                    'buy_sell_ratio': row[8],
                    'icebergs': row[9],
                    'bb_squeeze': bool(row[10])
                },
                'imbalance': {
                    'imbalance_pct': row[11]
                },
                'action': row[12]
            })
        
        return signals
    
    def get_top_signals(self, limit: int = 10, hours: int = 24) -> List[Dict]:
        """
        Obtiene las mejores señales de las últimas X horas
        
        Args:
            limit: Número máximo
            hours: Horas hacia atrás
            
        Returns:
            Lista de señales ordenadas por score
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, symbol, timestamp, price, score, classification,
                   rvol, cvd_divergence, buy_sell_ratio, icebergs,
                   bb_squeeze, imbalance_pct, action
            FROM signals
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY score DESC
            LIMIT ?
        """.format(hours), (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'symbol': row[1],
                'timestamp': row[2],
                'price': row[3],
                'score': row[4],
                'classification': row[5],
                'indicators': {
                    'rvol': row[6],
                    'cvd_divergence': bool(row[7]),
                    'buy_sell_ratio': row[8],
                    'icebergs': row[9],
                    'bb_squeeze': bool(row[10])
                },
                'imbalance': {
                    'imbalance_pct': row[11]
                },
                'action': row[12]
            })
        
        return signals
    
    def save_stats(self, stats: Dict) -> int:
        """Guarda estadísticas del escaneo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stats (
                total_pairs_scanned, signals_detected,
                high_score_signals, avg_score
            ) VALUES (?, ?, ?, ?)
        """, (
            stats.get('total_pairs_scanned'),
            stats.get('signals_detected'),
            stats.get('high_score_signals'),
            stats.get('avg_score')
        ))
        
        stats_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return stats_id
    
    def get_stats_summary(self) -> Dict:
        """Obtiene resumen de estadísticas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de señales
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_signals = cursor.fetchone()[0]
        
        # Señales últimas 24h
        cursor.execute("""
            SELECT COUNT(*) FROM signals
            WHERE timestamp >= datetime('now', '-24 hours')
        """)
        signals_24h = cursor.fetchone()[0]
        
        # Score promedio
        cursor.execute("""
            SELECT AVG(score) FROM signals
            WHERE timestamp >= datetime('now', '-24 hours')
        """)
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_signals': total_signals,
            'signals_24h': signals_24h,
            'avg_score': round(avg_score, 2)
        }
