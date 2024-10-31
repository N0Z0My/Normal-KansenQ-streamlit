import streamlit as st
import pandas as pd
from pathlib import Path
from utils.logger import setup_logger, get_logs
from datetime import datetime, timedelta

def get_admin_logger():
    """管理者用のロガーを取得"""
    SPREADSHEET_ID = st.secrets["spreadsheet_id"]
    return setup_logger(
        spreadsheet_id=SPREADSHEET_ID,
        user_id="admin"  # 管理者用のログとして識別
    )

def show_admin_screen():
    """管理者画面のメイン表示"""
    logger = get_admin_logger()
    logger.info("管理者画面にアクセスしました")
    
    st.title("管理者画面 📊")
    
    tab1, tab2 = st.tabs(["📝 ログ閲覧", "📊 統計情報"])

    with tab1:
        show_log_viewer()
    
    with tab2:
        show_statistics()

    if st.button("クイズ画面に戻る"):
        logger.info("管理者画面からクイズ画面に戻ります")
        st.session_state.screen = 'quiz'
        st.rerun()

def show_log_viewer():
    """ログ閲覧画面の表示"""
    logger = get_admin_logger()
    st.header("ログ閲覧")
    
    # フィルター設定
    col1, col2 = st.columns(2)
    with col1:
        user_filter = st.text_input("ユーザーIDでフィルター")
    with col2:
        level_filter = st.selectbox(
            "ログレベルでフィルター",
            ["すべて", "INFO", "ERROR", "WARNING"]
        )
    
    level = None if level_filter == "すべて" else level_filter
    try:
        SPREADSHEET_ID = st.secrets["spreadsheet_id"]
        logs = get_logs(
            spreadsheet_id=SPREADSHEET_ID,
            user_id=user_filter if user_filter else None,
            level=level,
            limit=1000  # 表示件数制限
        )
        
        if logs:
            # ログデータをDataFrameに変換
            df_logs = pd.DataFrame(logs, columns=[
                'created_at', 'user_id', 'level', 'logger_name', 'message', 'extra_data'
            ])
            
            # タイムスタンプを日本時間に変換
            df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
            
            # ログ表示
            st.dataframe(
                df_logs.style.highlight_cells(
                    subset=['level'],
                    value=['ERROR'],
                    color='red'
                ),
                height=400
            )
            
            # CSVダウンロード
            csv = df_logs.to_csv(index=False)
            st.download_button(
                label="📥 ログをCSVでダウンロード",
                data=csv,
                file_name=f"quiz_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("表示するログがありません")
            
    except Exception as e:
        logger.error(f"ログの読み込みに失敗: {str(e)}")
        st.error(f"ログの読み込みに失敗しました: {str(e)}")

def show_statistics():
    """統計情報画面の表示"""
    logger = get_admin_logger()
    st.header("統計情報")
    
    # 期間指定
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "開始日",
            datetime.now().date() - timedelta(days=7)
        )
    with col2:
        end_date = st.date_input("終了日", datetime.now().date())
    
    try:
        SPREADSHEET_ID = st.secrets["spreadsheet_id"]
        logs = get_logs(
            spreadsheet_id=SPREADSHEET_ID,
            limit=1000
        )
        
        if logs:
            # ログデータをDataFrameに変換
            df_logs = pd.DataFrame(logs, columns=[
                'created_at', 'user_id', 'level', 'logger_name', 'message', 'extra_data'
            ])
            
            # タイムスタンプを変換
            df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
            
            # 期間でフィルタリング
            mask = (df_logs['created_at'].dt.date >= start_date) & (df_logs['created_at'].dt.date <= end_date)
            df_filtered = df_logs[mask]
            
            # クイズ関連のログのみを抽出
            df_quiz = df_filtered[df_filtered['message'].str.contains('正解|不正解', na=False)]
            
            # 基本統計の計算
            total_answers = len(df_quiz)
            correct_answers = len(df_quiz[df_quiz['message'].str.contains('正解', na=False)])
            accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
            
            # 統計情報の表示
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="総回答数", value=total_answers)
            with col2:
                st.metric(label="正解数", value=correct_answers)
            with col3:
                st.metric(label="正答率", value=f"{accuracy:.1f}%")
            
            # ユーザー別の統計
            st.subheader("ユーザー別統計")
            user_stats = df_quiz.groupby('user_id').agg({
                'message': 'count'
            }).rename(columns={'message': '回答数'})
            st.dataframe(user_stats)
            
            logger.info(f"統計情報を表示しました（期間：{start_date}～{end_date}）")
        else:
            st.info("表示するデータがありません")
            
    except Exception as e:
        logger.error(f"統計情報の集計に失敗: {str(e)}")
        st.error(f"統計情報の集計に失敗しました: {str(e)}")