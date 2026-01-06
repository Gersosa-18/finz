# 🧠 Finz - Financial Monitoring Platform (Backend)

> **Backend desarrollado con FastAPI que implementa arquitectura en capas, autenticación JWT completa, tareas programadas desacopladas y lógica de negocio compleja para evaluación de alertas financieras en tiempo real.**

![Python](https://img.shields.io/badge/Python-3.13.7-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118+-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🧠 Arquitectura y Capacidades del Backend

- ✅ **Arquitectura en capas** - Separación clara: routers (HTTP) → services (lógica) → models (datos)
- ✅ **JWT con refresh tokens** - Sistema completo de autenticación stateless (access 30min + refresh 7días)
- ✅ **Background tasks** - APScheduler desacoplado del servidor web para evaluación de alertas
- ✅ **Integración de APIs externas** - Consumo resiliente de yfinance, Finnhub, TwelveData (con timeouts y fallbacks)
- ✅ **ORM + validación** - SQLAlchemy para persistencia, Pydantic para validación de datos
- ✅ **Sistema de alertas complejo** - Evaluación de condiciones compuestas (AND/OR) sin dependencias del framework

---

## 🧠 Decisiones Técnicas

**¿Por qué se construyó así?**

1. **Service Layer Pattern** → Toda la lógica fuera de los routers. Permite testing sin levantar FastAPI y reutilizar lógica (la evaluación de alertas se usa en endpoint manual + scheduler).

2. **JWT con Refresh Tokens** → Sistema de doble token en lugar de solo access. Sesiones largas sin comprometer seguridad (access corto limita ventana de exposición).

3. **Scheduler en Thread Separado** → APScheduler corre independiente del server. Previene que tareas pesadas (polling de 50+ tickers) bloqueen requests HTTP.

4. **Enums de Python** → Uso de enums (`TipoAlerta`, `EstadoAlerta`) en lugar de strings. Previene typos, mejora autocomplete, hace el código mantenible.

5. **Manejo de Errores en APIs** → Timeouts, reintentos y fallbacks en todas las integraciones. Si Finnhub cae, el sistema sigue con datos en caché.

6. **Alertas Polimórficas** → BD soporta diferentes tipos de alertas (simple/rango/porcentaje/compuesta) con estructura extensible

---

## 💼 ¿Por qué este proyecto?

Construí Finz para demostrar:

- Diseño de APIs desde cero (no tutorial)
- Autenticación real (no auth básico de ejemplo)
- Integración multi-API resiliente
- Manejo de estado complejo (alertas condicionales + evaluación en tiempo real)

---

## 🛠️ Stack

**Backend:** Python 3.13 · FastAPI · SQLAlchemy · PostgreSQL · Pydantic  
**Auth:** JWT (PyJWT) · bcrypt  
**Tasks:** APScheduler · pytz  
**APIs:** yfinance · Finnhub · TwelveData · WebPush

---

## 📁 Arquitectura

```
finz/
├── app/
│   ├── routers/         # Endpoints (capa HTTP)
│   ├── services/        # Lógica de negocio pura
│   ├── models/          # Entidades SQLAlchemy
│   ├── schemas/         # DTOs Pydantic
│   ├── middlewares/     # JWT, manejo de errores
│   ├── utils/           # Auth helpers, validaciones
│   ├── enums/           # Estados, tipos
│   ├── scheduler.py     # Tareas programadas
│   └── main.py          # Entry point
```

**Flujo:** `Cliente → Router → Service → Model → DB`

---

## ▶️ Instalación Rápida

```bash
# 1. Clonar
git clone https://github.com/Gersosa-18/finz.git
cd finz

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno (.env)
DATABASE_URL=postgresql://user:password@localhost:5432/finz
JWT_SECRET=cambiar_en_produccion
FINNHUB_API_KEY=tu_key
TWELVEDATA_API_KEY=tu_key

# 5. Ejecutar
uvicorn app.main:app --reload
```

🚀 **Server:** `http://localhost:8000`  
📚 **Swagger:** `http://localhost:8000/docs`

---

## 📡 Endpoints Principales

**Auth:** `/login` · `/refresh` · `/usuarios`  
**Alertas:** `/alertas/simple` · `/alertas/rango` · `/alertas/porcentaje` · `/alertas/compuesta`  
**RSI:** `/rsi/mis-rsi` · `/rsi/{ticker}` · `/rsi/seguimientos`  
**Eventos:** `/eventos/mis-eventos` · `/eventos/sincronizar`  
**Notifications:** `/notificaciones/suscribir`

Ver documentación completa en `/docs` (Swagger UI)

---

## 🔐 Autenticación

**Sistema de doble token:**

- **Access Token** (30min) → Para todas las requests autenticadas
- **Refresh Token** (7 días) → Renovar access sin re-login

**Flujo:**

```
POST /login → access + refresh
→ Usar access en requests
→ Si expira (401) → POST /refresh
→ Nuevo access token
```

**Formato:** `Authorization: Bearer <access_token>`

---

## 🚀 Sistema de Alertas

**Tipos implementados:**

- **Simple:** Precio > X, volumen < Y
- **Rango:** Precio entre X e Y
- **Porcentaje:** Cambió ±N%
- **Compuesta:** Múltiples condiciones con AND/OR

**Evaluación automática:** Scheduler revisa cada 5 minutos → si se cumple condición → push notification

---

## 📊 Scheduler Automático

**Evaluación de alertas** - Cada 5 minutos, 24/7:

1. Obtiene alertas activas
2. Consulta precios actuales
3. Evalúa condiciones
4. Dispara notificaciones push

**Actualización de RSI** - Cada 10 minutos (horario de mercado USA):

1. Solo días hábiles, 11:30-18:00 ARG
2. Consulta TwelveData API
3. Guarda histórico + detecta señales (sobrecompra/sobreventa)

---

**Para evaluar arquitectura:**

- `services/alertas.py` - Evaluación de alertas sin dependencias del framework
- `routers/` vs `services/` - Separación de responsabilidades

**Para evaluar auth:**

- `middlewares/auth.py` - JWT + refresh tokens + rotación
- `utils/auth.py` - Helpers de hashing y validación

**Para evaluar tasks:**

- `scheduler.py` - Configuración de APScheduler
- Threading separado del server FastAPI

**Para evaluar persistencia:**

- `models/` - Diseño de BD con enums y relaciones
- SQLAlchemy queries optimizadas

---

## 📈 Features del Dominio

**Indicadores Técnicos:**

- RSI (Relative Strength Index)
- Señales: Sobrecompra (>70), Sobreventa (<30), Neutral (30-70)
- Histórico para análisis de tendencias

**Calendario de Eventos:**

- Datos económicos (inflación, empleo, bancos centrales)
- Earnings trimestrales (fechas confirmadas + estimadas)
- Sincronización con Finnhub API

**Push Notifications:**

- Web Push API para notificaciones en tiempo real
- Suscripción por usuario
- Triggered por scheduler cuando alertas se activan

---

## 👤 Autor

**Germán Sosa** - Backend Developer

💼 [LinkedIn](https://www.linkedin.com/in/germán-sosa) · 🐙 [GitHub](https://github.com/Gersosa-18)

## 🔗 Links

🎨 [Frontend (React + TypeScript)](https://github.com/Gersosa-18/finz-frontend)  
🔗 [Demo en vivo](https://finz-frontend.vercel.app)

---

## 📝 Licencia

MIT License
