import streamlit as st
st.set_page_config(page_title="인테리어 견적 앱", layout="wide")

import pandas as pd
from io import BytesIO

# 세션 상태 초기화
if "estimate_table" not in st.session_state:
    st.session_state.estimate_table = []

# 자재 데이터 로드 함수
@st.cache_data(ttl=0)
def load_materials():
    try:
        return pd.read_csv("materials.csv")
    except:
        return pd.DataFrame(columns=["공정", "항목명", "단위", "단가(원)"])

df = load_materials()

st.title("🏗️ 인테리어 견적 자동화")

# 1️⃣ 자재 입력
with st.container():
    st.subheader("🧱 자재 입력")
    with st.form("input_form", clear_on_submit=True):
        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 2, 1.5, 1.5, 2, 1])
        with c1:
            margin = st.number_input("마진율(%)", min_value=0.0, step=1.0, value=10.0)
            if margin > 100:
                st.info("ℹ️ 고마진율 설정이 적용되었습니다. 단가에 직접 반영됩니다.")
        with c2:
            selected_process = st.selectbox("공정", df["공정"].unique())
            filtered = df[df["공정"] == selected_process]
        with c3:
            selected_item = st.selectbox("항목", filtered["항목명"].values)
        item = filtered[filtered["항목명"] == selected_item].iloc[0]
        unit = item["단위"]
        base_price = item["단가(원)"]
        unit_price = base_price * (1 + margin / 100)
        with c4:
            quantity = st.number_input(f"수량 ({unit})", min_value=0.0, value=1.0, step=1.0)
        with c5:
            note = st.text_input("비고")
        with c6:
            submitted = st.form_submit_button("➕ 추가")
            if submitted:
                total_price = quantity * unit_price
                st.session_state.estimate_table.append({
                    "공정": selected_process,
                    "항목명": selected_item,
                    "단위": unit,
                    "수량": float(quantity),
                    "단가(원)": round(unit_price),
                    "금액(원)": round(total_price),
                    "비고": note
                })
                st.success("✅ 항목이 추가되었습니다.")

# 2️⃣ 견적 목록
if st.session_state.estimate_table:
    st.subheader("📋 견적 목록")

    for i, row in enumerate(st.session_state.estimate_table):
        with st.container():
            st.markdown("""
                <div style='background-color:#f9f9f9; padding:10px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px;'>
            """, unsafe_allow_html=True)
            cols = st.columns([2, 2, 1, 1, 2, 2, 2, 1])
            cols[0].markdown(f"**공정**: {row['공정']}")
            cols[1].markdown(f"**항목**: {row['항목명']}")
            cols[2].markdown(f"**단위**: {row['단위']}")
            cols[3].markdown(f"**수량**: {row['수량']}")
            cols[4].markdown(f"**단가**: {row['단가(원)']:,} 원")
            cols[5].markdown(f"**금액**: {row['금액(원)']:,} 원")
            cols[6].markdown(f"**비고**: {row['비고']}")
            if cols[7].button("🗑️", key=f"delete_{i}"):
                st.session_state.estimate_table.pop(i)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# 3️⃣ 견적 요약 + 합계
if st.session_state.estimate_table:
    df_est = pd.DataFrame(st.session_state.estimate_table)

    st.subheader("📊 견적 요약")
    summary = df_est[["항목명", "수량", "단가(원)", "금액(원)"]]
    st.dataframe(summary, use_container_width=True)

    st.subheader("💰 견적 합계")
    subtotal = df_est["금액(원)"].sum()
    vat = subtotal * 0.1
    total = subtotal + vat

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("공급가액", f"{subtotal:,.0f} 원")
    with colB:
        st.metric("부가세 (10%)", f"{vat:,.0f} 원")
    with colC:
        st.metric("총합계", f"{total:,.0f} 원")

    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        label="💾 엑셀로 저장",
        data=to_excel_bytes(df_est),
        file_name="견적서.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 4️⃣ 자재 등록
st.markdown("---")
st.subheader("🛠️ 자재 단가 지금 추가")

with st.form("add_material_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_process = st.text_input("공정 입력")
    with col2:
        new_item = st.text_input("자재 항목명")
    with col3:
        new_unit = st.text_input("단위 (예: ㎡, 개 등)")
    with col4:
        new_price = st.number_input("단가 (원)", min_value=0)

    submitted_material = st.form_submit_button("📥 자재 추가")
    if submitted_material:
        if new_process and new_item and new_unit and new_price > 0:
            try:
                df_material = pd.read_csv("materials.csv")
            except:
                df_material = pd.DataFrame(columns=["공정", "항목명", "단위", "단가(원)"])

            new_row = pd.DataFrame([{
                "공정": new_process,
                "항목명": new_item,
                "단위": new_unit,
                "단가(원)": new_price
            }])

            df_material = pd.concat([df_material, new_row], ignore_index=True)
            df_material.to_csv("materials.csv", index=False)

            st.cache_data.clear()
            st.success("✅ 자재가 추가되었습니다. 위 입력창에서 즉시 사용할 수 있습니다.")
        else:
            st.warning("⚠️ 모든 항목을 정확히 입력해주세요.")