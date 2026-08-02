import platform
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq


def setup_korean_font():
    """그래프에서 한글이 깨지지 않도록 폰트 설정"""
    system = platform.system()
    if system == "Windows":
        plt.rcParams["font.family"] = "Malgun Gothic"
    elif system == "Darwin":  # Mac
        plt.rcParams["font.family"] = "AppleGothic"
    else:  # Linux
        plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False


def get_google_trend(keyword, period_days=90):
    """구글 트렌드에서 키워드의 관심도 변화를 가져온다"""
    pytrends = TrendReq(
        hl="ko-KR",
        tz=540,
        requests_args={"headers": {"User-Agent": "Mozilla/5.0"}}
    )

    if period_days <= 7:
        timeframe = "now 7-d"
    elif period_days <= 30:
        timeframe = "today 1-m"
    elif period_days <= 90:
        timeframe = "today 3-m"
    else:
        timeframe = "today 12-m"

    pytrends.build_payload([keyword], timeframe=timeframe, geo="KR")
    interest_df = pytrends.interest_over_time()

    if interest_df.empty:
        print(f"'{keyword}'에 대한 트렌드 데이터가 없습니다.")
        return None

    return interest_df


def summarize_trend(df, keyword):
    """트렌드 데이터를 요약해서 터미널에 보여준다"""
    if df is None:
        return

    print(f"\n'{keyword}' 트렌드 요약")
    print(f"조회 기간: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"평균 관심도: {df[keyword].mean():.1f}")
    print(f"최고 관심도: {df[keyword].max()} (날짜: {df[keyword].idxmax().date()})")
    print(f"최근 관심도: {df[keyword].iloc[-1]}")

    if len(df) >= 10:
        recent_avg = df[keyword].iloc[-5:].mean()
        previous_avg = df[keyword].iloc[-10:-5].mean()
        if recent_avg > previous_avg:
            print("추세: 상승")
        elif recent_avg < previous_avg:
            print("추세: 하락")
        else:
            print("추세: 유지")


def save_trend_to_csv(df, keyword):
    """트렌드 데이터를 CSV 파일로 저장 (표 형태 원본 데이터)"""
    if df is None:
        return None

    filename = f"trend_{keyword}.csv"
    df.to_csv(filename, encoding="utf-8-sig")
    print(f"\n[저장] CSV 파일: {filename}")
    print("  → 엑셀에서 열었을 때 날짜 칸이 '#####'로 보이면,")
    print("    A열 머리글 오른쪽 경계선을 더블클릭하면 정상적으로 보입니다.")
    return filename


def plot_trend(df, keyword):
    """트렌드 데이터를 꺾은선 그래프로 그려서 PNG 이미지 파일로 저장"""
    if df is None:
        return None

    setup_korean_font()

    plt.figure(figsize=(12, 5))
    plt.plot(df.index, df[keyword], marker="o", markersize=3, linewidth=2, color="#2F5496")
    plt.title(f"'{keyword}' 검색 관심도 추이", fontsize=14)
    plt.xlabel("날짜")
    plt.ylabel("관심도 (0~100)")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"trend_{keyword}.png"
    plt.savefig(filename, dpi=150)
    plt.close()

    print(f"[저장] 그래프 이미지: {filename}")
    print("  → CSV 파일 안에는 그래프가 포함되지 않습니다.")
    print("    같은 폴더에 별도로 생성된 이 PNG 파일을 열어서 확인하세요.")
    return filename


if __name__ == "__main__":
    keyword = input("트렌드를 조회할 키워드를 입력하세요: ").strip()

    trend_df = get_google_trend(keyword, period_days=90)
    summarize_trend(trend_df, keyword)
    save_trend_to_csv(trend_df, keyword)
    plot_trend(trend_df, keyword)