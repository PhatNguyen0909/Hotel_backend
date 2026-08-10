from fastapi import FastAPI

from app.config import get_settings
from app.routers import bookings, customers, hotels, rooms


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.include_router(hotels.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")


@app.get("/health", tags=["health"])
def healthcheck():
    return {"status": "ok"}
