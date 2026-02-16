"""
이메일 파싱 모듈 (Email Parser)

고객 이메일에서 번역 요청 정보를 GPT-4o-mini로 구조화 추출합니다.
파싱 결과는 웹 폼에 자동 사전입력(Pre-fill)됩니다.

이메일 파싱은 '요청 메타데이터'만 처리하므로 외부 API 사용 가능.
단, 이메일 본문에 번역 원문이 직접 포함된 경우:
  → 프로덕션에서는 원문 부분 마스킹 처리 후 API 전송
"""

import json
from datetime import date

from openai import OpenAI

from config.prompts import (
    EMAIL_PARSING_SYSTEM,
    EMAIL_PARSING_USER,
    EMAIL_FEW_SHOT_EXAMPLES,
)

# TODO [프로덕션]: base_url="http://localhost:11434/v1"
MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    # Lazy init: OPENAI_API_KEY 없이도 모듈 import 가능하도록
    # 실제 이메일 파싱 호출 시점에 OpenAI 클라이언트 생성
    return OpenAI()


def parse_email(
    sender: str,
    subject: str,
    body: str,
) -> dict:
    system_prompt = EMAIL_PARSING_SYSTEM.format(today=date.today().isoformat())
    user_prompt = EMAIL_PARSING_USER.format(
        sender=sender,
        subject=subject,
        body=body,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        *EMAIL_FEW_SHOT_EXAMPLES,
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        result = json.loads(response.choices[0].message.content)

        # 언어쌍 매핑
        src = result.get("source_lang")
        tgt = result.get("target_lang")
        if src and tgt:
            result["language_pair"] = f"{src}-{tgt}"
        else:
            result["language_pair"] = None

        return result
    except Exception as e:
        return {"error": str(e)}
