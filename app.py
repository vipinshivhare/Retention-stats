import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- Page Layout & Dark Styling ---
st.set_page_config(page_title="Course Performance Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: white !important; font-family: 'Helvetica', sans-serif; }
    .stSelectbox label { color: #3498DB !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Course Performance Dashboard")

# --- DATA LOADING LOGIC ---
st.sidebar.header("📂 Data Source")

# Aapki default link yahan set kar di hai
DEFAULT_LINK = "https://docs.google.com/spreadsheets/d/1jx_9Sj0uH9gkEgE7dNS8Ma_XIUr3NWkJz0-iiNduc40/edit?gid=0#gid=0"

source_type = st.sidebar.radio("Data kahan se laayein?", ["Google Sheet (Personal)", "Local Folder (data/)"])

@st.cache_data(ttl=300) # 5 minutes cache
def load_gsheet(url):
    try:
        # Edit link ko export link mein convert karna
        csv_url = url.split('/edit')[0] + '/export?format=csv'
        return pd.read_csv(csv_url)
    except:
        return None

df = None

if source_type == "Google Sheet (Personal)":
    # value=DEFAULT_LINK ki wajah se ye ab pehle se bhara hua aayega
    gsheet_url = st.sidebar.text_input("Google Sheet Link:", value=DEFAULT_LINK)
    
    if gsheet_url:
        df = load_gsheet(gsheet_url)
        if df is not None:
            st.sidebar.success("✅ Sheet Loaded!")
        else:
            st.sidebar.error("❌ Link check karo ya sheet ko Public karo.")
    
    if st.sidebar.button("🔄 Sync New Data"):
        st.cache_data.clear()
        st.rerun()

else:
    folder_name = "data"
    if os.path.exists(folder_name):
        files = [f for f in os.listdir(folder_name) if f.endswith('.csv')]
        if files:
            file_path = os.path.join(folder_name, files[0])
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            st.sidebar.success("✅ Local CSV Loaded!")

# --- Processing & Dashboard Logic ---
if df is not None:
    df.columns = df.columns.str.strip()

    # Static Column Mapping
    week_col, course_col = 'Week', 'Course'
    total_conv, couns_conv, sop_conv = 'Total Conversions', 'Counselling Conversions', 'SOP Conversions'
    couns_perc, ret_perc = 'Counselling Conversion%', 'Retention Conversion%'

    # Percent cleanup
    for col in [couns_perc, ret_perc]:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='coerce')

    # --- Top Filter ---
    st.markdown("---")
    all_courses = sorted(df[course_col].unique())
    selected_course = st.selectbox("🔍 Search & Select Course:", options=all_courses)
    
    course_df = df[df[course_col] == selected_course].sort_values(by=week_col)

    if not course_df.empty:
        st.markdown(f"### Visualizing Trend: {selected_course}")
        
        # --- DUAL SUBPLOTS ---
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.15,
            subplot_titles=("Counselling Conversion Trend (1% Scale)", "Retention Conversion Trend (10% Scale)")
        )

        fig.add_trace(go.Scatter(x=course_df[week_col], y=course_df[couns_perc], 
                                 name='Counselling %', mode='lines+markers+text',
                                 line=dict(color='#3498DB', width=3),
                                 text=course_df[couns_perc].astype(str)+'%', textposition='top center'), row=1, col=1)

        fig.add_trace(go.Scatter(x=course_df[week_col], y=course_df[ret_perc], 
                                 name='Retention %', mode='lines+markers+text',
                                 line=dict(color='#E74C3C', width=3),
                                 text=course_df[ret_perc].astype(str)+'%', textposition='top center'), row=2, col=1)

        fig.update_yaxes(title_text="Conv %", dtick=1, gridcolor='#3E4255', row=1, col=1)
        fig.update_yaxes(title_text="Retention %", dtick=10, range=[0, 110], gridcolor='#3E4255', row=2, col=1)

        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=750, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

        # --- Detailed Data View ---
        st.divider()
        st.subheader("📋 Detailed Data View")
        final_cols = [week_col, total_conv, couns_conv, sop_conv, couns_perc, ret_perc]
        
        # Download Button Feature
        csv_data = course_df[final_cols].to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download This Course Data (CSV)", data=csv_data, file_name=f"{selected_course}_report.csv", mime='text/csv')
        
        st.dataframe(course_df[final_cols], use_container_width=True, hide_index=True)

    else:
        st.error("Bhai, is course ka data nahi mil raha.")
else:
    st.info("👈 Sidebar mein link check karein.")