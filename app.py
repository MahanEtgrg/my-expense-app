import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import bcrypt
import os

DB_NAME = "expenses.db"

# -------------------- Database Setup --------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            amount INTEGER NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))
    return False

def load_data(username):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT date, title, amount, category FROM expenses WHERE username = ?", conn, params=(username,))
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=['date', 'title', 'amount', 'category'])
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df

def save_data(df, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE username = ?", (username,))
    for _, row in df.iterrows():
        c.execute('''
            INSERT INTO expenses (username, date, title, amount, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, row['date'], row['title'], row['amount'], row['category']))
    conn.commit()
    conn.close()

init_db()

# -------------------- Session State --------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# -------------------- Login/Register --------------------
st.set_page_config(page_title="مدیریت هزینه", layout="wide")
st.markdown("""
    <style>
    body, .stApp, .stSidebar, .stButton, .stTextInput, .stSelectbox, .stNumberInput, .stDateInput, .stDataFrame, .stMetric {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Tahoma', 'Arial', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💰 مدیریت هزینه‌های شخصی")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    
    with tab1:
        st.subheader("ورود به حساب کاربری")
        login_user = st.text_input("نام کاربری", key="login_user")
        login_pass = st.text_input("رمز عبور", type="password", key="login_pass")
        if st.button("ورود"):
            if check_user(login_user, login_pass):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success("✅ ورود موفق!")
                st.rerun()
            else:
                st.error("❌ نام کاربری یا رمز عبور اشتباه است.")
    
    with tab2:
        st.subheader("ایجاد حساب کاربری جدید")
        reg_user = st.text_input("نام کاربری جدید", key="reg_user")
        reg_pass = st.text_input("رمز عبور جدید", type="password", key="reg_pass")
        if st.button("ثبت‌نام"):
            if reg_user and reg_pass:
                if add_user(reg_user, reg_pass):
                    st.success("✅ حساب کاربری ساخته شد! لطفاً وارد شوید.")
                else:
                    st.error("❌ این نام کاربری قبلاً ثبت شده است.")
            else:
                st.error("لطفاً همه‌ی فیلدها را پر کنید.")
    
    st.info("👈 لطفاً برای ادامه وارد شوید یا ثبت‌نام کنید.")
    st.stop()

# -------------------- Main App --------------------
if st.session_state.logged_in:
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    st.sidebar.header("🎨 تم")
    dark_mode = st.sidebar.toggle("🌙 حالت شب", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()

    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            .stApp { background-color: #0E1117; color: #FAFAFA; }
            .stSidebar { background-color: #1E1E2E; }
            h1, h2, h3, h4, h5, h6, p, div, span, label { color: #FAFAFA !important; }
            .stButton button { background-color: #2D2D44 !important; color: #FAFAFA !important; border-radius: 8px; }
            .stMetric { background-color: #1E1E2E !important; border-radius: 10px; padding: 10px; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp { background-color: #FFFFFF; }
            .stSidebar { background-color: #F0F2F6; }
            h1, h2, h3, h4, h5, h6, p, div, span, label { color: #000000 !important; }
            .stButton button { background-color: #4CAF50 !important; color: white !important; border-radius: 8px; }
            .stMetric { background-color: #F0F2F6 !important; border-radius: 10px; padding: 10px; }
            </style>
        """, unsafe_allow_html=True)

    st.title(f"💰 خوش آمدید {st.session_state.username}!")
    st.write("هزینه‌های روزانه‌ی خود را مدیریت کنید.")

    if 'df' not in st.session_state:
        st.session_state.df = load_data(st.session_state.username)

    # Filters
    st.sidebar.header("🔍 فیلترها")
    categories = ["همه"] + sorted(st.session_state.df['category'].unique().tolist())
    selected_category = st.sidebar.selectbox("فیلتر بر اساس دسته‌بندی", categories)

    if not st.session_state.df.empty:
        min_date = st.session_state.df['date'].min()
        max_date = st.session_state.df['date'].max()
        date_range = st.sidebar.date_input("بازه‌ی زمانی", value=(min_date, max_date))
    else:
        date_range = (datetime.now().date(), datetime.now().date())

    filtered_df = st.session_state.df.copy()
    if selected_category != "همه":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

    if not filtered_df.empty and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]

    # Add Expense
    st.subheader("➕ ثبت هزینه جدید")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            expense_date = st.date_input("تاریخ", datetime.now().date())
        with col2:
            title = st.text_input("عنوان")
        with col3:
            amount = st.number_input("مبلغ (تومان)", min_value=0, step=1000)
        with col4:
            category = st.selectbox("دسته‌بندی", ["غذا", "حمل و نقل", "خرید", "تفریح", "قبوض", "سایر"])
        submitted = st.form_submit_button("➕ ثبت هزینه")

    if submitted:
        if title and amount > 0:
            category_map = {"غذا": "Food", "حمل و نقل": "Transport", "خرید": "Shopping", "تفریح": "Entertainment", "قبوض": "Bills", "سایر": "Other"}
            new_row = pd.DataFrame([[expense_date, title, amount, category_map[category]]], columns=['date', 'title', 'amount', 'category'])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data(st.session_state.df, st.session_state.username)
            st.success(f"✅ {title} با موفقیت ثبت شد!")
            st.rerun()
        else:
            st.error("لطفاً عنوان و مبلغ را وارد کنید.")

    # Display Data
    st.subheader("📊 لیست هزینه‌ها")
    if filtered_df.empty:
        st.info("هیچ هزینه‌ای یافت نشد.")
    else:
        category_map_reverse = {"Food": "غذا", "Transport": "حمل و نقل", "Shopping": "خرید", "Entertainment": "تفریح", "Bills": "قبوض", "Other": "سایر"}
        display_df = filtered_df.copy()
        display_df['category'] = display_df['category'].map(category_map_reverse)
        display_df = display_df.reset_index(drop=True)
        
        st.dataframe(display_df, use_container_width=True)

        total = filtered_df['amount'].sum()
        avg = filtered_df['amount'].mean()
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 مجموع کل", f"{total:,} تومان")
        col2.metric("📊 میانگین", f"{avg:,.0f} تومان")
        col3.metric("🧾 تعداد", len(filtered_df))

        # Charts
        st.subheader("📈 نمودارها")
        if not filtered_df.empty:
            pie_df = filtered_df.copy()
            pie_df['category'] = pie_df['category'].map(category_map_reverse)
            fig_pie = px.pie(pie_df, values='amount', names='category', title='توزیع هزینه‌ها بر اساس دسته')
            st.plotly_chart(fig_pie, use_container_width=True)

            daily_trend = filtered_df.groupby('date')['amount'].sum().reset_index()
            fig_line = px.line(daily_trend, x='date', y='amount', title='روند هزینه‌های روزانه', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

            cat_sum = filtered_df.groupby('category')['amount'].sum().reset_index()
            cat_sum['category'] = cat_sum['category'].map(category_map_reverse)
            fig_bar = px.bar(cat_sum, x='category', y='amount', title='مجموع هزینه‌ها بر اساس دسته', color='category')
            st.plotly_chart(fig_bar, use_container_width=True)

    # Logout
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.success("🚀 همه‌ی امکانات به‌خوبی کار می‌کنند!")



#rebuild
