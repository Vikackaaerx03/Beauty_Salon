from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import close_client, init_db
from app.routers.auth_router import router as auth_router
from app.routers.booking_router import router as booking_router
from app.routers.feedback_router import router as feedback_router
from app.routers.payments_router import router as payments_router
from app.routers.schedules_router import router as schedules_router
from app.routers.services_router import router as services_router
from app.routers.user_router import router as user_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Beauty Salon API",
    description="REST API для управління салоном краси",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(services_router)
app.include_router(schedules_router)
app.include_router(booking_router)
app.include_router(payments_router)
app.include_router(feedback_router)


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
    except Exception:
        logger.warning("MongoDB недоступна під час старту застосунку. API продовжить роботу без ініціалізації індексів.")


@app.on_event("shutdown")
def _shutdown() -> None:
    close_client()


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "Beauty Salon API is running"}
