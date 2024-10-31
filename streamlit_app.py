import streamlit as st
import pandas as pd
from components.quiz import show_quiz_screen
from components.result import show_result_screen
from utils.logger import setup_logger

def init_session_state():
    """セッション状態の初期化"""
    if 'screen' not in st.session_state:
        st.session_state.screen = 'login'
    if 'question_index' not in st.session_state:
        st.session_state.question_index = 0
    if 'correct_count' not in st.session_state:
        st.session_state.correct_count = 0
    if 'total_attempted' not in st.session_state:
        st.session_state.total_attempted = 0
    if 'nickname' not in st.session_state:
        st.session_state.nickname = None
    if 'logger' not in st.session_state:
        st.session_state.logger = None
    if 'quiz_df' not in st.session_state:
        st.session_state.quiz_df = None

def init_logger():
    """ロガーの初期化と設定"""
    try:
        if st.session_state.logger is None:
            try:
                SPREADSHEET_ID = st.secrets.gsheet["spreadsheet_id"]
                user_id = st.session_state.nickname or "anonymous"
                st.session_state.logger = setup_logger(
                    spreadsheet_id=SPREADSHEET_ID,
                    user_id=user_id
                )
            except Exception as e:
                st.write("デバッグ - 利用可能なsecrets:", list(st.secrets.keys()))
                st.write("デバッグ - gsheetの内容:", dict(st.secrets.gsheet))
                st.error(f"spreadsheet IDの取得に失敗: {str(e)}")
                return False
        return True
    except Exception as e:
        st.error(f"ロガーの初期化に失敗しました: {str(e)}")
        return False

@st.cache_data
def load_data():
    """データの読み込み"""
    try:
        df = pd.read_excel('f_kansen.xlsx', sheet_name='sheet1', index_col=0)
        return df
    except Exception as e:
        st.error("データの読み込みに失敗しました。")
        return None

def show_sidebar():
    """サイドバーの表示"""
    with st.sidebar:
        if st.session_state.nickname:
            if st.button("ログアウト"):
                st.session_state.nickname = None
                st.session_state.logger = None
                st.session_state.screen = 'login'
                st.session_state.quiz_df = None
                st.rerun()

def show_login_screen():
    """ログイン画面の表示"""
    st.title("ログイン")
    with st.form("login_form"):
        nickname = st.text_input("ニックネームを入力してください")
        submitted = st.form_submit_button("開始")
        
        if submitted and nickname:
            st.session_state.nickname = nickname
            st.session_state.screen = 'quiz'
            
            if init_logger():
                st.rerun()
            else:
                st.error("ログインできません。システム管理者に連絡してください。")

def main():
    # 初期化処理
    init_session_state()
    
    # サイドバーの表示
    show_sidebar()
    
    # 画面の表示を切り替え
    if st.session_state.screen == 'result':
        if st.session_state.quiz_df is not None:
            show_result_screen(st.session_state.quiz_df)
        else:
            df = load_data()
            if df is not None:
                st.session_state.quiz_df = df
                show_result_screen(df)
            else:
                st.error("問題データを読み込めませんでした。")
    elif st.session_state.nickname is None:
        show_login_screen()
    else:
        if not init_logger():
            st.error("ロガーの初期化に失敗しました。")
            return
            
        df = load_data()
        if df is not None:
            st.session_state.quiz_df = df
            show_quiz_screen(
                df=df,
                logger=st.session_state.logger
            )
        else:
            st.error("問題データを読み込めませんでした。")

if __name__ == "__main__":
    main()