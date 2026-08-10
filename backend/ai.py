import os

import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def call_claude(prompt, max_tokens=2000):
    """서버에 보관된 ANTHROPIC_API_KEY로 Claude를 호출한다.

    프론트엔드가 브라우저에서 api.anthropic.com을 직접 호출하면 인증 헤더를 실을 방법이
    없어 항상 실패한다 (CORS 이전에 키를 안전하게 둘 곳이 없음). 그래서 "내장·무료" 옵션은
    이 서버 경유 호출로만 동작한다.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("서버에 Anthropic API 키(ANTHROPIC_API_KEY)가 설정되어 있지 않습니다")

    res = requests.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    if not res.ok:
        detail = res.json().get("error", {}).get("message", res.text)
        raise RuntimeError(f"Claude API 오류: {detail}")
    data = res.json()
    return "".join(block.get("text", "") for block in data.get("content", []))
