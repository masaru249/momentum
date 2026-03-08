import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO

# --- Streamlit 페이지 기본 설정 및 CSS 주입 ---
st.set_page_config(page_title="통합 듀얼 모멘텀 대시보드", layout="wide")

st.markdown("""
<style>
/* 자산 이름(Label) 글자 크기 및 굵기 설정 */
[data-testid="stMetricLabel"] p {
    font-size: 22px !important;
    font-weight: 800 !important;
}
/* 평균모멘텀스코어(Value) 부분 글자 크기를 약간 작게 조정 */
[data-testid="stMetricValue"] {
    font-size: 18px !important; 
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧭 1. 사이드바 (Sidebar) 메뉴 구성
# ==========================================
st.sidebar.title("🧭 투자 유니버스 선택")
market_choice = st.sidebar.radio(
    "전략을 선택하세요:", 
    [
        "🇰🇷 한국주식/채권/현금 듀얼모멘텀", 
        "🇺🇸 미국주식/채권/현금 듀얼모멘텀",
        "🌏 한국주식/미국주식/금/현금 듀얼모멘텀"
    ]
)

# 선택한 메뉴에 따라 변수 동적 할당
if "한국주식/채권" in market_choice:
    st_title = "📊 한국주식/채권/현금 듀얼모멘텀 전략"
    st_desc = "- **한국주식**: KODEX 200 (069500)\n- **한국채권**: KODEX 국채선물10년 (152380)\n- **현금**: 파킹통장 (연 1.6% 단리/복리 계산 적용)"
    tickers = ['069500', '152380']
    names = ['한국주식', '한국채권', '현금']
    emojis = ['🇰🇷', '📜', '💵']
    colors = ['#ef553b', '#00cc96', '#636efa']
    # 전략 작동 원리 텍스트 설정
    info_text = "💡 **전략 작동 원리:** 전통 듀얼모멘텀 전략과는 달리 직전달 말일의 종가와 과거 1~12개월 전 말일의 종가 비교하여 모멘텀 스코어를 계산하므로 좀 더 정교한 투자 비율을 정할수 있습니다. 또한, 주식/채권이 모두 하락장이라 0점을 받게 되면, 전체 점수 중 현금만 남게 되어 포트폴리오의 100%가 현금으로 이동하여 방어력이 극대화 됩니다. 본 전략은 각각 자산의 단독투자 대비 샤프지수를 높이기 위한 전략입니다."

elif "미국주식/채권" in market_choice:
    st_title = "📊 미국주식/채권/현금 듀얼모멘텀 전략"
    st_desc = "- **미국주식**: SPY ETF(S&P500 etf)\n- **미국채권**: IEF ETF (미국 중기국채 7-10년)\n- **현금**: 파킹통장 (연 1.6% 단리/복리 계산 적용)"
    tickers = ['SPY', 'IEF']
    names = ['미국주식', '미국채권', '현금']
    emojis = ['🇺🇸', '📜', '💵']
    colors = ['#1f77b4', '#ff7f0e', '#636efa']
    # 전략 작동 원리 텍스트 설정
    info_text = "💡 **전략 작동 원리:** 전통 듀얼모멘텀 전략과는 달리 직전달 말일의 종가와 과거 1~12개월 전 말일의 종가 비교하여 모멘텀 스코어를 계산하므로 좀 더 정교한 투자 비율을 정할수 있습니다. 또한, 주식/채권이 모두 하락장이라 0점을 받게 되면, 전체 점수 중 현금만 남게 되어 포트폴리오의 100%가 현금으로 이동하여 방어력이 극대화 됩니다. 본 전략은 각각 자산의 단독투자 대비 샤프지수를 높이기 위한 전략입니다."

else:
    st_title = "📊 한국/미국/금/현금 듀얼모멘텀 전략"
    st_desc = "- **한국주식**: EWY ETF (iShares MSCI South Korea)\n- **미국주식**: SPY ETF(S&P500 etf)\n- **금**: GLD ETF (SPDR Gold Shares)\n- **현금**: 파킹통장 (연 1.6% 단리/복리 적용)"
    tickers = ['EWY', 'SPY', 'GLD']
    names = ['한국주식', '미국주식', '금', '현금']
    emojis = ['🇰🇷', '🇺🇸', '✨', '💵']
    colors = ['#ef553b', '#1f77b4', '#ffd700', '#636efa']
    # 전략 작동 원리 텍스트 설정 (주식/채권/금 모두 하락장 반영)
    info_text = "💡 **전략 작동 원리:** 전통 듀얼모멘텀 전략과는 달리 직전달 말일의 종가와 과거 1~12개월 전 말일의 종가 비교하여 모멘텀 스코어를 계산하므로 좀 더 정교한 투자 비율을 정할수 있습니다. 또한, 주식/채권/금이 모두 하락장이라 0점을 받게 되면, 전체 점수 중 현금만 남게 되어 포트폴리오의 100%가 현금으로 이동하여 방어력이 극대화 됩니다. 본 전략은 각각 자산의 단독투자 대비 샤프지수를 높이기 위한 전략입니다."

st.title(st_title)
st.markdown(st_desc)
# 평균모멘텀스코어 설명 (마크다운 줄바꿈 적용)
st.markdown("- **평균모멘텀스코어**:  \n직전달 말일의 종가와 과거 1~12개월 전 말일의 종가와 각각 비교하여, 직전달 말일의 종가가 더 큰 경우를 1, 작은 경우를 0으로하는 스코어를 정의하고, 스코어를 합산한뒤, 12로 나누어 평균을 구한 값 (0.0 ~ 1.0)")

# --- 엑셀 변환 함수 ---
@st.cache_data
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Data')
    return output.getvalue()

# --- 데이터 수집 함수 ---
@st.cache_data
def load_data(tickers_list, names_list):
    start_date = (datetime.today() - relativedelta(years=11)).strftime('%Y-%m-%d')
    df_dict = {}
    
    # 실제 시장 티커 데이터 다운로드
    for ticker, name in zip(tickers_list, names_list[:len(tickers_list)]):
        df_dict[name] = fdr.DataReader(ticker, start_date)['Close']
        
    df = pd.DataFrame(df_dict).ffill()
    df_monthly = df.resample('ME').last()
    
    # 당월 미확정 데이터 제외
    today = datetime.today()
    if df_monthly.index[-1].year == today.year and df_monthly.index[-1].month == today.month:
        df_monthly = df_monthly.iloc[:-1]
    
    # 현금(파킹통장) 연 1.6% 수익률 생성 (모든 전략에 공통 적용)
    monthly_rate = 0.016 / 12
    cash_index = [10000]
    for _ in range(1, len(df_monthly)):
        cash_index.append(cash_index[-1] * (1 + monthly_rate))
    df_monthly['현금'] = cash_index
        
    return df_monthly

# --- 평균모멘텀스코어 계산 ---
def calc_momentum_scores(df_monthly):
    scores = pd.DataFrame(index=df_monthly.index, columns=df_monthly.columns).fillna(0)
    for i in range(1, 13):
        condition = (df_monthly > df_monthly.shift(i)).astype(int)
        scores = scores + condition
        
    scores = scores.dropna()[12:]
    avg_scores = scores / 12.0
    return avg_scores

# ==========================================
# ⚙️ 3. 데이터 로드 및 전략 백테스트 연산
# ==========================================
df_monthly = load_data(tickers, names)
avg_scores_df = calc_momentum_scores(df_monthly)

total_scores = avg_scores_df.sum(axis=1)
weights_df = avg_scores_df.div(total_scores, axis=0) * 100 

# 누적 수익률 계산
returns_df = df_monthly.pct_change().dropna()

shifted_weights = (weights_df / 100.0).shift(1).dropna()
common_index = shifted_weights.index.intersection(returns_df.index)
shifted_weights = shifted_weights.loc[common_index]
returns_df = returns_df.loc[common_index]

port_returns = (shifted_weights * returns_df).sum(axis=1)
cum_port = (1 + port_returns).cumprod() * 100
cum_port.name = '💡 듀얼 모멘텀 전략'

# 벤치마크 (단순 보유) 누적 수익률 계산
cum_assets = (1 + returns_df[names]).cumprod() * 100
rename_dict = {names[i]: f'{emojis[i]} {names[i]} (단순보유)' for i in range(len(names))}
cum_assets.rename(columns=rename_dict, inplace=True)

backtest_df = pd.concat([cum_port, cum_assets], axis=1)

first_date = backtest_df.index[0] - pd.DateOffset(months=1)
base_row = pd.DataFrame(100, index=[first_date], columns=backtest_df.columns)
backtest_df = pd.concat([base_row, backtest_df])

# 성과 지표 (CAGR, MDD, Sharpe) 계산
monthly_returns_all = backtest_df.pct_change().dropna()
years = len(monthly_returns_all) / 12
cagr = (backtest_df.iloc[-1] / 100) ** (1 / years) - 1

roll_max = backtest_df.cummax()
drawdown = backtest_df / roll_max - 1.0
mdd = drawdown.min()

rf_rate_annual = 0.016
rf_rate_monthly = rf_rate_annual / 12
excess_returns = monthly_returns_all - rf_rate_monthly

# 표준편차가 0인 경우(현금) 결측치 처리 후 샤프지수 0으로 고정
std_dev = monthly_returns_all.std().replace(0, np.nan)
sharpe = (excess_returns.mean() / std_dev) * np.sqrt(12)
sharpe.fillna(0.0, inplace=True)
if '💵 현금 (단순보유)' in sharpe.index:
    sharpe['💵 현금 (단순보유)'] = 0.0

performance_summary = pd.DataFrame({
    '누적 수익률': (backtest_df.iloc[-1] - 100).apply(lambda x: f"{x:.2f}%"),
    'CAGR (연평균)': (cagr * 100).apply(lambda x: f"{x:.2f}%"),
    'MDD (최대낙폭)': (mdd * 100).apply(lambda x: f"{x:.2f}%"),
    '샤프 지수 (Sharpe)': sharpe.apply(lambda x: f"{x:.2f}")
})

# 다운로드용 데이터 포맷 변경
excel_df_monthly = df_monthly.copy()
excel_df_monthly.index = excel_df_monthly.index.strftime('%Y-%m')
excel_avg_scores = avg_scores_df.copy()
excel_avg_scores.index = excel_avg_scores.index.strftime('%Y-%m')
excel_weights = weights_df.copy()
excel_weights.index = excel_weights.index.strftime('%Y-%m')

# 차트 색상 매핑 동적 생성
color_map = {'💡 듀얼 모멘텀 전략': '#FF9900'}
for idx, asset in enumerate(names):
    color_map[asset] = colors[idx]
    color_map[f'{emojis[idx]} {asset} (단순보유)'] = colors[idx]

# ==========================================
# 🖥️ 4. 화면 출력 (Tabs)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["💡 최신 리밸런싱 가이드", "📈 비중 추이 및 시각화", "🚀 10년 누적 백테스트", "🗂️ 상세 데이터베이스"])

with tab1:
    latest_date = weights_df.index[-1].strftime('%Y년 %m월')
    st.subheader(f"🔔 최신 리밸런싱 비율 ({latest_date} 마지막 거래일 기준)")
    
    latest_scores = avg_scores_df.iloc[-1]
    latest_weights = weights_df.iloc[-1]
    
    # 자산 개수에 맞게 열(Column) 동적 생성 (3개 또는 4개)
    cols = st.columns(len(names))
    for i, col in enumerate(cols):
        col.metric(
            f"{emojis[i]} {names[i]}", 
            f"평균모멘텀스코어: {latest_scores[names[i]]:.2f}", 
            f"투자 비중: {latest_weights[names[i]]:.1f}%"
        )
    
    # 동적 텍스트 적용 (선택한 전략에 맞게 문구 자동 변환)
    st.info(info_text)

    fig = px.pie(
        names=latest_weights.index, 
        values=latest_weights.values, 
        title=f"{latest_date} 목표 포트폴리오 비중",
        hole=0.4,
        color_discrete_map=color_map
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📊 과거 투자 비중 변화 추이")
    fig_area = px.area(
        weights_df, 
        title="시간에 따른 자산별 투자 비중 (%)",
        labels={'value': '비중 (%)', 'Date': '날짜'},
        color_discrete_map=color_map
    )
    fig_area.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig_area, use_container_width=True)
    
    st.subheader("📉 최근 12개월 평균모멘텀스코어 변화")
    fig_line = px.line(
        avg_scores_df.tail(12), 
        markers=True,
        title="최근 1년 평균 스코어 변동 (0.0~1.0)",
        labels={'value': '스코어', 'Date': '날짜'}
    )
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    st.subheader("🚀 과거 10년 성과 비교 (전략 vs 단순 보유)")
    st.write("### 🏆 포트폴리오 성과 요약")
    st.table(performance_summary)
    
    fig_backtest = px.line(
        backtest_df,
        title="포트폴리오 및 개별 자산 누적 수익률 비교 (Equity Curve)",
        labels={'value': '누적 자산 가치 (100 시작)', 'index': '연도', 'variable': '구분'},
        color_discrete_map=color_map
    )
    fig_backtest.update_traces(line=dict(width=3), selector=dict(name='💡 듀얼 모멘텀 전략'))
    fig_backtest.update_traces(line=dict(width=1.5), selector=lambda t: t.name != '💡 듀얼 모멘텀 전략')
    st.plotly_chart(fig_backtest, use_container_width=True)

with tab4:
    st.subheader("검증용 상세 데이터 확인 및 다운로드")
    
    st.write("✅ **1. 월말 ETF 종가 데이터**")
    st.dataframe(df_monthly.sort_index(ascending=False).round(2), use_container_width=True)
    st.download_button(
        label="📥 종가 데이터 엑셀 다운로드",
        data=convert_df_to_excel(excel_df_monthly.sort_index(ascending=False).round(2)),
        file_name="월말_종가데이터.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='dl1'
    )
    st.divider()

    st.write("✅ **2. 산출된 평균모멘텀스코어 (0.0 ~ 1.0)**")
    st.dataframe(avg_scores_df.sort_index(ascending=False).round(4), use_container_width=True)
    st.download_button(
        label="📥 모멘텀 스코어 엑셀 다운로드",
        data=convert_df_to_excel(excel_avg_scores.sort_index(ascending=False).round(4)),
        file_name="평균모멘텀스코어.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='dl2'
    )
    st.divider()

    st.write("✅ **3. 최종 산출된 투자 비중 (%)**")
    st.dataframe(weights_df.sort_index(ascending=False).round(2), use_container_width=True)
    st.download_button(
        label="📥 투자 비중 엑셀 다운로드",
        data=convert_df_to_excel(excel_weights.sort_index(ascending=False).round(2)),
        file_name="최종투자비중.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key='dl3'
    )