from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.dependencies import get_google_sheets_repository
from app.services.google_sheets import GoogleSheetsRepository


def build_sheet_router(resource_name: str, entity_key: str) -> APIRouter:
    router = APIRouter(prefix=f"/{resource_name}", tags=[resource_name])

    @router.get("", response_model=None)
    def list_records(
        repository: GoogleSheetsRepository = Depends(
            get_google_sheets_repository),
    ):
        return repository.list_records(entity_key)

    @router.get("/{record_id}", response_model=None)
    def get_record(
        record_id: str,
        repository: GoogleSheetsRepository = Depends(
            get_google_sheets_repository),
    ):
        record = repository.get_record(entity_key, record_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_name[:-1].capitalize()} not found",
            )
        return record

    @router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
    def create_record(
        payload: dict = Body(...),
        repository: GoogleSheetsRepository = Depends(
            get_google_sheets_repository),
    ):
        return repository.create_record(entity_key, payload)

    @router.put("/{record_id}", response_model=None)
    def update_record(
        record_id: str,
        payload: dict = Body(...),
        repository: GoogleSheetsRepository = Depends(
            get_google_sheets_repository),
    ):
        return repository.update_record(entity_key, record_id, payload)

    return router
