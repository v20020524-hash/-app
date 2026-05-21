import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# =========================
# 頁面設定
# =========================
st.set_page_config(
    page_title="AI 記帳 App",
    page_icon="💰",
    layout="wide"
)

# =========================
# CSS 美化
# =========================
st.markdown("""
<style>
.big-font {
    font-size:28px !important;
    font-weight:bold;
}

.metric-card {
    background-color:#1e1e1e;
    padding:20px;
    border-radius:15px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 資料庫
# =========================
conn = sqlite3.connect("money.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    type TEXT,
    category TEXT,
    amount REAL,
    note TEXT
)
""")

conn.commit()

# =========================
# 標題
# =========================
st.markdown('<p class="big-font">💰 AI 智慧記帳 App</p>', unsafe_allow_html=True)

st.caption("永久記憶 + 圖表分析 + 手機可用")

# =========================
# 側邊欄
# =========================
menu = st.sidebar.radio(
    "功能選單",
    [
        "新增記帳",
        "查看資料",
        "統計分析",
        "搜尋資料"
    ]
)

# =========================
# 新增記帳
# =========================
if menu == "新增記帳":

    st.header("新增收入 / 支出")

    with st.form("add_form"):

        date = st.date_input(
            "日期",
            datetime.today()
        )

        record_type = st.selectbox(
            "類型",
            ["支出", "收入"]
        )

        category = st.selectbox(
            "類別",
            [
                "餐飲",
                "交通",
                "投資",
                "娛樂",
                "薪水",
                "購物",
                "學習",
                "醫療",
                "其他"
            ]
        )

        amount = st.number_input(
            "金額",
            min_value=0.0,
            step=1.0
        )

        note = st.text_input("備註")

        submit = st.form_submit_button("新增")

        if submit:

            c.execute("""
            INSERT INTO records
            (date, type, category, amount, note)
            VALUES (?, ?, ?, ?, ?)
            """, (
                str(date),
                record_type,
                category,
                amount,
                note
            ))

            conn.commit()

            st.success("新增成功！")

# =========================
# 查看資料
# =========================
elif menu == "查看資料":

    st.header("所有資料")

    df = pd.read_sql_query(
        "SELECT * FROM records ORDER BY date DESC",
        conn
    )

    if len(df) == 0:

        st.warning("目前沒有資料")

    else:

        st.dataframe(
            df,
            use_container_width=True
        )

        # 匯出 CSV
        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="下載 CSV",
            data=csv,
            file_name="記帳資料.csv",
            mime="text/csv"
        )

        # 刪除
        st.subheader("刪除資料")

        delete_id = st.number_input(
            "輸入 ID",
            min_value=1,
            step=1
        )

        if st.button("刪除"):

            c.execute(
                "DELETE FROM records WHERE id=?",
                (delete_id,)
            )

            conn.commit()

            st.success("刪除成功")

            st.rerun()

# =========================
# 統計分析
# =========================
elif menu == "統計分析":

    st.header("統計分析")

    df = pd.read_sql_query(
        "SELECT * FROM records",
        conn
    )

    if len(df) == 0:

        st.warning("沒有資料")

    else:

        expense_df = df[df["type"] == "支出"]
        income_df = df[df["type"] == "收入"]

        total_expense = expense_df["amount"].sum()
        total_income = income_df["amount"].sum()

        balance = total_income - total_expense

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "總收入",
            f"${total_income:,.0f}"
        )

        col2.metric(
            "總支出",
            f"${total_expense:,.0f}"
        )

        col3.metric(
            "剩餘",
            f"${balance:,.0f}"
        )

        # =========================
        # 支出分類圖
        # =========================
        st.subheader("支出分類")

        category_sum = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        if len(category_sum) > 0:

            fig = px.pie(
                category_sum,
                names="category",
                values="amount",
                title="支出比例"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            bar_fig = px.bar(
                category_sum,
                x="category",
                y="amount",
                title="支出金額"
            )

            st.plotly_chart(
                bar_fig,
                use_container_width=True
            )

        # =========================
        # 每月統計
        # =========================
        st.subheader("每月支出")

        expense_df["month"] = pd.to_datetime(
            expense_df["date"]
        ).dt.strftime("%Y-%m")

        monthly = (
            expense_df
            .groupby("month")["amount"]
            .sum()
            .reset_index()
        )

        if len(monthly) > 0:

            line_fig = px.line(
                monthly,
                x="month",
                y="amount",
                markers=True,
                title="每月支出變化"
            )

            st.plotly_chart(
                line_fig,
                use_container_width=True
            )

# =========================
# 搜尋資料
# =========================
elif menu == "搜尋資料":

    st.header("搜尋")

    keyword = st.text_input("輸入關鍵字")

    df = pd.read_sql_query(
        "SELECT * FROM records",
        conn
    )

    if keyword:

        result = df[
            df["note"].astype(str).str.contains(
                keyword,
                case=False
            )
            |
            df["category"].astype(str).str.contains(
                keyword,
                case=False
            )
        ]

        st.write(f"找到 {len(result)} 筆資料")

        st.dataframe(
            result,
            use_container_width=True
        )