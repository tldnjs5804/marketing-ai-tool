import json
from datetime import datetime

from backend.news import search_google_news


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

    news_list = search_google_news(keyword, max_results=100, period_days=period_days, exclude_keywords=exclude_keywords)

    print(f"\n'{keyword}' 검색 결과: 총 {len(news_list)}건\n")
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news['title']}")
        print(f"   {news['link']}\n")

    save_to_json(news_list, keyword)
