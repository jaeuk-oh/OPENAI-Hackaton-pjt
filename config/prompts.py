FILE_ANALYSIS_SYSTEM = """You are a professional translation project manager.
Analyze the following document sample and determine:
1. The document's subject domain
2. The source language

Respond in JSON format only:
{
  "domain": "general" | "legal" | "medical" | "technical",
  "source_lang": "ko" | "en" | "ja" | "zh",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}

Domain classification rules:
- "legal": contracts, agreements, legal opinions, court documents, patents, terms of service
- "medical": clinical trials, medical records, pharmaceutical documents, research papers on health
- "technical": software docs, engineering specs, IT manuals, API docs, technical standards
- "general": everything else (marketing, general business, personal documents)
"""

FILE_ANALYSIS_USER = """Analyze this document sample (first 500 characters):

---
{text_sample}
---

Determine the domain and source language."""

EMAIL_PARSING_SYSTEM = """You are a translation company's project manager.
Extract structured information from customer translation request emails.

Always respond in JSON format with this exact schema:
{
  "client_name": "string or null",
  "source_lang": "ko" | "en" | "ja" | "zh" | null,
  "target_lang": "ko" | "en" | "ja" | "zh" | null,
  "volume": {"value": number, "unit": "chars" | "words" | "pages"} | null,
  "domain": "general" | "legal" | "medical" | "technical" | null,
  "urgency": "urgent" | "semi_urgent" | "normal" | null,
  "deadline": "ISO 8601 datetime string" | null,
  "dtp_required": true | false | null,
  "notes": "string or null"
}

Extraction rules:
- urgency "urgent": mentions within 24h, "급하게", "내일", "ASAP", "긴급"
- urgency "semi_urgent": mentions within 48h, "이틀", "모레"
- urgency "normal": no urgency mentioned or deadline > 48h
- For deadline, infer from context. Today is {today}.
- If a field cannot be determined, use null.
- client_name: extract from email signature, greeting, or sender info.
"""

EMAIL_PARSING_USER = """Parse this customer email and extract translation request details:

From: {sender}
Subject: {subject}

{body}
"""

EMAIL_FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Parse this customer email and extract translation request details:

From: kim@abctrade.co.kr
Subject: 영문 카탈로그 번역 요청

안녕하세요, ABC무역 김민수입니다.
당사 제품 카탈로그 한글본을 영문으로 번역 부탁드립니다.
분량은 약 5,000자이고, 다음 주 금요일까지 부탁드립니다.
제품 기술 용어가 많으니 참고 부탁드립니다.""",
    },
    {
        "role": "assistant",
        "content": """{
  "client_name": "ABC무역 김민수",
  "source_lang": "ko",
  "target_lang": "en",
  "volume": {"value": 5000, "unit": "chars"},
  "domain": "technical",
  "urgency": "normal",
  "deadline": null,
  "dtp_required": null,
  "notes": "제품 기술 용어 다수 포함"
}""",
    },
    {
        "role": "user",
        "content": """Parse this customer email and extract translation request details:

From: lee@lawfirm.co.kr
Subject: 급한 번역 부탁드립니다

이 변호사입니다. 내일 오전까지 급하게 필요한 게 있어서요.
첨부 계약서 영문번역 부탁드립니다.
법률 용어 정확하게 해주셔야 합니다. 분량은 8페이지 정도요.""",
    },
    {
        "role": "assistant",
        "content": """{
  "client_name": "이 변호사",
  "source_lang": "ko",
  "target_lang": "en",
  "volume": {"value": 8, "unit": "pages"},
  "domain": "legal",
  "urgency": "urgent",
  "deadline": null,
  "dtp_required": null,
  "notes": "법률 용어 정확도 요구"
}""",
    },
]
