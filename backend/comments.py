import os
import re


def extract_youtube_id(url_or_id):
    m = re.search(r"(?:youtu\.be/|[?&]v=|/shorts/|/embed/)([A-Za-z0-9_-]{11})", url_or_id or "")
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id or ""):
        return url_or_id
    return None


def fetch_youtube_comments(video_id, max_results=50, order="relevance"):
    """유튜브 댓글을 Data API v3로 수집한다. 서버 환경변수 YOUTUBE_API_KEY가 필요하다."""
    import requests

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("서버에 YouTube API 키(YOUTUBE_API_KEY)가 설정되어 있지 않습니다")

    out = []
    page_token = ""
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    while len(out) < max_results:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "order": order,
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token
        res = requests.get(base_url, params=params, timeout=10)
        if not res.ok:
            detail = res.json().get("error", {}).get("message", res.text)
            raise RuntimeError(f"YouTube API 오류: {detail}")
        data = res.json()
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            out.append({
                "author": snippet.get("authorDisplayName", ""),
                "text": snippet.get("textDisplay", ""),
                "likes": snippet.get("likeCount", 0),
                "date": (snippet.get("publishedAt") or "")[:10],
            })
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return out[:max_results]


def fetch_reddit_comments(post_url_or_id, max_results=50):
    """레딧 게시글의 댓글을 PRAW로 수집한다. 서버 환경변수 REDDIT_CLIENT_ID/SECRET이 필요하다."""
    import praw

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "marketing-ai-tool/1.0")
    if not client_id or not client_secret:
        raise ValueError("서버에 Reddit API 자격증명(REDDIT_CLIENT_ID/SECRET)이 설정되어 있지 않습니다")

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    if post_url_or_id.startswith("http"):
        submission = reddit.submission(url=post_url_or_id)
    else:
        submission = reddit.submission(id=post_url_or_id)
    submission.comments.replace_more(limit=0)

    out = []
    for c in submission.comments.list()[:max_results]:
        out.append({
            "author": str(c.author) if c.author else "[deleted]",
            "text": c.body,
            "likes": c.score,
            "date": "",
        })
    return out
