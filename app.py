import os
import streamlit as st
import yfinance as yf
from google import genai
from datetime import datetime

# 1. 환경 설정 및 API 연결
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

# 2. 페이지 설정
st.set_page_config(page_title="KIS 7인 투자 위원회", layout="wide", page_icon="📈")

# 3. 데이터 수집 함수 (실시간성 강화)
@st.cache_data(ttl=600) # 10분 캐싱
def get_stock_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 기본 정보 추출
        data = {
            "종목명": info.get('longName', ticker_symbol),
            "현재가": info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
            "PER": info.get('trailingPE', 'N/A'),
            "PBR": info.get('priceToBook', 'N/A'),
            "ROE": info.get('returnOnEquity', 'N/A'),
            "부채비율": info.get('debtToEquity', 'N/A'),
            "시가총액": info.get('marketCap', 'N/A'),
            "배당수익률": info.get('dividendYield', 'N/A'),
            "52주고": info.get('fiftyTwoWeekHigh', 'N/A'),
            "52주저": info.get('fiftyTwoWeekLow', 'N/A'),
            "기준일": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return data
    except:
        return None

# 4. 메인 화면 구성
st.title("📈 KIS 7인 투자 위원회")
st.caption("실시간 야후 파이낸스 데이터를 기반으로 7인의 전문가가 분석합니다.")

col1, col2 = st.columns([1, 3])

with col1:
    market = st.radio("시장 선택", ["미국", "한국(KOSPI)", "한국(KOSDAQ)"])
    ticker_input = st.text_input("티커/종목코드", value="NVDA")
    
    ticker_final = ticker_input.strip().upper()
    if market == "한국(KOSPI)": ticker_final += ".KS"
    elif market == "한국(KOSDAQ)": ticker_final += ".KQ"
    
    analyze_btn = st.button("전문가 위원회 소집", type="primary")

if analyze_btn:
    with st.spinner("위원회 소집 중..."):
        stock_info = get_stock_data(ticker_final)
        
        if not stock_info or stock_info['현재가'] == 'N/A':
            st.error("데이터 수집 실패. 티커를 확인하세요.")
            st.stop()

        # 실시간 데이터 요약 출력 (사용자 확인용)
        st.sidebar.write("### 실시간 수집 데이터")
        st.sidebar.json(stock_info)

        # AI 프롬프트 (데이터 주입 방식 강화)
        prompt = f"""
당신은 **7인 투자 위원회**입니다. 반드시 아래 제공된 **[실시간 데이터]**만을 바탕으로 분석하십시오. 
절대 과거의 지식이나 추측으로 현재가, 시가총액, PER 등을 말하지 마십시오. 사실에 근거하지 않은 수치는 엄격히 금지합니다.

**[실시간 데이터]**
- 종목: {stock_info['종목명']} ({ticker_final})
- 현재가: {stock_info['현재가']}
- 기준일: {stock_info['기준일']}
- PER: {stock_info['PER']} / PBR: {stock_info['PBR']} / ROE: {stock_info['ROE']}
- 시가총액: {stock_info['시가총액']}
- 52주 최고/최저: {stock_info['52주고']} / {stock_info['52주저']}
- 배당수익률: {stock_info['배당수익률']}

---

**[출력 요구사항 - 반드시 이 순서와 마크다운 형식을 지킬 것]**

### 📌 결론 먼저 (3줄)
[매수 승인 여부 + 핵심 근거 + 핵심 리스크]

---
### 1. 데이터 요약
| 종목 | 현재가 | 기준일 | 신뢰도 |
|------|--------|--------|--------|
| {stock_info['종목명']} | {stock_info['현재가']} | {stock_info['기준일']} | 상 (실시간 API) |

| PER | PBR | ROE | 시가총액 | 52주고 | 52주저 |
|-----|-----|-----|---------|-------|-------|
| {stock_info['PER']} | {stock_info['PBR']} | {stock_info['ROE']} | {stock_info['시가총액']} | {stock_info['52주고']} | {stock_info['52주저']} |

---
### 2. 위원회 개별 의견
- **[1] 타이밍 전략가 (15%)**: 현재가와 52주 고저를 비교하여 진입 시점 판별.
- **[2] 장기 매집가 (15%)**: 장기적 추세 판별.
- **[3] 리스크 감시관 (10%)**: 거시적 위험 요소.
- **[4] 주도주 탐색가 (10%)**: 현재 섹터 내 위치.
- **[5] 워렌 버핏 (20%)**: 경제적 해자와 안전마진 분석. (버핏이라면: __ 필수 포함)
- **[6] 피터 린치 (15%)**: 성장주 유형 분류 및 PEG 분석. (린치라면: __ 필수 포함)
- **[7] 찰리 멍거 (15%)**: 역발상 리스크와 기회비용. (멍거라면: __ 필수 포함)

---
### 3. 최종 판단 및 시나리오
- **종합점수**: __/100 (가중치 합산)
- **매수승인**: (승인/조건부/보류/불승인)
- **권장비중**: __%
- **손익비 시나리오**: 목표가 및 손절가 제시

---
### 4. 다음 액션 제안
① 전략 설계  ② 백테스트  ③ 신호 확인  ④ 풀파이프라인
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        st.markdown(response.text)
        st.divider()
        st.caption("※ 본 분석은 실시간 수집 데이터를 바탕으로 AI가 생성한 시나리오입니다.")