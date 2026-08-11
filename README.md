# Hotel Backend with Google Sheets

This project provides 4 backend API groups that read and write directly to Google Sheets:

- `/api/hotels`
- `/api/customers`
- `/api/bookings`
- `/api/rooms`

## How it works

Each API request connects to the spreadsheet and works with one worksheet:

- `thông tin khách sạn`
- `Danh sách khách hàng`
- `Đặt phòng`
- `Danh sách phòng`

The first row in each worksheet is treated as the header row.
Each row below it is one record.
Each worksheet uses its own key column:

- Hotels: `Mã khách sạn`
- Customers: `Mã khách hàng`
- Bookings: `Mã đặt phòng`
- Rooms: `Mã phòng`

If you add a new field through the API, the backend automatically appends that column to the worksheet header.

## Setup

1. Create a Google Cloud service account.
2. Enable Google Sheets API for the project.
3. Download the service account JSON key.
4. Share the target Google Sheet with the service account email.
5. Copy `.env.example` to `.env` and fill in the values.
6. Install dependencies:

```bash
pip install -r requirements.txt
```

7. Run the server:

```bash
uvicorn app.main:app --reload
```

You can authenticate in one of two ways:

- Local: set `GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json`
- Render: set `GOOGLE_SERVICE_ACCOUNT_JSON` to the full JSON content of the service account key

If both are present, `GOOGLE_SERVICE_ACCOUNT_JSON` is used first.

## Deploy To Render

This repo now includes `render.yaml` for Render Web Service deployment.

### Render env vars

Set these variables on Render:

- `APP_NAME=Hotel Backend`
- `GOOGLE_SERVICE_ACCOUNT_JSON=<paste full service account json>`
- `GOOGLE_SPREADSHEET_ID=<your spreadsheet id>`
- `HOTEL_SHEET_NAME=thông tin khách sạn`
- `CUSTOMER_SHEET_NAME=Danh sách khách hàng`
- `BOOKING_SHEET_NAME=Đặt phòng`
- `ROOM_SHEET_NAME=Danh sách phòng`

Do not upload the JSON key file to the repo for Render. Use `GOOGLE_SERVICE_ACCOUNT_JSON` instead.

After deploy, your API URL will look like:

```text
https://your-service-name.onrender.com/api/rooms
```

## Suggested worksheet columns

### Hotels

`Mã khách sạn`, `Tên khách sạn`, `Thành phố`, `Địa chỉ`, `Số lượng phòng`, `Giờ check-in`, `Giờ check-out`, `Số điện thoại`, `Email`, `Website`

### Customers

`Mã khách hàng`, `Họ và tên`, `Giới tính`, `Số điện thoại`, `Email`, `Số CCCD/Hộ chiếu`, `Quốc tịch`, `Loại khách`, `Công ty`, `Ghi chú`

### Bookings

`Mã đặt phòng`, `Ngày đặt`, `Ngày nhận phòng`, `Ngày trả phòng`, `Mã khách hàng`, `Mã phòng`, `Số người`, `Trạng thái đặt phòng`, `Giá phòng mỗi đêm`, `Số đêm`, `Tổng tiền phòng`

### Rooms

`Mã phòng`, `Số phòng`, `Loại phòng`, `Tầng`, `Hướng phòng`, `Số khách tối đa`, `Giá ngày thường`, `Giá cuối tuần`, `Tình trạng phòng`, `Ghi chú`

## Example requests

Create a customer:

```http
POST /api/customers
Content-Type: application/json

{
  "Họ và tên": "Nguyen Minh Quan",
  "Giới tính": "Nam",
  "Số điện thoại": 905123456,
  "Email": "quan.nguyen@gmail.com",
  "Số CCCD/Hộ chiếu": 79204015678,
  "Quốc tịch": "Việt Nam",
  "Loại khách": "Khách lẻ",
  "Công ty": "",
  "Ghi chú": "Thích phòng tầng cao"
}
```

`Mã khách hàng` sẽ tự được sinh theo dạng `KH001`, `KH002`, ... nếu bạn không gửi lên.

Create a booking:

```http
POST /api/bookings
Content-Type: application/json

{
  "Mã đặt phòng": "DP013",
  "Ngày đặt": "2026-08-10",
  "Ngày nhận phòng": "2026-08-12",
  "Ngày trả phòng": "2026-08-14",
  "Mã khách hàng": "KH001",
  "Mã phòng": "P203",
  "Số người": 2,
  "Trạng thái đặt phòng": "Đã xác nhận",
  "Giá phòng mỗi đêm": 850000,
  "Số đêm": 2,
  "Tổng tiền phòng": 1700000
}
```

Update a room:

```http
PUT /api/rooms/P203
Content-Type: application/json

{
  "Tình trạng phòng": "Đang có khách",
  "Giá ngày thường": "1200000"
}
```

## Available endpoints

- `GET /health`
- `GET /api/hotels`
- `GET /api/hotels/{id}`
- `POST /api/hotels`
- `PUT /api/hotels/{id}`
- `GET /api/customers`
- `GET /api/customers/{id}`
- `POST /api/customers`
- `PUT /api/customers/{id}`
- `GET /api/bookings`
- `GET /api/bookings/{id}`
- `POST /api/bookings`
- `PUT /api/bookings/{id}`
- `GET /api/rooms`
- `GET /api/rooms/{id}`
- `POST /api/rooms`
- `PUT /api/rooms/{id}`