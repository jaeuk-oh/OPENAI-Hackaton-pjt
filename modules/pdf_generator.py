import io
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from modules.quote_calculator import QuoteResult, load_pricing
from templates.quote_template import build_quote_pdf


def generate_quote_pdf(
    result: QuoteResult,
    client_name: str,
    client_email: str,
    deadline: date,
    notes: str = "",
    quote_number: str | None = None,
) -> bytes:
    pricing = load_pricing()
    lang_label = pricing["language_pairs"][result.language_pair]
    domain_label = pricing["domains"][result.domain]

    if quote_number is None:
        quote_number = f"Q-{date.today().strftime('%Y%m%d')}-001"

    issue_date = date.today().strftime("%Y-%m-%d")
    valid_until = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    data = {
        "quote_number": quote_number,
        "issue_date": issue_date,
        "valid_until": valid_until,
        "client_name": client_name,
        "client_email": client_email,
        "deadline": deadline.strftime("%Y-%m-%d"),
        "translation_label": f"{lang_label} {domain_label} 번역",
        "converted_chars": result.converted_chars,
        "unit_price": result.unit_price,
        "base_amount": result.base_amount,
        "surcharges": result.surcharges,
        "subtotal": result.subtotal,
        "vat": result.vat,
        "total": result.total,
        "notes": notes,
    }

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=30,
        bottomMargin=30,
        leftMargin=40,
        rightMargin=40,
    )
    elements = build_quote_pdf(data)
    doc.build(elements)
    return buffer.getvalue()
