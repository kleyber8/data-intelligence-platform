from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.app.routers import health, auth, ports, vessels, routes, anomalies

# Rate Limiter por IP
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Maritime Data Intelligence API",
    description="API REST de consumo para los Data Marts de la capa Gold.",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS restrictivo (en producción, cambiar a dominios específicos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cambiar en producción
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Incluir Routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ports.router, prefix="/api/v1")
app.include_router(vessels.router, prefix="/api/v1")
app.include_router(routes.router, prefix="/api/v1")
app.include_router(anomalies.router, prefix="/api/v1")
