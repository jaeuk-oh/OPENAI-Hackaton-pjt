"""
파일 분석 모듈 (File Analyzer)

현재: OpenAI GPT-4o-mini 사용 (해커톤/개발용)

TODO [프로덕션 전환 시]
번역 원문(저작물)을 외부 API로 전송하면 유출 위험이 있으므로
실제 서비스에서는 반드시 로컬 LLM으로 전환해야 합니다.
  - Ollama + Mistral 7B: http://localhost:11434/api/generate
  - OpenAI-compatible API이므로 base_url만 변경하면 됨
"""

import json
import os
from pathlib import Path

from openai import OpenAI
from langdetect import detect

from config.prompts import FILE_ANALYSIS_SYSTEM, FILE_ANALYSIS_USER

# TODO [프로덕션]: base_url="http://localhost:11434/v1"
MODEL = "gpt-4o-mini"


def _get_client() -> OpenAI:
    # Lazy init: OpenAI()를 모듈 import 시점이 아닌 실제 API 호출 시점에 생성.
    # 이렇게 하면 OPENAI_API_KEY가 없어도 모듈 import가 실패하지 않고,
    # 파일 분석 기능을 사용하지 않는 경우(직접 입력 등) 정상 동작한다.
    return OpenAI()


def extract_text(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".txt":
        return file_bytes.decode("utf-8", errors="replace")

    if suffix == ".docx":
        import io
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)

    if suffix == ".pdf":
        import io
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    return file_bytes.decode("utf-8", errors="replace")


def count_volume(text: str) -> dict:
    char_count = len(text.replace(" ", "").replace("\n", ""))
    word_count = len(text.split())

    # 한국어 비중이 높으면 글자수 기준, 아니면 단어수 기준
    try:
        lang = detect(text[:1000]) if len(text) > 0 else "ko"
    except Exception:
        lang = "ko"

    if lang in ("ko", "ja", "zh-cn", "zh-tw"):
        return {"value": char_count, "unit": "chars", "detected_lang": lang}
    else:
        return {"value": word_count, "unit": "words", "detected_lang": lang}


def analyze_domain(text: str) -> dict:
    sample = text[:500]
    try:
        response = _get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": FILE_ANALYSIS_SYSTEM},
                {"role": "user", "content": FILE_ANALYSIS_USER.format(text_sample=sample)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "domain": "general",
            "source_lang": "ko",
            "confidence": 0.0,
            "reasoning": f"API error, defaulting to general: {e}",
        }


def analyze_file(file_bytes: bytes, filename: str) -> dict:
    text = extract_text(file_bytes, filename)
    if not text.strip():
        return {
            "error": "텍스트를 추출할 수 없습니다.",
            "volume": None,
            "domain_analysis": None,
        }

    volume = count_volume(text)
    domain_analysis = analyze_domain(text)

    # 언어 코드 정규화
    lang_map = {"ko": "ko", "en": "en", "ja": "ja", "zh-cn": "zh", "zh-tw": "zh"}
    detected_lang = lang_map.get(volume["detected_lang"], "ko")

    return {
        "volume": volume,
        "domain_analysis": domain_analysis,
        "detected_lang": detected_lang,
        "char_count": len(text.replace(" ", "").replace("\n", "")),
        "word_count": len(text.split()),
    }
