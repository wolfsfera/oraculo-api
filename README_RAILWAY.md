# 🐺 Oráculo API - Railway Deployment

Sistema de detección de oportunidades cripto en tiempo real.

## 🚀 Deploy en Railway

### Paso 1: Crear proyecto en Railway
```
1. Ve a https://railway.app
2. Click "New Project"
3. Selecciona "Deploy from GitHub repo"
```

### Paso 2: Variables de Entorno

Configura estas variables en Railway:

```env
# Opcional - API keys de Binance (no necesarias por ahora, el modo público funciona)
# BINANCE_API_KEY=tu_api_key  
# BINANCE_API_SECRET=tu_api_secret

# Configuración del Scanner
RVOL_THRESHOLD=5.0
VOLUME_LOOKBACK_HOURS=24
MIN_CANDLES_REQUIRED=100
SCAN_INTERVAL=60
QUOTE_CURRENCIES=USDT,USDC
MIN_VOLUME_USD=100000
DEBUG=False
```

### Paso 3: Deploy

Railway detectará automáticamente:
- `Procfile` → Comando de inicio
- `requirements.txt` → Dependencias Python
- `runtime.txt` → Versión de Python

El deploy es automático.

## 📊 Endpoints Disponibles

Una vez desplegado, tendrás:

```
GET https://tu-app.railway.app/
GET https://tu-app.railway.app/api/signals
GET https://tu-app.railway.app/api/signals/top
GET https://tu-app.railway.app/api/stats
WebSocket wss://tu-app.railway.app/ws
```

## 🔧 Post-Deploy

1. Copia la URL de tu aplicación en Railway
2. Actualiza el frontend en `wolfsfera-hub/src/app/oraculo/page.tsx`:
   ```typescript
   const API_URL = 'https://tu-app.railway.app';
   ```
3. Redeploy el frontend en Vercel

## 📈 Monitoreo

Railway te dará:
- Logs en tiempo real
- Métricas de CPU/RAM
- Health checks automáticos

## ⚠️ Notas Importantes

- **TA-Lib**: Si falla la instalación, Railway puede necesitar configuración adicional
- **Memory**: El scanner usa ~200-300MB de RAM
- **Requests API**: Binance tiene rate limits, respétalos

## 🐺 Soporte

Cualquier problema, revisa los logs en Railway Dashboard.

**Hecho con 🐺 por WolfPack**
