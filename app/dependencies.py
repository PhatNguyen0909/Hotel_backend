from functools import lru_cache

from app.config import get_settings
from app.services.google_sheets import GoogleSheetsRepository


@lru_cache
def get_google_sheets_repository() -> GoogleSheetsRepository:
    return GoogleSheetsRepository(get_settings())
