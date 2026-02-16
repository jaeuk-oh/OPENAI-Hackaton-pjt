# 번역 자동 견적 시스템

AI-powered translation quote system with OpenAI GPT-4o-mini

## Known Issues & Solutions

### Phase 2: 견적 엔진

**Issue #1: 복수 할증 적용 시 부동소수점 오차**

- **문제**: `surcharge_total`을 합산 비율(`total_surcharge_rate`)로 한번에 계산하면 부동소수점 오차 발생
  - `0.5 + 0.2 = 0.7000000000000001` → `int(180000 * 0.7000000000000001) = 125999` (기대값: 126,000)
- **원인**: Python float 연산에서 `0.5 + 0.2`가 정확히 `0.7`이 아닌 `0.7000000000000001`로 계산됨
- **해결**: 합산 비율로 한번에 곱하지 않고, 각 할증 금액을 개별 `int()` 변환 후 합산하도록 변경
  ```python
  # Before (오차 발생)
  surcharge_total = int(base_amount * total_surcharge_rate)

  # After (정확)
  for key in surcharge_keys:
      amount = int(base_amount * rate)
      surcharge_total += amount
  ```
- **테스트**: `test_multiple_surcharges` — 14/14 통과 확인

### Phase 5: OpenAI API 연동

**Issue #2: OpenAI 클라이언트 모듈 최상단 초기화 시 앱 전체 실행 불가**

- **문제**: `client = OpenAI()`를 모듈 레벨(최상단)에서 실행하면, `OPENAI_API_KEY`가 미설정 시 해당 모듈을 import하는 것만으로 `OpenAIError` 발생 → 앱 전체가 실행 불가
- **원인**: `app.py`가 `file_analyzer`, `email_parser`를 import → 모듈 로드 시점에 `OpenAI()` 생성자 호출 → API 키 검증 실패
- **해결**: `_get_client()` 함수로 지연 초기화(Lazy init). 실제 API 호출 시점에만 클라이언트 생성
  ```python
  # Before (모듈 import 시 에러)
  client = OpenAI()

  # After (API 호출 시점에 생성)
  def _get_client() -> OpenAI:
      return OpenAI()

  response = _get_client().chat.completions.create(...)
  ```
- **효과**: API 키 없이도 메인 플로우(직접 입력 → 견적 → PDF)가 정상 동작
