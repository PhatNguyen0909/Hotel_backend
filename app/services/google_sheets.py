import json
import re
from typing import Any, Optional

import gspread
from fastapi import HTTPException, status
from gspread.exceptions import WorksheetNotFound

from app.config import Settings, SheetDefinition


def _column_letter(column_number: int) -> str:
    result = ""
    while column_number > 0:
        column_number, remainder = divmod(column_number - 1, 26)
        result = chr(65 + remainder) + result
    return result


class GoogleSheetsRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        self._spreadsheet = None

    def list_records(self, entity_key: str) -> list[dict[str, Any]]:
        worksheet = self._get_worksheet(entity_key)
        return self._normalize_records(worksheet.get_all_records())

    def get_record(self, entity_key: str, record_id: str) -> Optional[dict[str, Any]]:
        definition = self._get_sheet_definition(entity_key)
        for record in self.list_records(entity_key):
            if str(record.get(definition.id_field, "")).strip() == record_id:
                return record
        return None

    def create_record(self, entity_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        definition = self._get_sheet_definition(entity_key)
        record = self._prepare_payload(
            definition,
            payload,
            fallback_id=None,
            allow_missing_id=entity_key in {"customers", "bookings"},
        )
        if entity_key == "customers" and not str(record.get(definition.id_field, "")).strip():
            record[definition.id_field] = self._generate_next_record_id(
                entity_key)
        if entity_key == "bookings" and not str(record.get(definition.id_field, "")).strip():
            record[definition.id_field] = self._generate_next_record_id(
                entity_key)
        existing = self.get_record(entity_key, record[definition.id_field])
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Record with id '{record[definition.id_field]}' already exists",
            )

        worksheet = self._get_worksheet(entity_key)
        headers = self._ensure_headers(definition, worksheet, record)
        row = [self._to_cell_value(record.get(header, ""))
               for header in headers]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return {header: record.get(header, "") for header in headers}

    def update_record(
        self,
        entity_key: str,
        record_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        definition = self._get_sheet_definition(entity_key)
        worksheet = self._get_worksheet(entity_key)
        records = self._normalize_records(worksheet.get_all_records())

        for row_index, existing_record in enumerate(records, start=2):
            if str(existing_record.get(definition.id_field, "")).strip() != record_id:
                continue

            incoming = self._prepare_payload(
                definition, payload, fallback_id=record_id)
            merged = {**existing_record, **incoming,
                      definition.id_field: record_id}
            headers = self._ensure_headers(definition, worksheet, merged)
            row = [self._to_cell_value(merged.get(header, ""))
                   for header in headers]
            cell_range = f"A{row_index}:{_column_letter(len(headers))}{row_index}"
            worksheet.update(cell_range, [row],
                             value_input_option="USER_ENTERED")
            return {header: merged.get(header, "") for header in headers}

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record with id '{record_id}' not found",
        )

    def _get_client(self) -> gspread.Client:
        if self._client is None:
            if self._settings.google_service_account_json:
                try:
                    service_account_info = json.loads(
                        self._settings.google_service_account_json
                    )
                except json.JSONDecodeError as error:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON",
                    ) from error

                self._client = gspread.service_account_from_dict(
                    service_account_info
                )
                return self._client

            if not self._settings.google_service_account_file:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Configure GOOGLE_SERVICE_ACCOUNT_FILE or "
                        "GOOGLE_SERVICE_ACCOUNT_JSON"
                    ),
                )
            self._client = gspread.service_account(
                filename=self._settings.google_service_account_file
            )
        return self._client

    def _get_spreadsheet(self):
        if self._spreadsheet is None:
            if not self._settings.google_spreadsheet_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GOOGLE_SPREADSHEET_ID is not configured",
                )
            self._spreadsheet = self._get_client().open_by_key(
                self._settings.google_spreadsheet_id
            )
        return self._spreadsheet

    def _get_worksheet(self, entity_key: str):
        definition = self._get_sheet_definition(entity_key)
        sheet_name = definition.worksheet_name

        if sheet_name is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown entity '{entity_key}'",
            )

        try:
            return self._get_spreadsheet().worksheet(sheet_name)
        except WorksheetNotFound as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Worksheet '{sheet_name}' not found",
            ) from error

    def _get_sheet_definition(self, entity_key: str) -> SheetDefinition:
        definition = self._settings.sheet_definitions.get(entity_key)
        if definition is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown entity '{entity_key}'",
            )
        return definition

    def _ensure_headers(
        self,
        definition: SheetDefinition,
        worksheet,
        payload: dict[str, Any],
    ) -> list[str]:
        existing_headers = worksheet.row_values(1)
        if not existing_headers:
            ordered_headers = self._ordered_headers(definition, payload.keys())
            worksheet.update("A1", [ordered_headers],
                             value_input_option="USER_ENTERED")
            return ordered_headers

        ordered_headers = self._ordered_headers(definition, payload.keys())
        missing_headers = [
            header for header in ordered_headers if header not in existing_headers]
        if not missing_headers:
            return existing_headers

        headers = existing_headers + missing_headers
        end_column = _column_letter(len(headers))
        worksheet.update(f"A1:{end_column}1", [
                         headers], value_input_option="USER_ENTERED")
        return headers

    @staticmethod
    def _prepare_payload(
        definition: SheetDefinition,
        payload: dict[str, Any],
        fallback_id: Optional[str],
        allow_missing_id: bool = False,
    ) -> dict[str, Any]:
        record = {str(key).strip(): value for key,
                  value in payload.items() if str(key).strip()}
        record_id = record.get(definition.id_field) or record.get(
            "id") or fallback_id

        if record_id is None or str(record_id).strip() == "":
            if allow_missing_id:
                record.pop("id", None)
                return record
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Payload must include a non-empty '{definition.id_field}'",
            )

        record.pop("id", None)
        record[definition.id_field] = str(record_id).strip()
        return record

    @staticmethod
    def _ordered_headers(definition: SheetDefinition, headers: Any) -> list[str]:
        unique_headers = list(definition.headers)
        for header in headers:
            header_text = str(header).strip()
            if not header_text or header_text == "id" or header_text in unique_headers:
                continue
            unique_headers.append(header_text)
        return unique_headers

    def _generate_next_record_id(self, entity_key: str) -> str:
        definition = self._get_sheet_definition(entity_key)
        prefix_map = {
            "customers": "KH",
            "bookings": "DP",
        }
        prefix = prefix_map.get(entity_key)
        if prefix is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Auto-generated IDs are not configured for '{entity_key}'",
            )

        existing_ids = []
        for record in self.list_records(entity_key):
            current_id = str(record.get(definition.id_field, "")).strip()
            match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", current_id)
            if match:
                existing_ids.append(int(match.group(1)))

        next_number = max(existing_ids, default=0) + 1
        return f"{prefix}{next_number:03d}"

    @staticmethod
    def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        for record in records:
            cleaned = {str(key).strip(): value for key,
                       value in record.items() if str(key).strip()}
            if any(str(value).strip() for value in cleaned.values()):
                normalized.append(cleaned)
        return normalized

    @staticmethod
    def _to_cell_value(value: Any) -> str:
        if value is None:
            return ""
        return str(value)
