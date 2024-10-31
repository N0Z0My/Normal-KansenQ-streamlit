import streamlit as st

# Google Sheets関連の設定
SPREADSHEET_ID = st.secrets["gsheet"]["spreadsheet_id"]

# OpenAI関連の設定
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

SHEET_NAME = "sheet1"