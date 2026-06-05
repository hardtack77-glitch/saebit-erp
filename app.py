import streamlit as st
import pandas as pd
import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="새빛 LED ERP", page_icon="💡", layout="wide")
st.title("💡 새빛 LED 맞춤형 ERP 시스템")
st.markdown("대구 대명동 소규모 주문제작형 제조업 전용 (재고 없는 모델)")

# 2. 가상의 데이터베이스 초기화 (실제 운영 시 파일이나 DB 연동 필요)
if 'orders' not in st.session_state:
    st.session_state.orders = pd.DataFrame([
        {"프로젝트코드": "P-260601", "발주처": "(주)대구건설", "품목/사양": "옥외 전광판 5m", "수주금액": 5000000, "계약일": datetime.date(2026, 6, 1), "진행상태": "제작중", "수금여부": "미수금"},
        {"프로젝트코드": "P-260602", "발주처": "대명상가", "품목/사양": "실내 LED 간판", "수주금액": 1200000, "계약일": datetime.date(2026, 6, 2), "진행상태": "납품완료", "수금여부": "완납"}
    ])

if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame([
        {"지출일자": datetime.date(2026, 6, 3), "구분": "부품구입", "상세내역": "LED 모듈 및 SMPS", "지출금액": 1500000, "프로젝트코드": "P-260601"},
        {"지출일자": datetime.date(2026, 6, 4), "구분": "인건비", "상세내역": "외주 설치 기사 일당", "지출금액": 300000, "프로젝트코드": "P-260601"},
        {"지출일자": datetime.date(2026, 6, 5), "구분": "운영비", "상세내역": "6월 사무실 임대료", "지출금액": 800000, "프로젝트코드": "공통지출"}
    ])

# 사이드바 메뉴 구성
menu = st.sidebar.radio("메뉴 선택", ["대시보드 (정산)", "수주/매출 등록 및 관리", "매입/지출 등록 및 관리"])

# ----------------------------------------------------
# 메뉴 1: 대시보드 및 월별 손익 정산
# ----------------------------------------------------
if menu == "대시보드 (정산)":
    st.header("📊 월별 손익 및 프로젝트별 마진율 현황")
    
    total_sales = st.session_state.orders["수주금액"].sum()
    total_expenses = st.session_state.expenses["지출금액"].sum()
    net_profit = total_sales - total_expenses
    
    col1, col2, col3 = st.columns(3)
    col1.metric("총 수주(매출) 금액", f"{total_sales:,.0f} 원")
    col2.metric("총 매입(지출) 금액", f"{total_expenses:,.0f} 원")
    col3.metric("당기 순이익", f"{net_profit:,.0f} 원")
    
    st.subheader("📋 프로젝트별 원가 및 마진 분석")
    p_reports = []
    for _, order in st.session_state.orders.iterrows():
        p_code = order["프로젝트코드"]
        p_cost = st.session_state.expenses[st.session_state.expenses["프로젝트코드"] == p_code]["지출금액"].sum()
        p_margin = order["수주금액"] - p_cost
        margin_rate = (p_margin / order["수주금액"]) * 100 if order["수주금액"] > 0 else 0
        
        p_reports.append({
            "프로젝트코드": p_code,
            "발주처": order["발주처"],
            "수주금액": order["수주금액"],
            "투입원가(부품+인건)": p_cost,
            "남은 마진": p_margin,
            "마진율(%)": f"{margin_rate:.1f}%"
        })
    st.dataframe(pd.DataFrame(p_reports), use_container_width=True)

# ----------------------------------------------------
# 메뉴 2: 수주/매출 등록 및 관리
# ----------------------------------------------------
elif menu == "수주/매출 등록 및 관리":
    st.header("📦 수주 등록 및 진행 상황")
    
    with st.expander("➕ 신규 수주(발주) 등록하기"):
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            p_code = col1.text_input("프로젝트 코드 (예: P-260603)")
            client = col2.text_input("발주처 명")
            specs = col1.text_input("품목 및 사양")
            price = col2.number_input("수주 금액 (원)", min_value=0, step=10000)
            order_date = col1.date_input("계약일")
            status = col2.selectbox("진행 상태", ["대기", "제작중", "납품완료", "A/S중"])
            payment = col1.selectbox("수금 여부", ["미수금", "일부수금", "완납"])
            
            # 수정된 부분! st.form_submit_button 으로 변경
            submit = st.form_submit_button("등록하기")
            
            if submit:
                new_data = {"프로젝트코드": p_code, "발주처": client, "품목/사양": specs, "수주금액": price, "계약일": order_date, "진행상태": status, "수금여부": payment}
                st.session_state.orders = pd.concat([st.session_state.orders, pd.DataFrame([new_data])], ignore_index=True)
                st.success("새로운 수주 건이 등록되었습니다!")

    st.subheader("📑 수주 관리 대장")
    st.dataframe(st.session_state.orders, use_container_width=True)

# ----------------------------------------------------
# 메뉴 3: 매입/지출 등록 및 관리
# ----------------------------------------------------
elif menu == "매입/지출 등록 및 관리":
    st.header("💸 부품 매입 및 운영 지출 관리")
    
    with st.expander("➕ 신규 지출 내역 등록하기"):
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            exp_date = col1.date_input("지출 일자")
            category = col2.selectbox("지출 구분", ["부품구입", "인건비", "운영비(임대료/세금/기타)"])
            detail = col1.text_input("상세 지출 내역")
            amount = col2.number_input("지출 금액 (원)", min_value=0, step=1000)
            
            p_codes = ["공통지출"] + st.session_state.orders["프로젝트코드"].tolist()
            p_match = col1.selectbox("연관 프로젝트 코드 (원가 계산용)", p_codes)
            
            # 수정된 부분! st.form_submit_button 으로 변경
            submit = st.form_submit_button("등록하기")
            
            if submit:
                new_expense = {"지출일자": exp_date, "구분": category, "상세내역": detail, "지출금액": amount, "프로젝트코드": p_match}
                st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_expense])], ignore_index=True)
                st.success("지출 내역이 성공적으로 기록되었습니다!")

    st.subheader("📑 지출/매입 관리 대장")
    st.dataframe(st.session_state.expenses, use_container_width=True)