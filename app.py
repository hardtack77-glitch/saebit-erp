import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 기본 설정
st.set_page_config(page_title="새빛 LED ERP", page_icon="💡", layout="wide")
st.title("(주)새빛 LED 맞춤형 ERP 시스템")
st.markdown("빛으로 세상과 소통하다 (주)새빛")

# 2. 구글 스프레드시트 연결 (Streamlit Secrets 설정을 자동으로 읽어옵니다)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("구글 시트 인증 설정 중 오류가 발생했습니다. Secrets 설정을 확인해주세요.")

# 데이터 불러오기 함수
def load_data(worksheet_name):
    try:
        return conn.read(worksheet=worksheet_name, ttl=0)
    except Exception:
        return pd.DataFrame()

orders_df = load_data("orders")
expenses_df = load_data("expenses")

# 사이드바 메뉴 구성
menu = st.sidebar.radio("메뉴 선택", ["대시보드 (정산)", "수주/매출 등록 및 관리", "매입/지출 등록 및 관리"])

# ----------------------------------------------------
# 메뉴 1: 대시보드 및 월별 손익 정산
# ----------------------------------------------------
if menu == "대시보드 (정산)":
    st.header("📊 월별 손익 및 프로젝트별 마진율 현황")
    
    if not orders_df.empty and not expenses_df.empty:
        orders_df["수주금액"] = pd.to_numeric(orders_df["수주금액"], errors='coerce').fillna(0)
        expenses_df["지출금액"] = pd.to_numeric(expenses_df["지출금액"], errors='coerce').fillna(0)
        
        total_sales = orders_df["수주금액"].sum()
        total_expenses = expenses_df["지출금액"].sum()
        net_profit = total_sales - total_expenses
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 수주(매출) 금액", f"{total_sales:,.0f} 원")
        col2.metric("총 매입(지출) 금액", f"{total_expenses:,.0f} 원")
        col3.metric("당기 순이익", f"{net_profit:,.0f} 원")
        
        st.subheader("📋 프로젝트별 원가 및 마진 분석")
        p_reports = []
        for _, order in orders_df.iterrows():
            p_code = order["프로젝트코드"]
            p_cost = expenses_df[expenses_df["프로젝트코드"] == p_code]["지출금액"].sum()
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
    else:
        st.info("등록된 데이터가 부족하여 대시보드를 표시할 수 없습니다.")

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
            
            submit = st.form_submit_button("등록하기")
            
            if submit:
                if p_code and client:
                    new_data = pd.DataFrame([{
                        "프로젝트코드": p_code, "발주처": client, "품목/사양": specs, 
                        "수주금액": price, "계약일": str(order_date), "진행상태": status, "수금여부": payment
                    }])
                    updated_df = pd.concat([orders_df, new_data], ignore_index=True)
                    conn.update(worksheet="orders", data=updated_df)
                    st.success("새로운 수주 건이 안전하게 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("프로젝트 코드와 발주처 명은 필수 입력 항목입니다.")

    st.subheader("📑 수주 관리 대장")
    st.dataframe(orders_df, use_container_width=True)

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
            
            p_codes = ["공통지출"]
            if not orders_df.empty:
                p_codes += orders_df["프로젝트코드"].dropna().tolist()
            p_match = col1.selectbox("연관 프로젝트 코드 (원가 계산용)", p_codes)
            
            submit = st.form_submit_button("등록하기")
            
            if submit:
                if detail and amount > 0:
                    new_expense = pd.DataFrame([{
                        "지출일자": str(exp_date), "구분": category, "상세내역": detail, 
                        "지출금액": amount, "프로젝트코드": p_match
                    }])
                    updated_df = pd.concat([expenses_df, new_expense], ignore_index=True)
                    conn.update(worksheet="expenses", data=updated_df)
                    st.success("지출 내역이 안전하게 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("상세 내역을 적고 지출 금액을 입력해주세요.")

    st.subheader("📑 지출/매입 관리 대장")
    st.dataframe(expenses_df, use_container_width=True)