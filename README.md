# 🐺 PROYECTO ORÁCULO

**Sistema de Detección de Oportunidades Cripto Antes que el Mercado**

## 📋 Descripción

El **Proyecto Oráculo** es una suite de robots en Python que escanea Binance (y otros CEX vía CCXT) en tiempo real para detectar anomalías invisibles al ojo humano.

### 🎯 Capacidades

El sistema tiene dos salidas principales:

1. **"Las Elegidas"** - Reporte diario de monedas en fase de acumulación silenciosa
2. **"Disparos de Francotirador"** - Alertas real-time para entrada inmediata

## 🏗️ Arquitectura

```
oraculo-scanner/
├── main.py                 # Entry point
├── config.py              # Configuración global
├── requirements.txt       # Dependencias
├── .env.example          # Template de variables de entorno
├── README.md             # Esta documentación
│
├── core/                 # Motores principales
│   ├── scanner.py        # MarketScanner (Detección RVol)
│   ├── order_flow.py     # OrderFlowAnalyzer (CVD + Divergencias)
│   ├── signals.py        # SignalDetector (Sistema de puntuación)
│   └── indicators.py     # TechnicalIndicators (Bollinger, RSI, etc.)
│
├── utils/                # Utilidades
│   ├── logging_config.py # Sistema de logs con colores
│   └── websocket_manager.py  # Gestión de WebSockets
│
└── data/
    ├── reports/          # Reportes generados
    └── oraculo.log       # Archivo de log
```

## ⚙️ Componentes Técnicos

### 1️⃣ **MarketScanner** (TAREA 1)

Detecta **Unusual Relative Volume (RVol)**

**Fórmula:**
```
RVol = Volumen_Actual / SMA_Volumen_24h

Señal: RVol > 5x
```

**Características:**
- Conexión async a Binance Spot
- Filtra pares por volumen mínimo (>100K USD)
- Excluye stablecoins y leveraged tokens
- Vectorización con pandas/numpy (sin bucles lentos)

### 2️⃣ **OrderFlowAnalyzer** (TAREA 2)

Analiza el flujo de órdenes para detectar **acumulación institucional**

**Métricas:**
- **CVD (Cumulative Volume Delta)**: Σ(Buy Volume - Sell Volume)
- **Divergencias Alcistas**: Precio baja, CVD sube → Smart Money acumulando
- **Icebergs**: Órdenes grandes ocultas en el order book (> 3σ)

**Algoritmo de Divergencia:**
```python
if precio_actual < precio_pasado AND cvd_actual > cvd_pasado:
    → SEÑAL DE COMPRA (Absorción Pasiva)
```

### 3️⃣ **SignalDetector** (TAREA 3)

Sistema de puntuación que combina todos los indicadores

**Score 0-100:**
- RVol > 5x: **+30 puntos**
- Divergencia Alcista: **+40 puntos**
- Bollinger Squeeze: **+20 puntos**
- Icebergs detectados: **+10 puntos**

**Clasificación:**
- **🔴 Score > 80**: DISPARO DE FRANCOTIRADOR (entrada inmediata)
- **🟡 Score 60-79**: VIGILANCIA ESTRECHA
- **🟢 Score 40-59**: ACUMULACIÓN SILENCIOSA ("Las Elegidas")
- **⚪ Score < 40**: RUIDO (ignorar)

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
cd /ruta/proyecto
```

### 2. Crear entorno virtual (recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

**⚠️ Nota sobre TA-Lib:**

Si `ta-lib` falla al instalar, en macOS ejecuta:
```bash
brew install ta-lib
```

En Linux:
```bash
sudo apt-get install ta-lib
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
nano .env  # Edita según tus necesidades
```

## 📖 Uso

### Modo 1: Escaneo Único (Testing)
```bash
python main.py single
```
Ejecuta un escaneo completo y genera un reporte.

### Modo 2: Monitoreo Continuo (Producción)
```bash
python main.py continuous
```
Escanea el mercado cada 60 segundos (configurable en `.env`).

### Modo 3: Reporte Diario "Las Elegidas"
```bash
python main.py report
```
Genera el reporte diario de monedas con compresión de volatilidad.

## 📊 Ejemplo de Salida

```
════════════════════════════════════════════════════════════════
🔴 DISPARO DE FRANCOTIRADOR
════════════════════════════════════════════════════════════════
💎 Par: SOL/USDT
📊 Score: 85/100
💰 Precio: $142.567000

📈 Indicadores:
   • rvol: 8.3
   • cvd_divergence: True
   • buy_sell_ratio: 1.87
   • icebergs: 2
   • bb_squeeze: True

🎯 Acción Recomendada:
   COMPRA INMEDIATA - Entrada agresiva con stop loss ajustado
════════════════════════════════════════════════════════════════
```

## 🧠 Matemática Anti-Falsos Positivos

### Filtro 1: Volumen Mínimo
```
Solo pares con volumen_24h > 100,000 USD
→ Elimina shitcoins ilíquidos
```

### Filtro 2: Velas Mínimas
```
Requiere > 100 velas históricas
→ Evita datos insuficientes
```

### Filtro 3: Confirmación Múltiple
```
Score alto requiere 3+ indicadores alineados
→ Reduce ruido del mercado
```

### Filtro 4: Análisis de Desviación
```
Icebergs: cantidad > (μ + 3σ)
→ Solo detecta verdaderas anomalías estadísticas
```

## 🔐 Seguridad

- **NO requiere API keys** para funciones de lectura (datos públicos)
- Si usas funciones avanzadas (trading futuro), usa `.env` y **NUNCA** subas las keys a GitHub
- Añade `.env` a `.gitignore`

## 🛠️ Configuración Avanzada

Edita `config.py` para ajustar:

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `RVOL_THRESHOLD` | 5.0 | Umbral de volumen relativo |
| `CVD_DIVERGENCE_LOOKBACK` | 20 | Velas para detectar divergencias |
| `BB_SQUEEZE_THRESHOLD` | 0.02 | Umbral de compresión BB (2%) |
| `SCAN_INTERVAL` | 60 | Segundos entre escaneos |
| `MIN_VOLUME_USD` | 100000 | Volumen mínimo 24h |

## 📈 Próximos Pasos

### Fase 1: MVP Standalone ✅
- [x] MarketScanner con RVol
- [x] OrderFlowAnalyzer con CVD
- [x] SignalDetector con scoring
- [x] Sistema de reportes

### Fase 2: Backend API (Próximamente)
- [ ] FastAPI con endpoints REST
- [ ] PostgreSQL para histórico
- [ ] Sistema de alertas Telegram

### Fase 3: Integración Wolfsfera (Futuro)
- [ ] Dashboard público `/oraculo`
- [ ] WebSocket para alertas live
- [ ] Track record público

## 🐛 Troubleshooting

### Error: "No module named 'ccxt'"
```bash
pip install ccxt
```

### Error: "WebSocket connection failed"
```bash
# Verifica tu conexión a internet
# Binance puede estar bloqueado en tu país (usa VPN)
```

### Error: "TA-Lib not found"
```bash
# macOS
brew install ta-lib
pip install TA-Lib

# Linux
sudo apt-get install ta-lib
pip install TA-Lib
```

## 📜 Licencia

Proyecto privado - Wolfsfera Ecosystem

## 🤝 Contribuciones

Este es un proyecto interno. Para sugerencias, contacta al equipo de desarrollo.

---

**Desarrollado con 🐺 por el WolfPack**

*"No puedes construir un imperio financiero con herramientas de juguete"*
