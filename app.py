import streamlit as st
from datetime import date, timedelta
from modules.quote_calculator import calculate_quote, load_pricing
from modules.pdf_generator import generate_quote_pdf

pricing = load_pricing()

LANG_PAIRS = pricing["language_pairs"]
DOMAINS = pricing["domains"]
SURCHARGES = pricing["surcharges"]
VOLUME_UNITS = {"chars": "글자 수", "words": "단어 수", "pages": "페이지 수"}
LANG_PAIR_KEYS = list(LANG_PAIRS.keys())
DOMAIN_KEYS = list(DOMAINS.keys())

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
for key in ["prefill_volume", "prefill_unit", "prefill_domain", "prefill_lang", "prefill_name",
            "prefill_email", "prefill_urgency", "prefill_dtp", "prefill_notes"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ============================
# Step 1: 정보 입력
# ============================
if st.session_state.step == 1:

    # ── 사이드바: 보조 기능 (파일 분석 / 이메일 파싱) ──
    with st.sidebar:
        st.header("🤖 AI 자동 입력")

        tab_file, tab_email = st.tabs(["📎 파일 분석", "📧 이메일 파싱"])

        with tab_file:
            st.caption("파일을 업로드하면 분량/분야를 AI가 자동 분석합니다.")
            uploaded_file = st.file_uploader(
                "원문 파일 업로드",
                type=["txt", "docx", "pdf"],
                key="file_upload",
            )
            if uploaded_file and st.button("🔍 파일 분석", key="btn_analyze"):
                with st.spinner("GPT-4o-mini로 분석 중..."):
                    from modules.file_analyzer import analyze_file
                    result = analyze_file(uploaded_file.getvalue(), uploaded_file.name)

                if result.get("error"):
                    st.error(result["error"])
                else:
                    vol = result["volume"]
                    dom = result["domain_analysis"]
                    st.session_state.prefill_volume = vol["value"]
                    st.session_state.prefill_unit = vol["unit"]
                    st.session_state.prefill_domain = dom.get("domain", "general")
                    st.session_state.prefill_lang = result.get("detected_lang", "ko")

                    st.success("분석 완료!")
                    st.json({
                        "분량": f'{vol["value"]:,} {vol["unit"]}',
                        "분야": dom.get("domain"),
                        "신뢰도": dom.get("confidence"),
                        "판단근거": dom.get("reasoning"),
                    })
                    st.rerun()

        with tab_email:
            st.caption("고객 이메일을 붙여넣으면 자동으로 폼을 채워줍니다.")
            email_sender = st.text_input("발신자", placeholder="lee@lawfirm.co.kr", key="email_sender")
            email_subject = st.text_input("제목", placeholder="급한 번역 부탁드립니다", key="email_subject")
            email_body = st.text_area("본문", height=150, key="email_body",
                                      placeholder="이메일 본문을 붙여넣으세요...")
            if email_body and st.button("🔍 이메일 파싱", key="btn_parse"):
                with st.spinner("GPT-4o-mini로 파싱 중..."):
                    from modules.email_parser import parse_email
                    parsed = parse_email(email_sender, email_subject, email_body)

                if parsed.get("error"):
                    st.error(f"파싱 실패: {parsed['error']}")
                else:
                    if parsed.get("client_name"):
                        st.session_state.prefill_name = parsed["client_name"]
                    if email_sender:
                        st.session_state.prefill_email = email_sender
                    if parsed.get("language_pair") and parsed["language_pair"] in LANG_PAIR_KEYS:
                        st.session_state.prefill_lang_pair = parsed["language_pair"]
                    if parsed.get("domain") and parsed["domain"] in DOMAIN_KEYS:
                        st.session_state.prefill_domain = parsed["domain"]
                    if parsed.get("volume"):
                        st.session_state.prefill_volume = parsed["volume"]["value"]
                        st.session_state.prefill_unit = parsed["volume"]["unit"]
                    if parsed.get("urgency") == "urgent":
                        st.session_state.prefill_urgency = "urgent"
                    elif parsed.get("urgency") == "semi_urgent":
                        st.session_state.prefill_urgency = "semi_urgent"
                    if parsed.get("dtp_required"):
                        st.session_state.prefill_dtp = True
                    if parsed.get("notes"):
                        st.session_state.prefill_notes = parsed["notes"]

                    st.success("파싱 완료! 폼에 자동 입력되었습니다.")
                    st.json(parsed)
                    st.rerun()

    # ── 메인: 고객 정보 ──
    st.subheader("👤 고객 정보")
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input(
            "고객명 / 회사명",
            value=st.session_state.prefill_name or "",
            placeholder="예: ABC무역 김민수",
        )
    with col2:
        client_email = st.text_input(
            "이메일",
            value=st.session_state.prefill_email or "",
            placeholder="예: client@company.com",
        )

    st.divider()

    # 번역 요건
    st.subheader("📋 번역 요건")

    # Pre-fill: 언어쌍
    default_lang_idx = 0
    prefill_lp = st.session_state.get("prefill_lang_pair")
    if prefill_lp and prefill_lp in LANG_PAIR_KEYS:
        default_lang_idx = LANG_PAIR_KEYS.index(prefill_lp)
    elif st.session_state.prefill_lang:
        # 파일 분석에서 감지된 source lang → 첫 번째 매칭 언어쌍
        for i, k in enumerate(LANG_PAIR_KEYS):
            if k.startswith(st.session_state.prefill_lang + "-"):
                default_lang_idx = i
                break

    # Pre-fill: 분야
    default_domain_idx = 0
    if st.session_state.prefill_domain and st.session_state.prefill_domain in DOMAIN_KEYS:
        default_domain_idx = DOMAIN_KEYS.index(st.session_state.prefill_domain)

    col1, col2 = st.columns(2)
    with col1:
        lang_pair = st.selectbox(
            "언어쌍",
            options=LANG_PAIR_KEYS,
            index=default_lang_idx,
            format_func=lambda x: LANG_PAIRS[x],
        )
    with col2:
        domain = st.selectbox(
            "분야",
            options=DOMAIN_KEYS,
            index=default_domain_idx,
            format_func=lambda x: DOMAINS[x],
        )

    # Pre-fill: 분량/단위
    default_volume = st.session_state.prefill_volume or 1000
    volume_unit_keys = list(VOLUME_UNITS.keys())
    default_unit_idx = 0
    if st.session_state.prefill_unit and st.session_state.prefill_unit in volume_unit_keys:
        default_unit_idx = volume_unit_keys.index(st.session_state.prefill_unit)

    col1, col2 = st.columns(2)
    with col1:
        volume = st.number_input("분량", min_value=1, value=int(default_volume), step=100)
    with col2:
        volume_unit = st.selectbox(
            "단위",
            options=volume_unit_keys,
            index=default_unit_idx,
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
        surcharge_checks["urgent"] = st.checkbox(
            SURCHARGES["urgent"]["label"],
            value=st.session_state.prefill_urgency == "urgent",
        )
    with col2:
        surcharge_checks["semi_urgent"] = st.checkbox(
            SURCHARGES["semi_urgent"]["label"],
            value=st.session_state.prefill_urgency == "semi_urgent",
        )
    with col3:
        surcharge_checks["dtp"] = st.checkbox(
            SURCHARGES["dtp"]["label"],
            value=bool(st.session_state.prefill_dtp),
        )
    with col4:
        surcharge_checks["night"] = st.checkbox(SURCHARGES["night"]["label"])

    # 긴급/준긴급 상호 배타 체크
    exclusive_error = surcharge_checks["urgent"] and surcharge_checks["semi_urgent"]
    if exclusive_error:
        st.error("긴급과 준긴급은 동시에 선택할 수 없습니다.")

    st.divider()

    # 특이사항
    notes = st.text_area(
        "📌 특이사항",
        value=st.session_state.prefill_notes or "",
        placeholder="추가 요청사항을 입력하세요",
        height=80,
    )

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

            # Google Sheets 자동 기록 (백그라운드)
            try:
                from modules.sheets_connector import save_quote_to_sheets
                save_quote_to_sheets(
                    result=result,
                    client_name=client_name,
                    client_email=client_email,
                    deadline=deadline,
                    notes=notes,
                )
            except Exception:
                pass  # Sheets 실패해도 견적 플로우는 계속 진행

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
