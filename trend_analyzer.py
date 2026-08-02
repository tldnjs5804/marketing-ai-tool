from pytrends.request import TrendReq
import pandas as pd

def get_google_trend(keyword, period_days=90):
    """
    구글 트렌드에서 키워드의 관심도 변화를 가져온다
    
    keyword: 검색할 키워드
    period_days: 조회 기간 (일 단위). 기본 90일
    """
    
    # pytrends 객체 생성 (hl=언어, tz=시간대 오프셋)
    pytrends = TrendReq(hl="ko-KR", tz=540)
    
    # 기간을 pytrends가 이해하는 문자열로 변환
    if period_days <= 7:
        timeframe = "now 7-d"
    elif period_days <= 30:
        timeframe = "today 1-m"
    elif period_days <= 90:
        timeframe = "today 3-m"
    else:
        timeframe = "today 12-m"
    
    # 키워드 등록 (구글 트렌드는 한 번에 최대 5개 키워드까지 비교 가능)
    pytrends.build_payload([keyword], timeframe=timeframe, geo="KR")
    
    # 시간대별 관심도 데이터 가져오기 (0~100 사이 상대값)
    interest_df = pytrends.interest_over_time()
    
    if interest_df.empty:
        print(f"'{keyword}'에 대한 트렌드 데이터가 없습니다.")
        return None
    
    return interest_df


def summarize_trend(df, keyword):
    """트렌드 데이터를 요약해서 보여준다"""
    
    if df is None:
        return
    
    print(f"\n'{keyword}' 트렌드 요약")
    print(f"조회 기간: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"평균 관심도: {df[keyword].mean():.1f}")
    print(f"최고 관심도: {df[keyword].max()} (날짜: {df[keyword].idxmax().date()})")
    print(f"최근 관심도: {df[keyword].iloc[-1]}")
    
    # 최근 추세 (최근 5개 평균 vs 그 이전 5개 평균)
    if len(df) >= 10:
        recent_avg = df[keyword].iloc[-5:].mean()
        previous_avg = df[keyword].iloc[-10:-5].mean()
        if recent_avg > previous_avg:
            print("추세: 상승 📈")
        elif recent_avg < previous_avg:
            print("추세: 하락 📉")
        else:
            print("추세: 유지 ➡️")


def save_trend_to_csv(df, keyword):
    """트렌드 데이터를 CSV 파일로 저장"""
    if df is None:
        return
    
    filename = f"trend_{keyword}.csv"
    df.to_csv(filename, encoding="utf-8-sig")  # 한글 깨짐 방지 인코딩
    print(f"저장 완료: {filename}")


if __name__ == "__main__":
    keyword = input("트렌드를 조회할 키워드를 입력하세요: ").strip()
    
    trend_df = get_google_trend(keyword, period_days=90)
    summarize_trend(trend_df, keyword)
    save_trend_to_csv(trend_df, keyword)