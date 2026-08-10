import os
import re
import urllib.parse
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests


def search_google_news(keyword, max_results=20, period_days=None, exclude_keywords=None):
    """구글 뉴스 RSS에서 키워드로 검색해서 헤드라인 목록을 가져온다 (서버에서 직접 호출하므로 CORS 제약 없음)"""
    query = keyword
    if period_days:
        query += f" when:{period_days}d"
    if exclude_keywords:
        for ex in exclude_keywords:
            query += f" -{ex}"

    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)

    results = []
    for entry in feed.entries[:max_results]:
        title = entry.title
        source = ""
        if " - " in title:
            title, source = title.rsplit(" - ", 1)
        date = ""
        if hasattr(entry, "published"):
            try:
                date = parsedate_to_datetime(entry.published).strftime("%Y-%m-%d")
            except (TypeError, ValueError):
                date = entry.published[:16]
        results.append({
            "title": title.strip(),
            "source": source.strip(),
            "date": date,
            "link": entry.link,
            "desc": "",
        })
    return results


def search_naver_news(keyword, max_results=20):
    """네이버 뉴스 검색 오픈API. 서버 환경변수(NAVER_CLIENT_ID/SECRET)가 없으면 빈 목록을 반환한다."""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": keyword, "display": min(max_results, 100), "sort": "date"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()

    tag_re = re.compile("<[^>]+>")
    results = []
    for item in data.get("items", []):
        title = tag_re.sub("", item.get("title", ""))
        desc = tag_re.sub("", item.get("description", ""))
        pub = item.get("pubDate", "")
        try:
            date = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
        except ValueError:
            date = pub[:16]
        results.append({
            "title": title.strip(),
            "source": "네이버뉴스",
            "date": date,
            "link": item.get("originallink") or item.get("link", ""),
            "desc": desc.strip(),
        })
    return results


def collect_news(keyword, max_results=20, sources=("google", "naver")):
    """여러 소스에서 뉴스를 모아 제목 기준으로 중복 제거 후 반환한다."""
    results = []
    if "google" in sources:
        results += search_google_news(keyword, max_results=max_results)
    if "naver" in sources:
        results += search_naver_news(keyword, max_results=max_results)

    seen = set()
    deduped = []
    for item in results:
        key = item["title"]
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:max_results]
