import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="HK 2026", page_icon="🇭🇰", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Anuphan:wght@200;300;400&family=Montserrat:wght@200;300;400&display=swap');
    
    html, body, [class*="css"], .stMarkdown { 
        font-family: 'Anuphan', 'Montserrat', sans-serif !important; 
        font-weight: 300 !important;
        color: #444;
    }

    summary > span > div > div { font-size: 0 !important; visibility: hidden !important; }
    summary > span > div > div > p { font-size: 16px !important; visibility: visible !important; font-family: 'Anuphan' !important; }
    svg[data-testid="stExpanderIcon"] { display: none !important; }

    h1 { font-weight: 300 !important; letter-spacing: 2px; text-align: center; text-transform: uppercase; margin-bottom: 2rem; }
    .stButton>button { border-radius: 12px; border: 0.5px solid #eee; background-color: #ffffff; transition: 0.3s; }
    div[data-baseweb="input"] { border-radius: 8px; border: 0.5px solid #f0f0f0; }

    [data-testid="stMetricValue"] { font-weight: 200 !important; font-size: 1.8rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; }
    
    div[data-testid="stExpander"] { border: 1px solid #f9f9f9 !important; border-radius: 12px !important; margin-bottom: 10px; }
    
    .mobile-flex-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        width: 100%;
        margin-top: 15px;
    }
    .flex-item-box {
        flex: 1;
        text-align: center;
        min-width: 0;
    }
    .member-label { 
        font-size: 11px; 
        font-weight: 400; 
        color: #222; 
        margin-bottom: 5px; 
        border-bottom: 0.5px solid #eee; 
        display: inline-block; 
        padding: 0 5px 1px 5px; 
        white-space: nowrap;
    }
    .item-text-centered { 
        font-size: 10px; 
        color: #999; 
        line-height: 1.4; 
        overflow-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# --- Connection ---
# ใช้ ID ใหม่ที่คุณระบุมา
SHEET_URL = "https://docs.google.com/spreadsheets/d/1NUePBMl8q6qr72KaVpP4PQwcdQkw1zayjixQlcl_Djc/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("HK TRIP 2026")
# ปรับเหลือ 2 Tabs
tab1, tab2 = st.tabs(["💰 EXPENSE", "📊 SUMMARY"])
members = ["KK", "Charlie"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_HKD'] = pd.to_numeric(df['Amount_HKD'], errors='coerce').fillna(0)
    if 'Note' not in df.columns: df['Note'] = ""
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_HKD", "Payer", "Participants", "Category", "Note", "Is_Settled"])

# --- TAB 1: EXPENSE ---
with tab1:
    with st.expander("ADD NEW", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item", placeholder="e.g. Dim Sum")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (HKD)", min_value=0.0, value=None, step=1.0)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            note = st.text_input("Note (Optional)", placeholder="เพิ่มเติม...")
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount is not None:
                    now_full = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now_full, "Item": item, "Amount_HKD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Note": note, "Is_Settled": settled}])
                    conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                    st.rerun()

    if not df.empty:
        with st.expander("EDIT"):
            list_edit = [f"{i}: {r['Item']}" for i, r in df.iterrows()]
            sel_edit = st.selectbox("Select Item to Edit", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Name", value=r['Item'])
                    e_amount = st.number_input("Price", value=float(r['Amount_HKD']))
                    e_cat = st.selectbox("Category", categories, index=categories.index(r['Category']) if r['Category'] in categories else 0)
                    e_note = st.text_input("Note", value=r['Note'] if pd.notna(r['Note']) else "")
                    if st.form_submit_button("UPDATE"):
                        df.at[idx, 'Item'], df.at[idx, 'Amount_HKD'], df.at[idx, 'Category'], df.at[idx, 'Note'] = e_item, e_amount, e_cat, e_note
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df); st.rerun()

        with st.expander("DELETE"):
            list_del = [f"{i}: {r_del['Item']}" for i, r_del in
