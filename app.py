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

# 2. 페이지 설정
st.set_page_config(page_title="KIS 7인 투자 위원회 Pro", layout="wide")

# 3. 데이터 수집 엔진 (에러 방지 로직 강화)
def get_stock_info(ticker, is_kr):
    try:
        if is_kr:
            # 최근 영업일 7일 중 가장 최신 데이터 탐색
            for i in range(7):
                target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                df_p = stock.get_market_ohlcv(target_date, target_date, ticker)
                if not df_p.empty:
                    df_f = stock.get_market_fundamental(target_date, target_date, ticker)
                    df_c = stock.get_market_cap(target_date, target_date, ticker)
                    name = stock.get_market_ticker_name(ticker)
                    
                    price = int(df_p['종가'].iloc[0])
                    per = float(df_f['PER'].iloc[0]) if not df_f.empty else 0
                    pbr = float(df_f['PBR'].iloc[0]) if not df_f.empty else 0
                    div = float(df_f['DIV'].iloc[0]) if not df_f.empty else 0
                    cap = int(df_c['시가총액'].iloc[0]) if not df_c.empty else 0
                    
                    return {
                        "종목명": name, "티커": ticker, "현재가": f"{price:,}원",
                        "PER": f"{per}배", "PBR": f"{pbr}배", "ROE": f"{round(pbr/per*100, 2) if per > 0 else 'N/A'}%",
                        "부채비율": "재무제표 참조", "시가총액": f"{round(cap/1e12, 2)}조 원", "배당": f"{div}%",
                        "52주고": f"{int(price * 1.2):,}원(추정)", "52주저": f"{int(price * 0.8):,}원(추정)",
                        "기준일": target_date
                    }
            return None
        else:
            yf_s = yf.Ticker(ticker)
            info = yf_s.info
            return {
                "종목명": info.get('longName'), "티커": ticker, "현재가": f"${info.get('currentPrice')}",
                "PER": f"{info.get('trailingPE')}배", "PBR": f"{info.get('priceToBook')}배",
                "ROE": f"{round(info.get('returnOnEquity', 0)*100, 2)}%", "부채비율": f"{info.get('debtToEquity')}%",
                "시가총액": f"${round(info.get('marketCap', 0)/1e9, 2)}B",
                "52주고": f"${info.get('fiftyTwoWeekHigh')}", "52주저": f"${info.get('fiftyTwoWeekLow')}",
                "배당": f"{info.get('dividendYield', 0)*100}%",
                "기준일": datetime.now().strftime("%Y-%m-%d")
            }
    except: return None

# 4. 메인 화면
st.title("🏛️ KIS 7인 투자 위원회 전문 분석")

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
    with st.spinner("위원회 보고서 양식에 맞춰 작성 중..."):
        is_kr = "국내" in market_choice
        data = get_stock_info(ticker_val, is_kr)
        
        if data:
            # AI에게 예시 형식을 강력히 강제하는 프롬프트
            report_prompt = f"""
            당신은 7인 투자 위원회입니다. 아래 데이터를 바탕으로 **제공된 BlackBerry(BB) 보고서 양식과 토씨 하나 틀리지 말고 동일한 구조**로 작성하세요.
            
            [실시간 데이터]: {data}
            
            [출력 필수 양식]:
            # [종목명] ([티커]) 투자 분석 보고서
            **기준일:** {data['기준일']} | **데이터 신뢰도:** 상 (실시간 API 수집)
            ---
            ## 📌 결론 먼저
            [매수 승인 여부 + 핵심 근거 + 핵심 리스크를 3줄로 작성]
            ---
            ### 1. 데이터 요약
            | 종목 | 현재가 | 기준일 | 신뢰도 | (표 작성)
            | PER | PBR | ROE | 부채비율 | 시가총액 | 배당 | 52주고 | 52주저 | (표 작성)
            ---
            ### 2. 기술지표
            | 지표 | 값 | 해석 | (RSI, MACD, 20/60/120/200일선 표 작성)
            **추세방향:** / **고점대비위치:** / **과열여부:** ---
            ### 3. 지지/저항선
            | 1차지지 | 2차지지 | 장기방어선 | 1차저항 | 2차저항 | (표 작성)
            ---
            ### 4. 위원회 의견
            (7명 위원 각각의 점수와 3가지 포인트, '누구라면:' 코멘트 포함)
            ---
            ### 5. 최종 판단
            | 종합점수 | 매수승인 | 권장비중 | 핵심결론 | (표 작성)
            ---
            ### 6. 시나리오 & 손익비
            (시나리오 A/B/C 표 작성 및 진입/목표/손절가 표 작성)
            > 100만원 투자 시 시뮬레이션 포함
            ---
            ### 7. 다음 액션 제안 (KIS 연동)
            (① 전략 설계 ② 백테스트 ③ 신호 확인 ④ 풀파이프라인)
            """
            
            response = client.models.generate_content(model="gemini-2.5-flash", contents=report_prompt)
            st.markdown(response.text)
        else:
            st.error("데이터 수집에 실패했습니다. 장 마감 후이거나 종목코드가 잘못되었을 수 있습니다.")
