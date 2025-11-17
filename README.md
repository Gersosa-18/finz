# 🧠 Finz - Financial Monitoring Platform (Backend)

Sistema backend de monitoreo financiero en tiempo real con alertas personalizadas y análisis de indicadores técnicos.

![Python](https://img.shields.io/badge/Python-3.13.7-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Características

- ✅ **APIs REST** con autenticación JWT (access + refresh tokens)
- ✅ **Sistema de alertas configurables**:
  - Alertas simples (precio > X, volumen < Y)
  - Alertas de rango (precio entre X e Y)
  - Alertas de porcentaje (cambió ±5%)
  - Alertas compuestas (múltiples condiciones con AND/OR)
- ✅ **Obtención de RSI** con señales de sobrecompra/sobreventa/neutral
- ✅ **Integración con APIs financieras**:
  - yfinance (precios en tiempo real)
  - Finnhub (earnings y eventos corporativos)
  - TwelveData (RSI y datos técnicos)
- ✅ **Push notifications** con Web Push API
- ✅ **Scheduler automático** (APScheduler) para actualización de datos cada 10 min
- ✅ **Calendario de eventos** económicos y earnings

## 🛠️ Stack Tecnológico

**Backend:**

- Python 3.13+
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL
- Pydantic (validación de datos)

**Autenticación:**

- JWT (access + refresh tokens)
- bcrypt (hash de contraseñas)

**Tareas automatizadas:**

- APScheduler
- pytz (manejo de zonas horarias)

**Integraciones:**

- yfinance
- Finnhub API
- TwelveData API
- Web Push (pywebpush)

## 📁 Arquitectura del Proyecto

```
finz/
├── app/
│   ├── config/          # Configuración de BD y variables de entorno
│   ├── models/          # Modelos SQLAlchemy (Usuarios, Alertas, RSI, Eventos)
│   ├── schemas/         # Schemas Pydantic para validación
│   ├── routers/         # Endpoints REST (alertas, usuarios, RSI, eventos)
│   ├── services/        # Lógica de negocio
│   ├── middlewares/     # JWT Bearer, manejo de errores
│   ├── utils/           # Utilidades (auth, validaciones)
│   ├── enums/           # Enumeraciones (tipos de alertas, eventos)
│   ├── scheduler.py     # Tareas programadas
│   └── main.py          # Punto de entrada de la aplicación
```

## 📡 Endpoints Principales

### Autenticación

- `POST /login` - Login y obtención de tokens
- `POST /refresh` - Renovar access token
- `POST /usuarios` - Registro de nuevo usuario

### Alertas

- `GET /alertas/mis-alertas` - Obtener alertas del usuario
- `POST /alertas/simple` - Crear alerta simple
- `POST /alertas/rango` - Crear alerta de rango
- `POST /alertas/porcentaje` - Crear alerta de porcentaje
- `POST /alertas/compuesta` - Crear alerta compuesta
- `GET /alertas/activadas` - Evaluar alertas activas
- `DELETE /alertas/{id}` - Eliminar alerta

### RSI

- `GET /rsi/mis-rsi` - Obtener RSI de tickers seguidos
- `POST /rsi/seguimientos` - Agregar ticker a seguimiento
- `DELETE /rsi/seguimientos/{ticker}` - Eliminar seguimiento
- `GET /rsi/{ticker}` - Obtener RSI de un ticker específico

### Eventos

- `GET /eventos/mis-eventos` - Eventos económicos y earnings próximos
- `POST /eventos/sincronizar` - Sincronizar eventos desde APIs

### Notificaciones

- `POST /notificaciones/suscribir` - Suscribirse a push notifications

## 🔐 Autenticación

El sistema usa JWT con dos tipos de tokens:

**Access Token:**

- Duración: 30 minutos
- Se envía en header: `Authorization: Bearer <token>`
- Usado para todas las peticiones autenticadas

**Refresh Token:**

- Duración: 7 días
- Permite renovar el access token sin re-login
- Endpoint: `POST /refresh`

## 📊 Scheduler Automático

El sistema ejecuta tareas programadas:

**Evaluación de alertas:**

- Frecuencia: Cada 5 minutos
- Verifica todas las alertas activas
- Envía notificaciones push cuando se activan

**Actualización de RSI:**

- Frecuencia: Cada 10 minutos
- Horario: 11:30 - 18:00 (horario de mercado USA en ARG)
- Solo días hábiles
- Guarda histórico en base de datos

## 👤 Autor

**Germán Sosa**

- LinkedIn: [linkedin.com/in/germán-sosa](https://www.linkedin.com/in/germán-sosa)
- GitHub: [@Gersosa-18](https://github.com/Gersosa-18)

## 🔗 Links Relacionados

- [Frontend (React + TypeScript)](https://github.com/Gersosa-18/finz-frontend)
- [🔗 Demo en vivo](https://finz-frontend.vercel.app)
