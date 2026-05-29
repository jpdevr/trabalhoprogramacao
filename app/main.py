from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.database import Base, SessionLocal, engine
from app.services.price_events import price_event_bus


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    price_event_bus.start(SessionLocal)
    yield
    price_event_bus.stop()


app = FastAPI(
    title="Sistema de Pagamentos API",
    version="1.0.0",
    description="API REST para gestao de clientes, produtos, tabela de precos e vendas.",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": "payment-system-api"}
