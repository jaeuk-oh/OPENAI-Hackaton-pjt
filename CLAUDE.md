# CLAUDE.md - 번역 자동 견적 시스템

## Project Overview

번역 회사의 핵심 반복 업무인 '주문 접수 → 견적 발송' 프로세스를 자동화하는 웹 시스템.
웹에서 번역 요건을 입력하면 실시간 견적 산출 → PDF 견적서 다운로드까지 30초 내 완결.

## Core Architecture

### OpenAI API Usage
1. **GPT-4o-mini (파일 분석)**: 업로드된 문서 샘플(첫 500자) 분석 → 분야(법률/의료/기술) 자동 판별
2. **GPT-4o-mini (이메일 파싱)**: 고객 이메일에서 언어쌍, 분량, 납기, 긴급도 등 JSON 구조화 추출

### 2가지 플로우
- **메인**: 웹 직접 입력 → rule-based 실시간 견적 → PDF 다운로드
- **보조**: 이메일 → GPT-4o-mini 파싱 → 웹 폼 Pre-fill → 담당자 확인

### 견적 산출
- Rule-based 계산 (LLM 불필요, 즉시 계산)
- 단가표: 언어쌍(4종) × 분야(일반/법률/의료/기술)
- 할증: 긴급(+50%), 준긴급(+30%), DTP(+20%), 야간(+10%)
- 최종 = 기본금액 × 할증 + VAT(10%)

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: OpenAI GPT-4o-mini (openai Python SDK)
- **견적 엔진**: Python rule-based
- **PDF 생성**: ReportLab
- **데이터 저장**: Google Sheets (gspread)
- **Package Manager**: uv
- **Python**: 3.14

## Project Structure
```
/
├── CLAUDE.md
├── pyproject.toml
├── app.py                    # Streamlit 메인 (웹 견적 페이지)
├── modules/
│   ├── quote_calculator.py   # 견적 산출 (rule-based)
│   ├── file_analyzer.py      # 파일 분석 (GPT-4o-mini)
│   ├── email_parser.py       # 이메일 파싱 (GPT-4o-mini)
│   ├── pdf_generator.py      # PDF 견적서 생성
│   └── sheets_connector.py   # Google Sheets 연동
├── config/
│   ├── pricing.json          # 단가표 (언어쌍 × 분야)
│   └── prompts.py            # LLM 프롬프트 관리
├── templates/
│   └── quote_template.py     # PDF 템플릿
├── tests/
│   ├── test_emails/          # 테스트 이메일
│   ├── test_files/           # 테스트 번역 파일 (더미)
│   └── test_e2e.py           # E2E 테스트
└── docs/
    ├── flowchart.md          # 시스템 플로우
    └── prompt_iteration.md   # 프롬프트 개선 기록
```

## Development Rules (CRITICAL)

### Git & Deployment
- **NEVER commit or push without explicit user approval**
- **NEVER create branches without explicit user approval**
- Always ask before any git push, commit, or branch creation
- Write clear, descriptive commit messages in English

### Environment & Secrets
- **NEVER touch, modify, read, or create .env files**
- **NEVER create .env.example, .env.sample, or any env template files**
- Environment variables are managed entirely by the user
- Reference env vars in code via config, never hardcode secrets

### Code Style
- Python: Follow PEP 8, use type hints
- Keep functions small and focused (single responsibility)
- No unnecessary comments or docstrings on obvious code
- Error handling only at system boundaries (user input, external APIs)

### Security (Production Note)
- 현재: OpenAI API 사용 (개발/해커톤용)
- 프로덕션: 로컬 LLM 전환 필수 (번역 원문 유출 방지)
- OpenAI-compatible API이므로 base_url만 변경하면 전환 가능
- 코드 내 TODO 주석으로 전환 포인트 명시

## Commands
```bash
# Install dependencies
uv sync

# Run Streamlit app
uv run streamlit run app.py

# Run tests
uv run pytest
```
