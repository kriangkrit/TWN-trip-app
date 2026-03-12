import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Config & Minimalism Style ---
st.set_page_config(page_title="TAIWAN 2026", page_icon="🇹🇼", layout="centered")

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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1jM63Gi3Mh_ZGJAlNc9CA2ohlLEvuAnnSdCOvp88Nr1U/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("TAIWAN TRIP 2026")
tab1, tab2 = st.tabs(["💰 EXPENSE", "📊 SUMMARY"])
# เปลี่ยนชื่อคนตรงนี้ครับ
members = ["JOY", "F"]
categories = ["Food", "Drinks", "Transport", "Shopping", "Hotel", "Flight", "Others"]

# --- Data Loading ---
try:
    df = conn.read(spreadsheet=SHEET_URL, worksheet=0, ttl=0).dropna(how='all')
    if not df.empty:
        df['Amount_TWD'] = pd.to_numeric(df['Amount_TWD'], errors='coerce').fillna(0)
    if 'Note' not in df.columns: df['Note'] = ""
    if 'Is_Settled' not in df.columns: df['Is_Settled'] = False
except:
    # ปรับชื่อคอลัมน์เป็น Amount_TWD ให้เข้ากับไต้หวัน
    df = pd.DataFrame(columns=["Timestamp", "Item", "Amount_TWD", "Payer", "Participants", "Category", "Note", "Is_Settled"])

# --- TAB 1: EXPENSE ---
with tab1:
    with st.expander("ADD NEW", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            item = st.text_input("Item", placeholder="e.g. Bubble Tea")
            c1, c2 = st.columns(2)
            with c1: amount = st.number_input("Price (TWD)", min_value=0.0, value=None, step=1.0)
            with c2: payer = st.selectbox("Payer", members)
            cat = st.selectbox("Category", categories)
            parts = st.multiselect("Split with", members, default=members)
            note = st.text_input("Note (Optional)", placeholder="etc...")
            settled = st.checkbox("Settled (Pre-paid)")
            if st.form_submit_button("SAVE"):
                if item and amount is not None:
                    now_full = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M")
                    new_row = pd.DataFrame([{"Timestamp": now_full, "Item": item, "Amount_TWD": float(amount), "Payer": payer, "Participants": ", ".join(parts), "Category": cat, "Note": note, "Is_Settled": settled}])
                    try:
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=pd.concat([df, new_row], ignore_index=True))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating sheet: {e}")

    if not df.empty:
        with st.expander("EDIT"):
            list_edit = [f"{i}: {r['Item']}" for i, r in df.iterrows()]
            sel_edit = st.selectbox("Select Item to Edit", ["-- Select --"] + list_edit)
            if sel_edit != "-- Select --":
                idx = int(sel_edit.split(":")[0])
                r = df.iloc[idx]
                with st.form("edit_form"):
                    e_item = st.text_input("Name", value=r['Item'])
                    e_amount = st.number_input("Price", value=float(r['Amount_TWD']))
                    e_cat = st.selectbox("Category", categories, index=categories.index(r['Category']) if r['Category'] in categories else 0)
                    e_note = st.text_input("Note", value=r['Note'] if pd.notna(r['Note']) else "")
                    if st.form_submit_button("UPDATE"):
                        df.at[idx, 'Item'], df.at[idx, 'Amount_TWD'], df.at[idx, 'Category'], df.at[idx, 'Note'] = e_item, e_amount, e_cat, e_note
                        conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df)
                        st.rerun()

        with st.expander("DELETE"):
            list_del = [f"{i}: {r_del['Item']}" for i, r_del in df.iterrows()]
            sel_del = st.selectbox("Choose item to remove", ["-- Select --"] + list_del)
            if sel_del != "-- Select --" and st.button("CONFIRM DELETE", use_container_width=True):
                idx_to_del = int(sel_del.split(":")[0])
                conn.update(spreadsheet=SHEET_URL, worksheet=0, data=df.drop(idx_to_del).reset_index(drop=True))
                st.rerun()

        st.write("")
        display_df = df.copy()
        display_df['Date'] = display_df['Timestamp'].str.split().str[0]
        final_df = display_df.sort_index(ascending=False)[['Date', 'Item', 'Amount_TWD', 'Payer', 'Category', 'Note']]
        st.dataframe(final_df, use_container_width=True, hide_index=True)

# --- TAB 2: SUMMARY ---
with tab2:
    if not df.empty and df['Amount_TWD'].sum() > 0:
        cat_sum = df.groupby('Category')['Amount_TWD'].sum().reset_index()
        cat_sum = cat_sum[cat_sum['Amount_TWD'] > 0]
        if not cat_sum.empty:
            fig = px.pie(cat_sum, values='Amount_TWD', names='Category', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=20, b=20, l=10, r=10), font=dict(family="Anuphan", size=14))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<p style='font-weight:300;'>CATEGORY BREAKDOWN</p>", unsafe_allow_html=True)
            st.table(cat_sum.style.format({'Amount_TWD': '{:,.0f}'}))
            st.divider()

            # เรทเงินไต้หวันปกติจะประมาณ 1.05 - 1.10
            rate = st.number_input("Rate (1 TWD = ? THB)", value=1.08, step=0.01)
            df['Is_Settled'] = df['Is_Settled'].apply(lambda x: str(x).upper() == 'TRUE' or x == True)
            bal = {m: 0.0 for m in members}
            for _, r in df[df['Is_Settled'] == False].iterrows():
                bal[r['Payer']] += float(r['Amount_TWD'])
                p_list = str(r['Participants']).split(", ")
                for p in p_list: 
                    if p in bal: bal[p] -= (float(r['Amount_TWD']) / len(p_list))

            diff = bal["JOY"]
            c1, c2 = st.columns(2)
            c1.metric("TRANSFER (TWD)", f"{abs(diff):,.2f}")
            c2.metric("TRANSFER (THB)", f"{abs(diff)*rate:,.0f}")
            if diff > 0.01: st.info("F → JOY")
            elif diff < -0.01: st.info("JOY → F")

            st.markdown("<hr style='border: 0.5px solid #eee; margin-top: 30px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:300;'>NET SPEND PER PERSON</p>", unsafe_allow_html=True)
            
            usage = {m: 0.0 for m in members}
            user_items = {m: [] for m in members}
            for _, r in df.iterrows():
                p_list = str(r['Participants']).split(", ")
                share = float(r['Amount_TWD']) / len(p_list)
                for p in p_list: 
                    if p in usage: 
                        usage[p] += share
                        user_items[p].append(f"{r['Item']} ({share:,.0f})")
            
            usage_df = pd.DataFrame([{"Name": m, "TWD": usage[m], "THB": usage[m]*rate} for m in members])
            st.table(usage_df.style.format({'TWD': '{:,.2f}', 'THB': '{:,.2f}'}))
            
            joy_items = ' • ' + ' <br> • '.join(user_items["JOY"]) if user_items["JOY"] else 'No items'
            f_items = ' • ' + ' <br> • '.join(user_items["F"]) if user_items["F"] else 'No items'

            st.markdown(f"""
                <div class="mobile-flex-container">
                    <div class="flex-item-box">
                        <div class="member-label">JOY's Items</div>
                        <div class="item-text-centered">{joy_items}</div>
                    </div>
                    <div class="flex-item-box">
                        <div class="member-label">F's Items</div>
                        <div class="item-text-centered">{f_items}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info("No data.")
