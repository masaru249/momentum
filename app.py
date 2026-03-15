import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO

# --- Streamlit 페이지 기본 설정 및 CSS 주입 ---
st.set_page_config(page_title="통합 퀀트 대시보드", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricLabel"] p {
    font-size: 22px !important;
    font-weight: 800 !important;
}
[data-testid="stMetricValue"] {
    font-size: 18px !important; 
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧭 1. 사이드바 (Sidebar) 전체 메뉴 구성
# ==========================================
st.sidebar.markdown("### 🧭 핵심 투자 전략")

# 직관적인 2개의 핵심 리스트 메뉴로 개편
market_choice = st.sidebar.radio(
    label="메뉴 선택",
    label_visibility="collapsed",
    options=[
        "🚀 30/30/20/20 성장최적화 자산배분모델",
        "🌏 코스피/나스닥/금/현금 듀얼모멘텀"
    ]
)

# 메뉴 플래그 설정
is_static = market_choice == "🚀 30/30/20/20 성장최적화 자산배분모델"
is_dynamic = not is_static

# ==========================================
# ⚙️ 2. 전략별 변수 및 로직 동적 할당
# ==========================================

# --- [A] 정적 자산배분 세팅 ---
if is_static:
    st_title = "🚀 30/30/20/20 성장최적화 자산배분모델"
    st_desc = "나스닥과 S&P500으로 수익성을 강력하게 끌어올리면서도, 장기채와 금으로 효율적인 방어선을 구축한 모델입니다."
    tickers = ['QQQ', 'SPY', 'TLT', 'GLD']
    names = ['미국기술주(QQQ)', '미국대형주(SPY)', '장기채(TLT)', '금(GLD)']
    weights_dict = {'미국기술주(QQQ)': 0.3, '미국대형주(SPY)': 0.3, '장기채(TLT)': 0.2, '금(GLD)': 0.2}
    
    info_text = """💡 **전략 설명 및 성과 해석:**
과거 60/40이 채권에 전적으로 방어를 의존했다면, 이 모델은 방어막을 듀레이션(TLT)과 실물 자산(GLD)으로 정교하게 분산시킵니다. 포트폴리오의 60%를 주식에 배분함으로써 장기 연평균 수익률(CAGR)은 11.5% ~ 13.0%로 매우 강력하게 뻗어나갑니다. SPY와 QQQ를 동일 비중으로 섞음으로써 대형 우량주의 안정적인 베타와 기술주의 초과 수익 알파를 모두 획득합니다.

주목할 점은 위기 시의 상호 보완 작용입니다. 2008년 금융 위기와 같이 성장이 붕괴할 때는 20%의 장기채(TLT)가 가격이 치솟으며 주식의 손실을 방어하고, 2022년처럼 채권마저 붕괴하는 극심한 금리 인상기에는 20%의 금(GLD)이 실질 가치를 유지하며 방어선을 형성합니다. 

그 결과 이 포트폴리오의 실질적인 최대 낙폭은 -22% ~ -25% 선에서 방어되며, 샤프 지수는 0.95 ~ 1.05 수준을 기록해 주식에 60%나 투자했음에도 불구하고 100% SPY(MDD -50.8%, 샤프 0.8 내외)보다 훨씬 우수한 효율 경계선(Efficient Frontier)을 구축하게 됩니다.

🔄 **리밸런싱 주기:** 매년 1회 (1월 첫 거래일 기준)"""

# --- [B] 동적 자산배분 세팅 ---
else:
    st_title = "📊 코스피/나스닥/금/현금 듀얼모멘텀 전략"
    st_desc = "- **한국주식**: EWY ETF (MSCI South Korea / 코스피 프록시)\n- **미국주식**: QQQ ETF (나스닥100)\n- **금**: GLD ETF (SPDR Gold Shares)\n- **현금**: 파킹통장 (연 1.6% 단리/복리 적용)"
    tickers = ['EWY', 'QQQ', 'GLD']
    names = ['코스피(EWY)', '나스닥(QQQ)', '금(GLD)', '현금']
    emojis = ['🇰🇷', '🇺🇸', '✨', '💵']
    colors = ['#ef553b', '#1f77b4', '#ffd700', '#636efa']
    info_text = "💡 **전략 작동 원리:** 직전달 말일 종가와 과거 1~12개월 전 말일 종가를 비교해 모멘텀 스코어를 계산합니다. 모든 자산이 하락장이면 포트폴리오 100%가 현금으로 이동하여 방어력이 극대화됩니다.\n\n🔄 **리밸런싱 주기:** 매월 1회 (월말 기준 스코어 산출 후 월초 리밸런싱)"

st.title(st_title)
st.markdown(st_desc)

if is_dynamic:
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
def load_data(tickers_list, names_list, include_cash=True):
    start_date = '1990-01-01' 
    df_dict = {}
    
    for ticker, name in zip(tickers_list, names_list):
        if name == '현금': continue
        raw_data = fdr.DataReader(ticker, start_date)
        raw_data = raw_data[~raw_data.index.duplicated(keep='last')]
        df_dict[name] = raw_data['Close']
        
    df = pd.DataFrame(df_dict).ffill()
    df_monthly = df.resample('ME').last().dropna() 
    
    today = datetime.today()
    if df_monthly.index[-1].year == today.year and df_monthly.index[-1].month == today.month:
        df_monthly = df_monthly.iloc[:-1]
    
    if include_cash:
        monthly_rate = 0.016 / 12
        cash_index = [10000]
        for _ in range(1, len(df_monthly)):
            cash_index.append(cash_index[-1] * (1 + monthly_rate))
        df_monthly['현금'] = cash_index
        
    return df_monthly

# --- 글로벌 자산군 랭킹 데이터 수집 (공통 탭용) ---
@st.cache_data
def load_global_ranking_data():
    ranking_tickers = ['QQQ', 'SPY', 'EWY', 'EWJ', 'EWZ', 'IEF', 'TLT', 'DBC', 'DBA', 'GLD']
    return load_data(ranking_tickers, ranking_tickers, include_cash=False)

def calc_momentum_scores(df_monthly):
    scores = pd.DataFrame(index=df_monthly.index, columns=df_monthly.columns).fillna(0)
    for i in range(1, 13):
        condition = (df_monthly > df_monthly.shift(i)).astype(int)
        scores = scores + condition
    return scores.dropna()[12:] / 12.0

global_ranking_df = load_global_ranking_data()
global_scores_df = calc_momentum_scores(global_ranking_df)

# 글로벌 랭킹 탭을 그리는 헬퍼 함수
def render_ranking_tab():
    latest_date = global_scores_df.index[-1].strftime('%Y년 %m월')
    st.subheader(f"🔔 {latest_date} 마지막 거래일 기준 글로벌 자산군 스코어")
    st.info("💡 **메뉴 설명:** 특정 비중을 계산하지 않고, 각 자산이 현재 상승장(1.0)인지 하락장(0.0)인지 모멘텀 스코어만 직관적으로 파악합니다.")
    
    # 💡 정렬(.sort_values) 제거: 배열에 선언된 원래 순서(QQQ, SPY, EWY...) 그대로 유지
    latest_scores = global_scores_df.iloc[-1]
    
    fig_bar = px.bar(
        x=latest_scores.index, 
        y=latest_scores.values,
        text=latest_scores.values.round(2),
        labels={'x': '자산군 (ETF 티커)', 'y': '평균모멘텀스코어'},
        title="현재 글로벌 자산군 모멘텀 스코어 (1.0 = 완벽한 상승 추세)",
        color=latest_scores.values,
        color_continuous_scale=px.colors.diverging.RdYlGn,
        range_color=[0, 1]
    )
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(yaxis_range=[0, 1.1])
    st.plotly_chart(fig_bar, use_container_width=True)

    etf_descriptions = {
        'QQQ': 'Invesco QQQ Trust (미국 나스닥 100)',
        'SPY': 'SPDR S&P 500 ETF Trust (미국 S&P 500)',
        'EWY': 'iShares MSCI South Korea ETF (한국 주식)',
        'EWJ': 'iShares MSCI Japan ETF (일본 주식)',
        'EWZ': 'iShares MSCI Brazil ETF (브라질 주식)',
        'IEF': 'iShares 7-10 Year Treasury Bond ETF (미국 7-10년 중기국채)',
        'TLT': 'iShares 20+ Year Treasury Bond ETF (미국 20년 이상 장기국채)',
        'DBC': 'Invesco DB Commodity Index Tracking Fund (원자재 종합)',
        'DBA': 'Invesco DB Agriculture Fund (농산물)',
        'GLD': 'SPDR Gold Shares (금 실물)'
    }
    with st.expander("📌 분석 대상 ETF 상세 설명", expanded=False):
        for tk, desc in etf_descriptions.items():
            st.markdown(f"- **{tk}** : {desc}")

# --- 정적 자산배분 연 1회 리밸런싱 백테스트 함수 ---
def backtest_static_portfolio(returns_df, weights_dict):
    assets = list(weights_dict.keys())
    rets = returns_df[assets]
    weights = np.array([weights_dict[a] for a in assets])
    
    port_val = 100.0
    vals = []
    
    current_alloc = weights * port_val
    for idx, row in rets.iterrows():
        # 정적 자산배분은 매년 1월 연 1회 리밸런싱
        if idx.month == 1: 
            current_alloc = weights * port_val
        current_alloc = current_alloc * (1 + row.values)
        port_val = current_alloc.sum()
        vals.append(port_val)
        
    return pd.Series(vals, index=rets.index)


# ==========================================
# 🖥️ 3. 데이터 연산 및 화면 출력
# ==========================================

# -------------------------------------------------------------------------
# [A] 정적 자산배분 (30/30/20/20) 화면 출력
# -------------------------------------------------------------------------
if is_static:
    df_monthly = load_data(tickers, names, include_cash=False)
    monthly_returns = df_monthly.pct_change().dropna()
    
    # 30/30/20/20 포트폴리오 백테스트 계산
    cum_port = backtest_static_portfolio(monthly_returns, weights_dict)
    cum_port.name = '🚀 30/30/20/20 성장최적화'
    
    # 벤치마크 (SPY 단독) 계산
    cum_spy = (1 + monthly_returns['미국대형주(SPY)']).cumprod() * 100
    cum_spy.name = '🇺🇸 S&P500 (SPY 단순보유)'
    
    # 벤치마크 (QQQ 단독) 추가 계산
    cum_qqq = (1 + monthly_returns['미국기술주(QQQ)']).cumprod() * 100
    cum_qqq.name = '📈 나스닥100 (QQQ 단순보유)'
    
    backtest_df = pd.concat([cum_port, cum_spy, cum_qqq], axis=1)
    
    first_date = backtest_df.index[0] - pd.DateOffset(months=1)
    base_row = pd.DataFrame(100, index=[first_date], columns=backtest_df.columns)
    backtest_df = pd.concat([base_row, backtest_df])

    monthly_returns_all = backtest_df.pct_change().dropna()
    
    years = len(monthly_returns_all) / 12
    n_years = round(years, 1)
    cagr = (backtest_df.iloc[-1] / 100) ** (1 / years) - 1
    
    roll_max = backtest_df.cummax()
    drawdown = backtest_df / roll_max - 1.0
    mdd = drawdown.min()
    
    rf_rate_annual = 0.016
    rf_rate_monthly = rf_rate_annual / 12
    excess_returns = monthly_returns_all - rf_rate_monthly
    sharpe = (excess_returns.mean() / monthly_returns_all.std()) * np.sqrt(12)

    performance_summary = pd.DataFrame({
        '누적 수익률': (backtest_df.iloc[-1] - 100).apply(lambda x: f"{x:.2f}%"),
        'CAGR (연평균)': (cagr * 100).apply(lambda x: f"{x:.2f}%"),
        'MDD (최대낙폭)': (mdd * 100).apply(lambda x: f"{x:.2f}%"),
        '샤프 지수 (Sharpe)': sharpe.apply(lambda x: f"{x:.2f}")
    })

    # 💡 글로벌 자산군 랭킹 탭(tab4)을 완전히 제거함
    tab1, tab2, tab3 = st.tabs(["💡 포트폴리오 비중 및 설명", f"🚀 {n_years}년 누적 백테스트", "🗂️ 상세 데이터베이스"])

    with tab1:
        st.subheader(f"🔔 포트폴리오 고정 비율")
        st.info(info_text)
        
        plot_weights = pd.Series(weights_dict) * 100
        fig_pie = px.pie(
            names=plot_weights.index, 
            values=plot_weights.values, 
            title="자산별 투자 비중",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader(f"🚀 과거 {n_years}년 성과 지표 비교")
        st.caption("※ 매년 1회 (1월 첫 거래일) 목표 비중으로 리밸런싱한 기준입니다.")
        st.table(performance_summary)
        
        fig_backtest = px.line(
            backtest_df,
            title="성장최적화 모델 vs SPY & QQQ 누적 수익률 (Equity Curve)",
            labels={'value': '누적 자산 가치 (100 시작)', 'index': '연도', 'variable': '구분'}
        )
        fig_backtest.update_traces(line=dict(width=3.5), selector=dict(name=cum_port.name))
        fig_backtest.update_traces(line=dict(width=1.5), selector=dict(name=cum_spy.name))
        fig_backtest.update_traces(line=dict(width=1.5), selector=dict(name=cum_qqq.name))
        st.plotly_chart(fig_backtest, use_container_width=True)

    with tab3:
        st.subheader("검증용 상세 데이터 확인")
        st.dataframe(df_monthly.sort_index(ascending=False).round(2), use_container_width=True)

# -------------------------------------------------------------------------
# [B] 동적 자산배분 화면 (듀얼 모멘텀)
# -------------------------------------------------------------------------
else:
    df_monthly = load_data(tickers, names, include_cash=True)
    monthly_returns = df_monthly.pct_change().dropna()
    
    avg_scores_df = calc_momentum_scores(df_monthly)

    total_scores = avg_scores_df.sum(axis=1)
    weights_df = avg_scores_df.div(total_scores, axis=0) * 100 

    shifted_weights = (weights_df / 100.0).shift(1).dropna()
    common_index = shifted_weights.index.intersection(monthly_returns.index)
    shifted_weights = shifted_weights.loc[common_index]
    returns_df = monthly_returns.loc[common_index]

    port_returns = (shifted_weights * returns_df).sum(axis=1)
    cum_port = (1 + port_returns).cumprod() * 100
    cum_port.name = '💡 듀얼 모멘텀 전략'

    cum_assets = (1 + returns_df[names]).cumprod() * 100
    rename_dict = {names[i]: f'{emojis[i]} {names[i]} (단순보유)' for i in range(len(names))}
    cum_assets.rename(columns=rename_dict, inplace=True)

    backtest_df = pd.concat([cum_port, cum_assets], axis=1)

    first_date = backtest_df.index[0] - pd.DateOffset(months=1)
    base_row = pd.DataFrame(100, index=[first_date], columns=backtest_df.columns)
    backtest_df = pd.concat([base_row, backtest_df])

    monthly_returns_all = backtest_df.pct_change().dropna()
    years = len(monthly_returns_all) / 12
    n_years = round(years, 1)
    cagr = (backtest_df.iloc[-1] / 100) ** (1 / years) - 1

    roll_max = backtest_df.cummax()
    drawdown = backtest_df / roll_max - 1.0
    mdd = drawdown.min()

    rf_rate_annual = 0.016
    rf_rate_monthly = rf_rate_annual / 12
    excess_returns = monthly_returns_all - rf_rate_monthly
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

    color_map = {'💡 듀얼 모멘텀 전략': '#FF9900'}
    for idx, asset in enumerate(names):
        color_map[asset] = colors[idx]
        color_map[f'{emojis[idx]} {asset} (단순보유)'] = colors[idx]

    # 탭 구성 유지: 마지막에 글로벌 자산군 랭킹(정렬 안된 버전) 탭 포함
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💡 최신 리밸런싱 가이드", "📈 비중 추이 및 시각화", f"🚀 {n_years}년 누적 백테스트", "🗂️ 상세 데이터베이스", "📊 글로벌 자산군 랭킹"])

    with tab1:
        latest_date = weights_df.index[-1].strftime('%Y년 %m월')
        st.subheader(f"🔔 최신 리밸런싱 비율 ({latest_date} 마지막 거래일 기준)")
        
        latest_scores = avg_scores_df.iloc[-1]
        latest_weights = weights_df.iloc[-1]
        
        cols = st.columns(len(names))
        for i, col in enumerate(cols):
            col.metric(
                f"{emojis[i]} {names[i]}", 
                f"평균모멘텀스코어: {latest_scores[names[i]]:.2f}", 
                f"투자 비중: {latest_weights[names[i]]:.1f}%"
            )
        
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
        st.subheader(f"🚀 과거 {n_years}년 성과 비교 (전략 vs 단순 보유)")
        st.caption("※ 동적 자산배분은 매월 1회 리밸런싱을 진행한 결과입니다.")
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
        st.subheader("검증용 상세 데이터 확인")
        st.dataframe(df_monthly.sort_index(ascending=False).round(2), use_container_width=True)
        
    with tab5:
        # 💡 정렬 로직이 제거된 랭킹 탭 표출
        render_ranking_tab()
