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

if not API_KEY:
    st.error("API 키를 찾을 수 없습니다. Streamlit Secrets를 확인해주세요.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# 2. 페이지 및 UI 설정
st.set_page_config(page_title="KIS 7인 투자 위원회 Pro", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .report-container { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .stMetric { background: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 엔진
def get_stock_info(ticker, is_kr):
    try:
        if is_kr:
            today = datetime.now().strftime("%Y%m%d")
            name = stock.get_market_ticker_name(ticker)
            df_f = stock.get_market_fundamental(today, today, ticker)
            if df_f.empty:
                today = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
                df_f = stock.get_market_fundamental(today, datetime.now().strftime("%Y%m%d"), ticker).tail(1)
            
            pbr = float(df_f['PBR'].iloc[0])
            per = float(df_f['PER'].iloc[0])
            div = float(df_f['DIV'].iloc[0])
            cap = int(stock.get_market_cap(today, today, ticker)['시가총액'].iloc[0])
            price = int(stock.get_market_ohlcv(today, today, ticker)['종가'].iloc[0])
            
            return {
                "종목명": name, "티커": ticker, "현재가": f"{price:,}원",
                "PER": f"{per}배", "PBR": f"{pbr}배", "ROE": f"{round(pbr/per*100, 2) if per > 0 else 'N/A'}%",
                "시가총액": f"{round(cap/1e12, 2)}조 원", "배당수익률": f"{div}%",
                "기준일": datetime.now().strftime("%Y-%m-%d")
            }
        else:
            yf_s = yf.Ticker(ticker)
            info = yf_s.info
            return {
                "종목명": info.get('longName'), "티커": ticker, "현재가": f"${info.get('currentPrice')}",
                "PER": f"{info.get('trailingPE')}배", "PBR": f"{info.get('priceToBook')}배",
                "ROE": f"{round(info.get('returnOnEquity', 0)*100, 2)}%",
                "시가총액": f"${round(info.get('marketCap', 0)/1e9, 2)}B",
                "52주고": f"${info.get('fiftyTwoWeekHigh')}", "52주저": f"${info.get('fiftyTwoWeekLow')}",
                "기준일": datetime.now().strftime("%Y-%m-%d")
            }
    except: return None

# 4. 메인 화면 구성
st.title("🏛️ KIS 7인 투자 위원회 전문 분석 시스템")

# 퀵 버튼
st.write("### ⚡ 빠른 종목 분석")
col_q1, col_q2, _ = st.columns([1, 1, 4])
if col_q1.button("🔵 삼성전자 (005930)"): st.session_state.ticker = "005930"; st.session_state.m_type = "국내 주식"
if col_q2.button("🔴 SK하이닉스 (000660)"): st.session_state.ticker = "000660"; st.session_state.m_type = "국내 주식"

st.divider()

# 입력 섹션
c1, c2 = st.columns([1, 2])
with c1:
    market_choice = st.radio("시장 선택", ["국내 주식", "해외 주식"], index=0 if st.session_state.get('m_type') != "해외 주식" else 1)
with c2:
    ticker_val = st.text_input("종목코드 또는 티커 입력", value=st.session_state.get('ticker', '000660'))

if st.button("🚀 위원회 소집 및 심층 분석 시작", type="primary", use_container_width=True):
    with st.spinner("전문가들이 데이터를 검토 중입니다..."):
        is_kr = "국내" in market_choice
        data = get_stock_info(ticker_val, is_kr)
        
        if data:
            # 1. 요약 메트릭 표시
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("종목", data['종목명'])
            m2.metric("현재가", data['현재가'])
            m3.metric("PER", data['PER'])
            m4.metric("ROE", data['ROE'])

            # 2. AI 전문 보고서 생성
            report_prompt = f"""
            당신은 7인 투자 위원회입니다. 아래 실시간 데이터를 바탕으로 BlackBerry(BB) 보고서 예시와 동일한 형식의 전문 리포트를 작성하세요.
            [실시간 데이터]: {data}
            
            지시사항:
            - STEP 1~2 과정을 거쳐 결론, 데이터 요약, 기술지표, 지지/저항선, 위원회 의견(7명), 최종판단, 시나리오를 모두 포함할 것.
            - 52주 고저 데이터가 없으면 현재가 기준으로 지지/저항선을 전문적으로 추정할 것.
            - 출력 포맷은 반드시 깔끔한 마크다운 표와 헤더를 사용할 것.
            """
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=report_prompt)
            st.markdown(response.text)
        else:
            st.error("데이터 수집 실패. 종목코드를 확인해 주세요.")

st.divider()
st.caption("※ 본 분석은 실시간 수집 데이터를 바탕으로 AI가 생성한 시나리오입니다.")
