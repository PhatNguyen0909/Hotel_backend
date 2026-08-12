from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.dependencies import get_google_sheets_repository
from app.services.google_sheets import GoogleSheetsRepository, _parse_date

router = APIRouter(prefix="/bookings", tags=["bookings"])


class AvailabilityRequest(BaseModel):
    ngay_nhan_phong: str
    ngay_tra_phong: str


def _resolve_availability(ngay_nhan_phong: str, ngay_tra_phong: str, repository: GoogleSheetsRepository):
    try:
        check_in = _parse_date(ngay_nhan_phong)
        check_out = _parse_date(ngay_tra_phong)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return repository.list_available_rooms(check_in=check_in, check_out=check_out)


# Must be registered BEFORE /{record_id} to avoid path conflict
@router.get("/search-availability", response_model=None)
def list_available_rooms_get(
    ngay_nhan_phong: str = Query(
        ..., description="Ngày nhận phòng (DD/MM, DD/MM/YYYY, YYYY-MM-DD, ...)"),
    ngay_tra_phong: str = Query(
        ..., description="Ngày trả phòng (DD/MM, DD/MM/YYYY, YYYY-MM-DD, ...)"),
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    """Trả về danh sách phòng còn trống trong khoảng ngày nhận – trả phòng."""
    return _resolve_availability(ngay_nhan_phong, ngay_tra_phong, repository)


@router.post("/search-availability", response_model=None)
def list_available_rooms_post(
    payload: AvailabilityRequest = Body(...),
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    """Như GET /search-availability nhưng nhận params qua JSON body."""
    return _resolve_availability(payload.ngay_nhan_phong, payload.ngay_tra_phong, repository)


@router.get("", response_model=None)
def list_bookings(
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    return repository.list_records("bookings")


@router.get("/{record_id}", response_model=None)
def get_booking(
    record_id: str,
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    record = repository.get_record("bookings", record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return record


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
def create_booking(
    payload: dict = Body(...),
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    return repository.create_record("bookings", payload)


@router.put("/{record_id}", response_model=None)
def update_booking(
    record_id: str,
    payload: dict = Body(...),
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    return repository.update_record("bookings", record_id, payload)
