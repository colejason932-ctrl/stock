import os
import streamlit as st
import yfinance as yf
from google import genai
from datetime import datetime

# 1. 환경 설정
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# 2. UI 및 스타일 설정
st.set_page_config(page_title="KIS 7인 투자 위원회 PRO", layout="wide")
st.markdown("""
    <style>
    .stMarkdown { font-size: 1.05rem !important; line-height: 1.6; }
    .report-card { background: white; padding: 2rem; border-radius: 15px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# 3. 데이터 수집 (지표 보강)
@st.cache_data(ttl=600)
def get_detailed_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = ticker.history(period="1y") # 1년치 데이터로 추세 확인용
        
        data = {
            "종목명": info.get('longName', ticker_symbol),
            "현재가": info.get('currentPrice', info.get('regularMarketPrice')),
            "PER": info.get('trailingPE'),
            "PBR": info.get('priceToBook'),
            "ROE": info.get('returnOnEquity'),
            "EPS": info.get('trailingEps'),
            "부채비율": info.get('debtToEquity'),
            "시가총액": info.get('marketCap'),
            "배당수익률": info.get('dividendYield'),
            "52주고": info.get('fiftyTwoWeekHigh'),
            "52주저": info.get('fiftyTwoWeekLow'),
            "거래량": info.get('volume'),
            "FCF": info.get('freeCashflow'),
            "기준일": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return data
    except:
        return None

# 4. 헤더 및 입력
st.title("🏛️ KIS 7인 투자 위원회 전문 분석 시스템")
st.info("야후 파이낸스 실시간 데이터와 Gemini 2.5 Pro급 추론 엔진을 사용하여 심층 보고서를 생성합니다.")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    market = st.selectbox("시장", ["미국 주식", "한국 KOSPI", "한국 KOSDAQ"])
with col2:
    raw_input = st.text_input("티커/코드", value="000660" if "한국" in market else "NVDA")

ticker = raw_input.strip().upper()
if "KOSPI" in market: ticker += ".KS"
elif "KOSDAQ" in market: ticker += ".KQ"

if st.button("🚀 위원회 소집 및 심층 분석 시작", type="primary", use_container_width=True):
    with st.spinner("전문가들이 데이터를 검토 중입니다..."):
        stock_info = get_detailed_data(ticker)
        
        if not stock_info or not stock_info['현재가']:
            st.error("데이터를 수집할 수 없습니다.")
            st.stop()

        # [핵심] 전문성을 강제하는 고도화된 프롬프트
        expert_prompt = f"""
당신은 월스트리트 출신의 **7인 투자 위원회**입니다. 
제공된 데이터({stock_info})를 바탕으로 기관 투자자 수준의 **심층 보고서**를 작성하십시오. 

**[작성 가이드라인]**
1. **데이터 기반 추론**: 수치가 'N/A'인 경우, 업종 평균이나 현재가 추세를 바탕으로 논리적인 추정치를 제시하고 그 근거를 밝히십시오.
2. **페르소나 강화**: 각 위원은 최소 3~5문장의 심도 있는 분석을 제공해야 합니다. 단답형은 금지합니다.
3. **기술적 분석**: 52주 고저 대비 현재가 위치를 계산하여(Fibonacci Retinement 등 활용) 지지/저항을 정교하게 도출하십시오.
4. **결론의 일관성**: 7인의 점수를 가중치에 따라 합산하여 최종 종합 점수를 산출하십시오.

---

### 📌 결론 먼저 (3줄)
- **승인 여부**: [적극매수/매수/관망/매도]
- **핵심 근거**: 해당 종목의 현재 가장 강력한 업사이드 모멘텀
- **핵심 리스크**: 투자자가 반드시 체크해야 할 하방 리스크

---

### 1. 데이터 요약 및 지표 분석
(종목명, 현재가, PER, ROE, 시가총액 등을 포함한 상세 표 작성)

---

### 2. 기술적 지표 및 가격 전략
| 항목 | 값 | 심층 해석 |
|------|----|----------|
| RSI(추정) | | 현재 가격 위치 기반 과매수/과매도 분석 |
| 가격 모멘텀 | | 52주 고점 대비 괴리율 및 추세 강도 |
| 지지선/저항선 | | 1, 2차 구간 및 손절 라인 |

---

### 3. 위원회 개별 심층 의견

**[1] 타이밍 전략가 (15%) — 점수: /100**
(거래량 패턴과 현재 가격의 이격도를 바탕으로 최적의 진입 시점 분석)

**[2] 장기 매집가 (15%) — 점수: /100**
(업황의 사이클과 장기 이평선 기준의 매집 매력도 분석)

**[3] 리스크 감시관 (10%) — 점수: /100**
(거시경제 영향, 지정학적 리스크, 섹터 내 경쟁 심화 분석)

**[4] 주도주 탐색가 (10%) — 점수: /100**
(섹터 내 시가총액 순위와 기술적 리더십 분석)

**[5] 워렌 버핏 (20%) — 점수: /100**
(경제적 해자, ROE의 질, 자본 배치 효율성 분석)
*버핏이라면:* "나는 이 기업이 10년 후에도..." (단기 용어 절대 금지)

**[6] 피터 린치 (15%) — 점수: /100**
(성장률 대비 PER 평가(PEG), 이익성장 스토리 분석)
*린치라면:* "이 주식은 OO유형에 속하며, 향후..."

**[7] 찰리 멍거 (15%) — 점수: /100**
(다학제적 모델 기반 리스크, 경영진의 도덕성, 인버트 사고)
*멍거라면:* "이 투자가 실패한다면 그 이유는..."

---

### 4. 종합 판단 및 시뮬레이션
- **종합 점수**: [산출된 점수]/100
- **권장 비중**: [포트폴리오 내 %]
- **수익/손실 시뮬레이션**: 100만원 투자 시 기대 수익과 최대 예상 손실(MDD)

---

### 5. KIS 실행 가이드
(kis-strategy-builder 및 kis-order-executor와 연동하기 위한 다음 액션 제안)
"""

        # API 호출
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=expert_prompt
        )
        
        # 결과 대시보드 출력
        st.markdown(response.text)
        
        st.divider()
        st.caption("본 보고서는 전문 투자 에이전트 시스템에 의해 자동 생성되었습니다. 투자 판단의 책임은 본인에게 있습니다.")
