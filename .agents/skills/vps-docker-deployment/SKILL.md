---
name: vps-docker-deployment
description: Instrucciones y directrices para el aprovisionamiento, despliegue containerizado en Docker y optimización de latencia en VPS Low-Cost (Hetzner / DigitalOcean).
---

# 🐳 Skill: VPS Docker Deployment (`vps-docker-deployment`)

Esta habilidad detalla el procedimiento operativo para desplegar el servidor de inferencia de **Trading Signals ML** en un Servidor Privado Virtual (**VPS Low-Cost a ~$4.50/mes** en Hetzner Cloud o DigitalOcean), garantizando un **uptime del 99.99%**, conexiones **WebSocket ininterrumpidas** y **latencia $<5\text{ms}$** respecto a los servidores de Binance/Bybit.

---

## 🎯 Selección del Servidor VPS (Low-Cost)

1. **Proveedor Recomendado:**
   - **Hetzner Cloud (CX22 / CPX11):** ~€3.79 a €4.50 / mes (2 vCPU, 2GB RAM, 40GB NVMe SSD).
   - **DigitalOcean (Basic Droplet):** ~$6.00 / mes (1 vCPU, 1GB RAM, 25GB SSD).
2. **Ubicación Geográfica:**
   - **Fráncfort (eu-central):** Excelente latencia para Binance / Bybit Spot & Futures API.
   - **Tokio (ap-northeast):** Latencia ultra-baja para servidores asiáticos de exchanges.

---

## 🚀 Pasos de Despliegue en el VPS

### 1. Clonar Repositorio e Instalar Docker
```bash
# Actualizar e instalar Docker en Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose -y
sudo systemctl enable --now docker

# Clonar el proyecto
git clone https://github.com/Franco4447/trading-signals-ml.git
cd trading-signals-ml
```

### 2. Configurar Variables de Entorno (.env)
```bash
cat <<EOF > .env
TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
TELEGRAM_CHAT_ID="987654321"
EOF
```

### 3. Iniciar el Servidor Containerizado
```bash
# Construir e iniciar en segundo plano
docker-compose up -d --build

# Verificar logs del servidor
docker-compose logs -f
```

---

## 📡 Verificación del Endpoint de Inferencia

```bash
# Probar Health Check
curl http://localhost:8000/health

# Probar Inferencia en Tiempo Real
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{
       "candles": [
         {"timestamp": "2024-01-01T00:00:00", "open": 40000, "high": 40500, "low": 39800, "close": 40200, "volume": 100},
         {"timestamp": "2024-01-01T01:00:00", "open": 40200, "high": 41200, "low": 40100, "close": 41000, "volume": 150}
       ],
       "max_leverage": 5.0
     }'
```

---

## 🛡️ Mantenimiento y Logs
* **Reiniciar Servicio:** `docker-compose restart`
* **Detener Servicio:** `docker-compose down`
* **Inspeccionar Uso de CPU/Memoria:** `docker stats`
