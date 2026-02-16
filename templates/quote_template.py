from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import platform

# ── 한글 폰트 등록 ──
_font_registered = False


def _register_korean_font():
    global _font_registered
    if _font_registered:
        return

    font_paths = []
    if platform.system() == "Darwin":
        font_paths = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        ]
    elif platform.system() == "Linux":
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/nanum/NanumGothic.ttf",
        ]
    elif platform.system() == "Windows":
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",
        ]

    for fp in font_paths:
        if Path(fp).exists():
            try:
                pdfmetrics.registerFont(TTFont("Korean", fp))
                _font_registered = True
                return
            except Exception:
                continue

    _font_registered = False


def get_korean_font() -> str:
    _register_korean_font()
    return "Korean" if _font_registered else "Helvetica"


# ── 스타일 ──
BLUE = colors.HexColor("#1a73e8")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
DARK_GRAY = colors.HexColor("#333333")


def _styles():
    font = get_korean_font()
    return {
        "title": ParagraphStyle("title", fontName=font, fontSize=18, textColor=BLUE, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName=font, fontSize=9, textColor=colors.gray),
        "heading": ParagraphStyle("heading", fontName=font, fontSize=12, textColor=DARK_GRAY, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", fontName=font, fontSize=10, textColor=DARK_GRAY, leading=14),
        "small": ParagraphStyle("small", fontName=font, fontSize=8, textColor=colors.gray),
        "total": ParagraphStyle("total", fontName=font, fontSize=14, textColor=BLUE, alignment=2),
    }


# ── 테이블 공통 스타일 ──
def _base_table_style():
    font = get_korean_font()
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GRAY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        # 헤더 행
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        # 줄무늬
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ])


def build_quote_pdf(data: dict) -> list:
    """PDF 요소(flowables) 리스트를 반환한다."""
    s = _styles()
    elements = []

    # ── 헤더 ──
    elements.append(Paragraph("견 적 서", s["title"]))
    elements.append(Paragraph("QUOTATION", s["subtitle"]))
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=BLUE))
    elements.append(Spacer(1, 6 * mm))

    # ── 견적 정보 / 고객 정보 ──
    font = get_korean_font()
    info_data = [
        ["견적서 번호", data["quote_number"], "수신", data["client_name"]],
        ["발행일", data["issue_date"], "이메일", data["client_email"]],
        ["유효기간", data["valid_until"], "납기일", data["deadline"]],
    ]
    info_table = Table(info_data, colWidths=[70, 130, 50, None])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GRAY),
        ("TEXTCOLOR", (0, 0), (0, -1), BLUE),
        ("TEXTCOLOR", (2, 0), (2, -1), BLUE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    # ── 견적 상세 ──
    elements.append(Paragraph("견적 상세", s["heading"]))

    detail_header = ["항목", "분량", "단가", "할증", "금액"]
    detail_rows = [detail_header]

    # 기본 번역
    detail_rows.append([
        data["translation_label"],
        f'{data["converted_chars"]:,}자',
        f'{data["unit_price"]:,}원/자',
        "-",
        f'{data["base_amount"]:,}원',
    ])

    # 할증 항목
    for s_item in data["surcharges"]:
        detail_rows.append([
            s_item["label"],
            "-",
            "-",
            f'+{int(s_item["rate"] * 100)}%',
            f'{s_item["amount"]:,}원',
        ])

    detail_table = Table(detail_rows, colWidths=[150, 70, 70, 50, None])
    style = _base_table_style()
    style.add("ALIGN", (1, 0), (-1, -1), "RIGHT")
    detail_table.setStyle(style)
    elements.append(detail_table)
    elements.append(Spacer(1, 6 * mm))

    # ── 합계 ──
    elements.append(Paragraph("합계", s["heading"]))

    total_rows = [
        ["소계", f'{data["subtotal"]:,}원'],
        ["VAT (10%)", f'{data["vat"]:,}원'],
        ["총 견적금액", f'{data["total"]:,}원'],
    ]
    total_table = Table(total_rows, colWidths=[None, 150])
    total_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GRAY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, BLUE),
        ("FONTSIZE", (0, -1), (-1, -1), 13),
        ("TEXTCOLOR", (0, -1), (-1, -1), BLUE),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 8 * mm))

    # ── 부가 정보 ──
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 4 * mm))

    footer_lines = [
        f"결제조건: 납품 후 30일",
        f"유효기간: {data['issue_date']} ~ {data['valid_until']}",
    ]
    if data.get("notes"):
        footer_lines.append(f"특이사항: {data['notes']}")

    for line in footer_lines:
        elements.append(Paragraph(line, s["small"]))
        elements.append(Spacer(1, 1 * mm))

    return elements
