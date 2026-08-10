from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import ai as ai_module
from backend import comments as comments_module
from backend import news as news_module

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="Marketing AI Tool API")


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


# API 라우트 등록 뒤에 마운트해야 /api/* 가 정적 파일 서빙보다 먼저 매칭된다
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
