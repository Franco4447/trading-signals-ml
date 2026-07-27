---
name: github-deploy-monitor
description: Directrices e instrucciones automáticas para orquestar, auditar y monitorear despliegues continuos (CI/CD) hacia los entornos DEV, QA y MAIN/PROD en servidores VPS. Se activa automáticamente tras cada commit, merge o intento de despliegue para validar la salud del sistema, variables MLOps y métricas cuantitativas.
---

# GitHub Deploy Monitor & CD Orchestration

Esta habilidad define la metodología y el protocolo operativo que el agente debe ejecutar de forma **automática e imperativa** cada vez que se realice un `git commit`, `git merge`, un *Pull Request* o cuando se inicie un despliegue hacia cualquiera de los entornos de infraestructura (**DEV**, **QA**, **PROD**).

---

## ⚡ 1. Disparadores Automáticos (Trigger Conditions)

El agente **debe activar esta skill** obligatoriamente cuando:
1. Se haya realizado un `git commit` o `git merge` en las ramas `dev`, `qa` o `main`.
2. El usuario solicite verificar, arrancar o monitorear un contenedor Docker (`docker compose up -d`).
3. Se complete un ciclo de CI/CD en GitHub Actions o se esté realizando una transición entre fases del proyecto.
4. Se inicie el protocolo de **Forward Testing Multi-Día en Staging (QA)** antes de un pase a Producción Live.

---

## 🗺️ 2. Matriz de Monitoreo y Variables por Entorno

Cada entorno tiene exigencias de seguridad y operativas estrictamente diferenciadas. El agente debe auditar las siguientes variables y métricas según el perfil activo:

### 🌿 Entorno: DEV (Desarrollo Continuo - VPS 1)
*   **Rama Git**: `dev`
*   **Archivo Docker**: `docker-compose.dev.yml` | **Puerto API**: `8002` | **Puerto Dash**: `8503`
*   **Archivo de Entorno**: `.env.dev`
*   **Variables Obligatorias a Auditar**:
    *   `EXCHANGE_TESTNET=true` (¡Estrictamente verdadero! Prohibido dinero real).
    *   `HARD_MAX_LEVERAGE=5` (Apalancamiento de prueba).
*   **Métricas MLOps y Cuantitativas**:
    *   Verificar que las optimizaciones con **Optuna** y el entrenamiento de **LightGBM / XGBoost** en el pipeline de reentrenamiento converjan sin presentar *overfitting* (curvas de aprendizaje alineadas).
    *   Tiempo de respuesta del endpoint de inferencia en caliente (`/predict` y `/reload-model`) $< 100\text{ ms}$.

---

### 🧪 Entorno: QA / Staging (Forward Testing Multi-Día - VPS 1)
*   **Rama Git**: `qa`
*   **Archivo Docker**: `docker-compose.qa.yml` | **Puerto API**: `8001` | **Puerto Dash**: `8502`
*   **Archivo de Entorno**: `.env.qa`
*   **Variables Obligatorias a Auditar**:
    *   `EXCHANGE_TESTNET=true` (Modo Paper Trading / Testnet activo).
    *   `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` configurados apuntando al **Canal de Telegram QA**.
*   **Métricas del Gatekeeper Cuantitativo (Monitoreo Continuo)**:
    *   **Señal Unificada**: Toda señal emitida debe estar normalizada exactamente en el intervalo continuo **`[-1.0, +1.0]`**.
    *   **Sharpe Ratio Empírico**: Debe mantenerse en **$> 1.00$** durante los días de prueba en vivo.
    *   **Sortino Ratio Empírico**: Debe ser **$> 2.00$**.
    *   **Max Drawdown (MDD)**: **¡Límite estricto del $\le 15.00\%$!** Si se supera este umbral en QA, el sistema debe alertar de inmediato al Telegram QA y bloquear cualquier futura solicitud de pase a Producción.
    *   **Fricciones de Mercado**: Auditar en los balances simulados que cada operación deduzca correctamente el **Maker Fee del 0.020%** y el slippage estimado.

---

### 🚀 Entorno: MAIN / PROD (Producción Live Aislado - VPS 2)
*   **Rama Git**: `main`
*   **Archivo Docker**: `docker-compose.prod.yml` | **Puerto API**: `8000` | **Puerto Dash**: `8501`
*   **Archivo de Entorno**: `.env.prod`
*   **Variables Obligatorias a Auditar**:
    *   `EXCHANGE_TESTNET=false` (Modo Live operando con capital real).
    *   `HARD_MAX_LEVERAGE=10` (Capado de seguridad Kelly).
    *   `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` apuntando al **Canal de Telegram Live Prod**.
*   **Seguridad e Infraestructura (Binance API Whitelist)**:
    *   Verificar que el contenedor se está ejecutando desde la IP estática autorizada en Binance (**"Restrict access to trusted IPs only"**).
    *   Auditar la emisión del latido de encendido (*Heartbeat*) en Telegram al iniciar el contenedor.
    *   Verificar la ejecución de órdenes **Bracket OCO** reales (Take-Profit y Stop-Loss colocados simultáneamente en el exchange).

---

## 🛠️ 3. Protocolo de Auditoría (Los 4 Pilares)

Para validar cualquiera de los entornos anteriores, el agente ejecutará el script de auditoría adjunto a la skill:

```bash
python .agents/skills/github-deploy-monitor/scripts/monitor_deploy_health.py --env <dev|qa|prod>
```

Este script evalúa los siguientes 4 pilares:
1.  **Salud de Contenedores Docker**: Comprueba el estado `running` (sin bucles de reinicio o *CrashLoopBackOff*), consumo de memoria/CPU y escanea los últimos 50 logs en busca de trazas de excepción o *Tracebacks*.
2.  **Integridad y Seguridad del Entorno**: Llama internamente a `scripts/validate_env.py` verificando las variables críticas sin exponer secretos en consola.
3.  **Conectividad y Latidos Exclusivos**: Verifica latencia con Binance REST/WebSockets y comprueba que la API de Telegram responda afirmativamente.
4.  **Invariante Antifuga y Calibración**: En caso de haber un servidor activo en el puerto local, ejecuta una consulta de prueba (*Smoke Test*) al endpoint para validar que el contrato de salida retorne un flotante en `[-1.0, +1.0]`.

---

## 📄 4. Generación de Reporte Post-Despliegue

Al finalizar cada monitoreo o tras un merge importante, el agente documentará el estado de salud en un reporte o resumen ejecutivo estructurado con formato GitHub Flavored Markdown:
*   Si se ejecuta localmente o en VPS, generar el reporte en la carpeta `docs/reports/` (ej. `docs/reports/deploy_qa_2026-07-27.md`).
*   Si se detecta alguna anomalía, utilizar alertas de GitHub (`> [!WARNING]`, `> [!CAUTION]`) y proponer de inmediato el aislamiento del fallo usando la metodología `systematic-debugging`.
