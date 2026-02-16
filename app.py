import streamlit as st
from datetime import date, timedelta
from modules.quote_calculator import calculate_quote, load_pricing
from modules.pdf_generator import generate_quote_pdf

pricing = load_pricing()

LANG_PAIRS = pricing["language_pairs"]
DOMAINS = pricing["domains"]
SURCHARGES = pricing["surcharges"]
VOLUME_UNITS = {"chars": "글자 수", "words": "단어 수", "pages": "페이지 수"}

st.set_page_config(page_title="번역 견적 시스템", page_icon="📝", layout="centered")

# ── Custom CSS ──
st.markdown("""
<style>
    .main .block-container { max-width: 720px; padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background: #f0f2f6; border-radius: 8px; padding: 12px 16px;
    }
    .big-total {
        font-size: 2rem; font-weight: 700; color: #1a73e8;
        text-align: center; padding: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📝 번역 자동 견적 시스템")
st.caption("번역 요건을 입력하면 즉시 견적을 확인할 수 있습니다.")

# ── Session state 초기화 ──
if "step" not in st.session_state:
    st.session_state.step = 1

# ============================
# Step 1: 정보 입력
# ============================
if st.session_state.step == 1:

    # 고객 정보
    st.subheader("👤 고객 정보")
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("고객명 / 회사명", placeholder="예: ABC무역 김민수")
    with col2:
        client_email = st.text_input("이메일", placeholder="예: client@company.com")

    st.divider()

    # 번역 요건
    st.subheader("📋 번역 요건")
    col1, col2 = st.columns(2)
    with col1:
        lang_pair = st.selectbox(
            "언어쌍",
            options=list(LANG_PAIRS.keys()),
            format_func=lambda x: LANG_PAIRS[x],
        )
    with col2:
        domain = st.selectbox(
            "분야",
            options=list(DOMAINS.keys()),
            format_func=lambda x: DOMAINS[x],
        )

    col1, col2 = st.columns(2)
    with col1:
        volume = st.number_input("분량", min_value=1, value=1000, step=100)
    with col2:
        volume_unit = st.selectbox(
            "단위",
            options=list(VOLUME_UNITS.keys()),
            format_func=lambda x: VOLUME_UNITS[x],
        )

    deadline = st.date_input(
        "납기일",
        value=date.today() + timedelta(days=3),
        min_value=date.today(),
    )

    st.divider()

    # 할증 옵션
    st.subheader("⚡ 할증 옵션")
    st.caption("긴급 / 준긴급은 하나만 선택 가능합니다.")

    col1, col2, col3, col4 = st.columns(4)
    surcharge_checks = {}
    with col1:
        surcharge_checks["urgent"] = st.checkbox(SURCHARGES["urgent"]["label"])
    with col2:
        surcharge_checks["semi_urgent"] = st.checkbox(SURCHARGES["semi_urgent"]["label"])
    with col3:
        surcharge_checks["dtp"] = st.checkbox(SURCHARGES["dtp"]["label"])
    with col4:
        surcharge_checks["night"] = st.checkbox(SURCHARGES["night"]["label"])

    # 긴급/준긴급 상호 배타 체크
    exclusive_error = surcharge_checks["urgent"] and surcharge_checks["semi_urgent"]
    if exclusive_error:
        st.error("긴급과 준긴급은 동시에 선택할 수 없습니다.")

    st.divider()

    # 특이사항
    notes = st.text_area("📌 특이사항", placeholder="추가 요청사항을 입력하세요", height=80)

    # 견적 산출 버튼
    st.divider()
    can_submit = client_name and client_email and volume > 0 and not exclusive_error
    if st.button("🧮 견적 산출하기", type="primary", disabled=not can_submit, use_container_width=True):
        selected_surcharges = [k for k, v in surcharge_checks.items() if v]
        try:
            result = calculate_quote(
                language_pair=lang_pair,
                domain=domain,
                volume=volume,
                volume_unit=volume_unit,
                surcharge_keys=selected_surcharges,
            )
            st.session_state.step = 2
            st.session_state.result = result
            st.session_state.client_name = client_name
            st.session_state.client_email = client_email
            st.session_state.deadline = deadline
            st.session_state.notes = notes
            st.rerun()
        except ValueError as e:
            st.error(str(e))

# ============================
# Step 2: 견적 결과
# ============================
elif st.session_state.step == 2:
    result = st.session_state.result
    quote_number = f"Q-{date.today().strftime('%Y%m%d')}-001"

    # 헤더
    st.markdown(f"**견적서 번호:** `{quote_number}`")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**수신:** {st.session_state.client_name}")
        st.markdown(f"**이메일:** {st.session_state.client_email}")
    with col2:
        st.markdown(f"**발행일:** {date.today().strftime('%Y-%m-%d')}")
        st.markdown(f"**납기일:** {st.session_state.deadline.strftime('%Y-%m-%d')}")

    st.divider()

    # 견적 상세
    st.subheader("📊 견적 상세")

    lang_label = LANG_PAIRS[result.language_pair]
    domain_label = DOMAINS[result.domain]
    unit_label = VOLUME_UNITS[result.volume_unit]

    # 기본 금액
    st.markdown(
        f"**{lang_label} · {domain_label}** — "
        f"{result.original_volume:,.0f}{unit_label} "
        f"(환산 {result.converted_chars:,}자) × {result.unit_price:,}원/자"
    )

    # 상세 테이블
    rows = [
        {"항목": f"{lang_label} {domain_label} 번역", "금액": f"{result.base_amount:,}원"},
    ]
    for s in result.surcharges:
        rows.append({"항목": f"{s['label']} (+{int(s['rate']*100)}%)", "금액": f"{s['amount']:,}원"})

    st.table(rows)

    # 합계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("소계", f"{result.subtotal:,}원")
    with col2:
        st.metric("VAT (10%)", f"{result.vat:,}원")
    with col3:
        st.metric("총 견적금액", f"{result.total:,}원")

    st.markdown(f'<div class="big-total">💰 {result.total:,}원</div>', unsafe_allow_html=True)

    # 특이사항
    if st.session_state.notes:
        st.info(f"📌 **특이사항:** {st.session_state.notes}")

    st.caption(f"유효기간: {date.today().strftime('%Y-%m-%d')} ~ {(date.today() + timedelta(days=7)).strftime('%Y-%m-%d')} | 결제조건: 납품 후 30일")

    st.divider()

    # 하단 버튼
    col1, col2 = st.columns(2)
    with col1:
        pdf_bytes = generate_quote_pdf(
            result=result,
            client_name=st.session_state.client_name,
            client_email=st.session_state.client_email,
            deadline=st.session_state.deadline,
            notes=st.session_state.notes,
            quote_number=quote_number,
        )
        st.download_button(
            "📄 PDF 견적서 다운로드",
            data=pdf_bytes,
            file_name=f"{quote_number}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col2:
        if st.button("🔄 새 견적 작성", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
