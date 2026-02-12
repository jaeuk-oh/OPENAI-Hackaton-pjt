# CLAUDE.md - SnapListing AI

## Project Overview

**SnapListing AI** - AI-Powered E-commerce Product Listing & Content Generator

상품 사진 한 장으로 글로벌 이커머스 리스팅, SNS 콘텐츠, 광고 카피, 프로 상품 이미지를 자동 생성하는 SaaS 플랫폼.

## Product Specification

### Core Value Proposition
- **Input**: 상품 사진 1장 (또는 여러 장)
- **Output**: 완성된 이커머스 리스팅 + 마케팅 콘텐츠 + AI 상품 이미지
- **Target User**: 글로벌 이커머스 셀러, D2C 브랜드, 소규모 온라인 사업자

### OpenAI API Usage
1. **GPT-4o Vision API**: 상품 사진 분석 (카테고리, 특징, 소재, 색상, 타겟 고객 추론)
2. **GPT-4o Chat API**: 리스팅 콘텐츠 생성 (제목, 설명, 키워드, SEO 최적화, 다국어 번역)
3. **DALL-E 3 API**: 프로페셔널 상품 이미지 생성 (화이트배경, 라이프스타일 컷)

### Key Features (MVP)
1. **Photo → Analysis**: 상품 사진 업로드 → AI 자동 분석
2. **Listing Generation**: 최적화된 이커머스 리스팅 자동 생성
   - 상품 제목 (SEO 최적화)
   - 상품 설명 (매력적인 카피라이팅)
   - 핵심 특징 불릿포인트
   - 검색 키워드/태그
3. **Multi-Language**: 한국어, 영어, 일본어, 중국어 등 다국어 리스팅 생성
4. **AI Product Images**: DALL-E 3로 프로 상품 이미지 생성
5. **Export**: Amazon, Shopify, 쿠팡 등 마켓플레이스 포맷으로 내보내기

### Revenue Model
- Free: 3 listings/month
- Pro ($29/mo): 100 listings + all languages + AI images
- Business ($99/mo): Unlimited + API access + team

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.14)
- **Package Manager**: uv
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Auth**: JWT-based authentication
- **API Client**: openai (Python SDK)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: React hooks + Context
- **Package Manager**: pnpm

### Project Structure
```
/
├── CLAUDE.md
├── pyproject.toml
├── main.py                  # FastAPI entry point
├── backend/
│   ├── api/
│   │   ├── routes/          # API route handlers
│   │   └── deps.py          # Dependencies (auth, db)
│   ├── core/
│   │   ├── config.py        # Settings & config
│   │   └── security.py      # Auth utilities
│   ├── services/
│   │   ├── vision.py        # GPT-4o Vision - product analysis
│   │   ├── listing.py       # GPT-4o - listing generation
│   │   ├── image_gen.py     # DALL-E 3 - product image generation
│   │   └── export.py        # Marketplace format export
│   ├── models/              # DB models (SQLAlchemy)
│   └── schemas/             # Pydantic schemas
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities & API client
│   └── public/              # Static assets
├── uploads/                 # Uploaded product images (gitignored)
└── tests/
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
- Reference env vars in code via config.py, never hardcode secrets

### Code Style
- Python: Follow PEP 8, use type hints, async/await for API calls
- TypeScript/React: Functional components, TypeScript strict mode
- Keep functions small and focused (single responsibility)
- No unnecessary comments or docstrings on obvious code
- Error handling only at system boundaries (user input, external APIs)

### API Design
- RESTful endpoints with clear naming
- All responses use consistent JSON structure: `{ "success": bool, "data": ..., "error": ... }`
- Proper HTTP status codes
- Input validation via Pydantic schemas

### UX/UI Principles
- Mobile-first responsive design
- Clean, minimal interface - reduce cognitive load
- Clear loading states and progress indicators for AI operations
- Instant feedback on user actions
- Professional, trustworthy visual design (think: Shopify-level polish)

## Commands

### Backend
```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn main:app --reload --port 8000

# Run tests
uv run pytest
```

### Frontend
```bash
cd frontend

# Install dependencies
pnpm install

# Run dev server
pnpm dev

# Build
pnpm build
```
