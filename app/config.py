from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class SheetDefinition:
    worksheet_name: str
    id_field: str
    headers: tuple[str, ...]


@dataclass(frozen=True)
class Settings:
    app_name: str
    google_service_account_file: str
    google_service_account_json: str
    google_spreadsheet_id: str
    hotel_sheet_name: str
    customer_sheet_name: str
    booking_sheet_name: str
    room_sheet_name: str

    @property
    def worksheet_map(self) -> dict[str, str]:
        return {
            "hotels": self.hotel_sheet_name,
            "customers": self.customer_sheet_name,
            "bookings": self.booking_sheet_name,
            "rooms": self.room_sheet_name,
        }

    @property
    def sheet_definitions(self) -> dict[str, SheetDefinition]:
        return {
            "hotels": SheetDefinition(
                worksheet_name=self.hotel_sheet_name,
                id_field="Mã khách sạn",
                headers=(
                    "Mã khách sạn",
                    "Tên khách sạn",
                    "Thành phố",
                    "Địa chỉ",
                    "Số lượng phòng",
                    "Giờ check-in",
                    "Giờ check-out",
                    "Số điện thoại",
                    "Email",
                    "Website",
                ),
            ),
            "customers": SheetDefinition(
                worksheet_name=self.customer_sheet_name,
                id_field="Mã khách hàng",
                headers=(
                    "Mã khách hàng",
                    "Họ và tên",
                    "Giới tính",
                    "Số điện thoại",
                    "Email",
                    "Số CCCD/Hộ chiếu",
                    "Quốc tịch",
                    "Loại khách",
                    "Công ty",
                    "Ghi chú",
                ),
            ),
            "bookings": SheetDefinition(
                worksheet_name=self.booking_sheet_name,
                id_field="Mã đặt phòng",
                headers=(
                    "Mã đặt phòng",
                    "Ngày đặt",
                    "Ngày nhận phòng",
                    "Ngày trả phòng",
                    "Mã khách hàng",
                    "Mã phòng",
                    "Số người",
                    "Trạng thái đặt phòng",
                    "Giá phòng mỗi đêm",
                    "Số đêm",
                    "Tổng tiền phòng",
                ),
            ),
            "rooms": SheetDefinition(
                worksheet_name=self.room_sheet_name,
                id_field="Mã phòng",
                headers=(
                    "Mã phòng",
                    "Số phòng",
                    "Loại phòng",
                    "Tầng",
                    "Hướng phòng",
                    "Số khách tối đa",
                    "Giá ngày thường",
                    "Giá cuối tuần",
                    "Tình trạng phòng",
                    "Ghi chú",
                ),
            ),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Hotel Backend"),
        google_service_account_file=os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE", ""),
        google_service_account_json=os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON", ""),
        google_spreadsheet_id=os.getenv("GOOGLE_SPREADSHEET_ID", ""),
        hotel_sheet_name=os.getenv("HOTEL_SHEET_NAME", "Hotels"),
        customer_sheet_name=os.getenv("CUSTOMER_SHEET_NAME", "Customers"),
        booking_sheet_name=os.getenv("BOOKING_SHEET_NAME", "Bookings"),
        room_sheet_name=os.getenv("ROOM_SHEET_NAME", "Rooms"),
    )
