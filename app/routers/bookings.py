from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.dependencies import get_google_sheets_repository
from app.services.google_sheets import GoogleSheetsRepository

router = APIRouter(prefix="/bookings", tags=["bookings"])

# Must be registered BEFORE /{record_id} to avoid path conflict
@router.get("/search-availability", response_model=None)
def search_room_availability(
    ma_phong: str = Query(..., description="Mã phòng cần kiểm tra"),
    ngay_nhan_phong: date = Query(..., description="Ngày nhận phòng (YYYY-MM-DD)"),
    ngay_tra_phong: date = Query(..., description="Ngày trả phòng (YYYY-MM-DD)"),
    repository: GoogleSheetsRepository = Depends(get_google_sheets_repository),
):
    """Kiểm tra phòng có bị đặt trùng lịch trong khoảng ngày cho trước hay không."""
    return repository.search_room_availability(
        room_id=ma_phong,
        check_in=ngay_nhan_phong,
        check_out=ngay_tra_phong,
    )


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
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
