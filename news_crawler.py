import feedparser
import urllib.parse
import json
from datetime import datetime

def search_google_news(keyword, period_days=None, exclude_keywords=None):
    """
    구글 뉴스 RSS에서 키워드로 검색해서 헤드라인 목록을 가져온다
    
    keyword: 검색할 키워드
    period_days: 최근 N일 이내 뉴스만 (예: 7이면 최근 7일). None이면 기간 제한 없음
    exclude_keywords: 제외할 키워드 리스트 (예: ["광고", "홍보"])
    """
    
    # 구글 뉴스는 검색어에 "when:7d" 같은 문법을 붙이면 기간 필터링이 됨
    query = keyword
    if period_days:
        query += f" when:{period_days}d"
    
    # 제외 키워드는 검색어 앞에 "-"를 붙이면 제외됨 (구글 검색 문법)
    if exclude_keywords:
        for ex in exclude_keywords:
            query += f" -{ex}"
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(url)
    
    results = []
    for entry in feed.entries:
        results.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        })
    
    return results


def save_to_json(data, keyword):
    """검색 결과를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"news_{keyword}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n저장 완료: {filename}")


def get_user_input():
    """사용자로부터 검색 조건을 입력받는다"""
    
    keyword = input("검색할 키워드를 입력하세요: ").strip()
    
    print("\n기간을 선택하세요:")
    print("1. 최근 1일")
    print("2. 최근 7일")
    print("3. 최근 30일")
    print("4. 전체 기간")
    period_choice = input("선택 (1~4): ").strip()
    
    period_map = {"1": 1, "2": 7, "3": 30, "4": None}
    period_days = period_map.get(period_choice, None)
    
    exclude_input = input("\n제외할 키워드가 있으면 쉼표(,)로 구분해서 입력하세요 (없으면 Enter): ").strip()
    exclude_keywords = [kw.strip() for kw in exclude_input.split(",")] if exclude_input else []
    
    return keyword, period_days, exclude_keywords


if __name__ == "__main__":
    keyword, period_days, exclude_keywords = get_user_input()
    
    news_list = search_google_news(keyword, period_days, exclude_keywords)
    
    print(f"\n'{keyword}' 검색 결과: 총 {len(news_list)}건\n")
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news['title']}")
        print(f"   {news['link']}\n")
    
    save_to_json(news_list, keyword)