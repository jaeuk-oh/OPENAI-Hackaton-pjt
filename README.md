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
