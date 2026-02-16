import os
from datetime import date, datetime

import gspread
from google.oauth2.service_account import Credentials

from modules.quote_calculator import QuoteResult, load_pricing

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER_ROW = [
    "견적서번호", "발행일", "고객명", "이메일",
    "언어쌍", "분야", "분량(원본)", "단위", "환산글자수",
    "글자당단가", "기본금액", "할증내역", "할증합계",
    "소계", "VAT", "총견적금액", "납기일", "특이사항",
]


def _get_client() -> gspread.Client:
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_or_create_sheet(client: gspread.Client) -> gspread.Worksheet:
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", "번역견적_자동기록")
    try:
        spreadsheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(sheet_name)
        spreadsheet.share("", perm_type="anyone", role="writer")

    worksheet = spreadsheet.sheet1
    if worksheet.row_count == 0 or worksheet.acell("A1").value != HEADER_ROW[0]:
        worksheet.update([HEADER_ROW], "A1")

    return worksheet


def save_quote_to_sheets(
    result: QuoteResult,
    client_name: str,
    client_email: str,
    deadline: date,
    notes: str = "",
    quote_number: str | None = None,
) -> bool:
    pricing = load_pricing()
    lang_label = pricing["language_pairs"][result.language_pair]
    domain_label = pricing["domains"][result.domain]

    if quote_number is None:
        quote_number = f"Q-{date.today().strftime('%Y%m%d')}-001"

    surcharge_labels = ", ".join(
        f"{s['label']}(+{int(s['rate']*100)}%)" for s in result.surcharges
    ) or "-"

    row = [
        quote_number,
        date.today().strftime("%Y-%m-%d"),
        client_name,
        client_email,
        lang_label,
        domain_label,
        result.original_volume,
        result.volume_unit,
        result.converted_chars,
        result.unit_price,
        result.base_amount,
        surcharge_labels,
        result.surcharge_total,
        result.subtotal,
        result.vat,
        result.total,
        deadline.strftime("%Y-%m-%d"),
        notes or "-",
    ]

    gc = _get_client()
    worksheet = _get_or_create_sheet(gc)
    worksheet.append_row(row, value_input_option="USER_ENTERED")
    return True
