import os
from datetime import datetime, timezone

import requests


def _config():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("서버에 Supabase 연결 정보(SUPABASE_URL/SUPABASE_SERVICE_KEY)가 설정되어 있지 않습니다")
    return url.rstrip("/"), key


def _headers(key):
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def save_backup(data):
    """단일 행(id=1)에 전체 백업을 upsert한다 — 지금은 1인 사용을 전제로 한 가장 단순한 구조다."""
    url, key = _config()
    payload = {"id": 1, "data": data, "updated_at": datetime.now(timezone.utc).isoformat()}
    res = requests.post(
        f"{url}/rest/v1/gogup_backups",
        headers={**_headers(key), "Prefer": "resolution=merge-duplicates"},
        json=payload,
        timeout=15,
    )
    if not res.ok:
        raise RuntimeError(f"Supabase 저장 오류: {res.text}")


def load_backup():
    url, key = _config()
    res = requests.get(
        f"{url}/rest/v1/gogup_backups",
        headers=_headers(key),
        params={"id": "eq.1", "select": "data,updated_at"},
        timeout=15,
    )
    if not res.ok:
        raise RuntimeError(f"Supabase 조회 오류: {res.text}")
    rows = res.json()
    return rows[0] if rows else None
