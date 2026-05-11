import os
import streamlit as st
import yfinance as yf
from google import genai

# 1. 환경 설정 및 API 연결 (클라우드/로컬 자동 대응)
try:
    # 1순위: Streamlit Cloud의 보안 금고(Secrets)에서 키를 찾음
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # 2순위: 내 컴퓨터(로컬)일 경우 .env 파일에서 키를 찾음
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("API 키를 찾을 수 없습니다.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# --- 이하 2. 페이지 및 UI 설정 부분부터는 기존 코드와 100% 동일하게 유지하시면 됩니다 ---
# st.set_page_config(...)

# 2. 페이지 및 UI 설정 (이전 프로젝트 감성 적용)
st.set_page_config(page_title="KIS 7인 투자 위원회", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .hero-container { display: flex; justify-content: center; margin-bottom: 40px; margin-top: 20px; }
    .hero-box {
        background: rgba(30, 39, 46, 0.8);
        backdrop-filter: blur(15px);
        padding: 40px 60px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        text-align: center;
        width: fit-content;
    }
    .hero-title { 
        font-size: 34px; font-weight: 900; 
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px; 
    }
    .hero-sub { font-size: 16px; color: #dfe6e9; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 함수 (STEP 0)
@st.cache_data(ttl=3600) # 1시간 동안 데이터 캐싱
def get_stock_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 7인 위원회가 요구하는 핵심 데이터 추출
        data = {
            "종목명": info.get('longName', ticker_symbol),
            "현재가": info.get('currentPrice', 'N/A'),
            "PER": info.get('trailingPE', 'N/A'),
            "PBR": info.get('priceToBook', 'N/A'),
            "ROE": info.get('returnOnEquity', 'N/A'),
            "EPS": info.get('trailingEps', 'N/A'),
            "매출성장률": info.get('revenueGrowth', 'N/A'),
            "부채비율": info.get('debtToEquity', 'N/A'),
            "FCF": info.get('freeCashflow', 'N/A'),
            "52주고": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52주저": info.get('fiftyTwoWeekLow', 'N/A'),
            "거래량": info.get('volume', 'N/A'),
            "시가총액": info.get('marketCap', 'N/A'),
            "배당수익률": info.get('dividendYield', 'N/A')
        }
        return data
    except Exception as e:
        return None

# 4. 헤더 영역
st.markdown("""
    <div class="hero-container">
        <div class="hero-box">
            <div class="hero-title">KIS 7인 투자 위원회 AI 대시보드</div>
            <div class="hero-sub">
                타이밍 전략가부터 찰리 멍거까지, 7인의 전문가가 독립 분석 후 종합 판단을 내립니다.<br>
                종목 티커를 입력하고 분석을 시작하세요.
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 5. 사용자 입력 및 실행 영역
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    target_ticker = st.text_input("분석할 티커 입력 (예: NVDA, AAPL, MSFT)", value="NVDA", max_chars=10)
    analyze_btn = st.button("🚀 위원회 분석 소집", type="primary", use_container_width=True)

# 6. AI 분석 로직
if analyze_btn and target_ticker:
    with st.spinner(f"'{target_ticker}' 데이터를 수집하고 7인 위원회가 분석 중입니다..."):
        
        # 데이터 수집
        stock_data = get_stock_data(target_ticker)
        
        if not stock_data:
            st.error("데이터를 불러오지 못했습니다. 티커명을 다시 확인해주세요.")
            st.stop()
            
        # 프롬프트 구성 (사용자 요청사항 완벽 반영)
        system_prompt = f"""
        당신은 7인 투자 위원회 + KIS 실행 에이전트입니다.
        아래 수집된 데이터를 바탕으로, 지시된 [분석 출력 (순서 고정)] 양식에 맞추어 정확하게 마크다운(Markdown) 리포트를 작성하세요.
        
        [수집된 데이터 (STEP 0)]
        {stock_data}
        
        [STEP 1 — 위원회 분석 기준]
        [1] 타이밍 전략가 (15%): RSI·MACD·이동평균·거래량 기반 진입 타이밍
        