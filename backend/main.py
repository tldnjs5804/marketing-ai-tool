import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend import ai as ai_module
from backend import comments as comments_module
from backend import db as db_module
from backend import news as news_module

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Marketing AI Tool API")
# index.html alone is 200KB+ of mostly text (HTML/CSS/JS); gzip shrinks that dramatically
# and also compresses the JSON API responses (news/comments payloads can be sizeable)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/api/news")
def api_news(
    q: str = Query(..., min_length=1),
    max: int = Query(20, ge=1, le=100),
    sources: str = Query("google,naver"),
):
    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    try:
        items = news_module.collect_news(q, max_results=max, sources=source_list)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"query": q, "count": len(items), "items": items}


@app.get("/api/comments/youtube")
def api_youtube_comments(
    video: str = Query(..., description="영상 URL 또는 ID"),
    max: int = Query(50, ge=1, le=200),
    order: str = Query("relevance"),
):
    video_id = comments_module.extract_youtube_id(video)
    if not video_id:
        raise HTTPException(status_code=400, detail="영상 URL 또는 ID를 확인해주세요")
    try:
        items = comments_module.fetch_youtube_comments(video_id, max_results=max, order=order)
        meta = comments_module.fetch_youtube_video_info(video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"video_id": video_id, "count": len(items), "items": items, "meta": meta}


@app.get("/api/comments/reddit")
def api_reddit_comments(
    post: str = Query(..., description="게시글 URL 또는 ID"),
    max: int = Query(50, ge=1, le=200),
):
    try:
        items, meta = comments_module.fetch_reddit_comments(post, max_results=max)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"count": len(items), "items": items, "meta": meta}


class ClaudeRequest(BaseModel):
    prompt: str
    max_tokens: int = 2000


@app.post("/api/ai/claude")
def api_ai_claude(body: ClaudeRequest):
    try:
        text = ai_module.call_claude(body.prompt, max_tokens=body.max_tokens)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"text": text}


def _check_sync_token(x_sync_token: Optional[str] = Header(None)):
    """단일 사용자 전제의 최소 보호 장치 — 로그인 시스템 대신 공유 비밀 토큰 하나로
    /api/backup을 지킨다. Render 환경변수 SYNC_TOKEN과 클라이언트가 보내는
    X-Sync-Token 헤더를 상수 시간 비교한다."""
    expected = os.environ.get("SYNC_TOKEN")
    if not expected:
        raise HTTPException(status_code=500, detail="서버에 SYNC_TOKEN이 설정되어 있지 않습니다")
    if not x_sync_token or not secrets.compare_digest(x_sync_token, expected):
        raise HTTPException(status_code=401, detail="동기화 토큰이 올바르지 않습니다")


class BackupRequest(BaseModel):
    data: Dict[str, Any]


@app.post("/api/backup")
def api_save_backup(body: BackupRequest, x_sync_token: Optional[str] = Header(None)):
    _check_sync_token(x_sync_token)
    try:
        db_module.save_backup(body.data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


@app.get("/api/backup")
def api_load_backup(x_sync_token: Optional[str] = Header(None)):
    _check_sync_token(x_sync_token)
    try:
        row = db_module.load_backup()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="저장된 백업이 없습니다")
    return row


# Only index.html is served — NOT a StaticFiles(directory=BASE_DIR) mount. That used to
# expose every file in the project root over HTTP, including .env (API keys/secrets),
# the backend/*.py source, and requirements.txt.
@app.get("/")
def serve_index():
    return FileResponse(BASE_DIR / "index.html")
