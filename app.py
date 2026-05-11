import os
import streamlit as st
import pandas as pd
import yfinance as yf
from pykrx import stock
from google import genai
from datetime import datetime, timedelta

# 1. API 연결 설정
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# 2. UI 설정
st.set_page_config(page_title="KIS 7인 투자 위원회 Pro", layout="wide")
st.markdown("""
    <style>
    .stTable { font-size: 0.9rem; }
    .css-1kyx0rg { background-color: #f0f2f6; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 엔진 (KRX 전용)
def get_krx_data(ticker):
    try:
        today = datetime.now().strftime("%Y%m%d")
        # 기본 정보
        name = stock.get_market_ticker_name(ticker)
        df_f = stock.get_market_fundamental(today, today, ticker)
        df_p = stock.get_market_ohlcv(today, today, ticker)
        df_c = stock.get_market_cap(today, today, ticker)
        
        # 데이터가 비어있을 경우 최근 영업일 찾기
        if df_f.empty:
            prev_day = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
            df_f = stock.get_market_fundamental(prev_day, today, ticker).tail(1)
            df_p = stock.get_market_ohlcv(prev_day, today, ticker).tail(1)
            df_c = stock.get_market_cap(prev_day, today, ticker).tail(1)

        data = {
            "종목명": name,
            "현재가": int(df_p['종가'].iloc[0]),
            "PER": float(df_f['PER'].iloc[0]),
            "PBR": float(df_f['PBR'].iloc[0]),
            "ROE": round(float(df_f['PBR'].iloc[0]) / float(df_f['PER'].iloc[0]) * 100, 2) if df_f['PER'].iloc[0] > 0 else "N/A",
            "시가총액": int(df_c['시가총액'].iloc[0]),
            "배당수익률": float(df_f['DIV'].iloc[0]),
            "거래량": int(df_p['거래량'].iloc[0]),
            "52주고": "지원 예정", # OHLCV 범위 데이터 필요
            "52주저": "지원 예정"
        }
        
        # 동종 업계 비교 데이터 추출
        sector_code = stock.get_market_ticker_list(market="ALL")
        # 간단한 로직: 동일 시장(KOSPI/KOSDAQ) 내 시총 상위 비교
        market_type = "KOSPI" if ticker in stock.get_market_ticker_list(market="KOSPI") else "KOSDAQ"
        comparison_df = stock.get_market_fundamental(today, today, market=market_type).nlargest(5, 'PER')
        
        return data, comparison_df
    except Exception as e:
        return None, None

# 4. 데이터 수집 엔진 (해외 전용)
def get_us_data(ticker):
    try:
        yf_stock = yf.Ticker(ticker)
        info = yf_stock.info
        data = {
            "종목명": info.get('longName'),
            "현재가": info.get('currentPrice'),
            "PER": info.get('trailingPE'),
            "PBR": info.get('priceToBook'),
            "ROE": round(info.get('returnOnEquity', 0) * 100, 2),
            "시가총액": info.get('marketCap'),
            "배당수익률": round(info.get('dividendYield', 0) * 100, 2),
            "52주고": info.get('fiftyTwoWeekHigh'),
            "52주저": info.get('fiftyTwoWeekLow')
        }
        return data
    except:
        return None

# 5. 메인 레이아웃
st.title("🏛️ KIS 7인 투자 위원회 Pro")
st.caption("한국 주식은 pykrx(실시간 KRX 데이터), 해외 주식은 yfinance 엔진을 사용합니다.")

with st.sidebar:
    st.header("🔍 종목 설정")
    region = st.radio("시장 선택", ["국내(KOSPI/KOSDAQ)", "해외(NASDAQ/NYSE)"])
    ticker_input = st.text_input("종목코드/티커", value="000660" if region == "국내(KOSPI/KOSDAQ)" else "NVDA")
    analyze_btn = st.button("전문가 위원회 소집", type="primary")

if analyze_btn:
    with st.spinner("데이터 분석 및 위원회 리포트 생성 중..."):
        stock_info = None
        comp_data = None
        
        if region == "국내(KOSPI/KOSDAQ)":
            stock_info, comp_data = get_krx_data(ticker_input)
        else:
            stock_info = get_us_data(ticker_input)

        if not stock_info:
            st.error("데이터를 수집할 수 없습니다. 코드를 확인해 주세요.")
            st.stop()

        # UI 출력: 상단 요약 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("현재가", f"{stock_info['현재가']:,}")
        c2.metric("PER", f"{stock_info['PER']}배")
        c3.metric("PBR", f"{stock_info['PBR']}배")
        c4.metric("ROE", f"{stock_info['ROE']}%")

        if comp_data is not None:
            with st.expander("📊 동종 업계 비교 (시총 상위)", expanded=True):
                st.table(comp_data[['BPS', 'PER', 'PBR', 'EPS', 'DIV']])

        # AI 프롬프트 생성
        prompt = f"""
당신은 7인 투자 위원회입니다. 아래 [실시간 수집 데이터]를 바탕으로 전문적인 투자 리포트를 작성하세요.
특히 '동종 업계 비교 데이터'가 있다면 이를 참고하여 해당 종목의 밸류에이션 위치를 린치와 버핏의 관점에서 비평하십시오.

[실시간 수집 데이터]
{stock_info}

[동종 업계 지표]
{comp_data.to_string() if comp_data is not None else "해외 주식 비교 데이터 생략"}

---
(이후 기존의 7인 위원회 출력 양식 적용)
"""
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        st.markdown(response.text)

st.divider()
st.caption("※ 데이터 출처: KRX(국내), Yahoo Finance(해외). 모든 투자의 책임은 본인에게 있습니다.")
