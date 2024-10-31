import os
import sys
from google.oauth2 import service_account
import google_auth_httplib2
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from googleapiclient.errors import HttpError
import logging
import json
from datetime import datetime
import pytz
import time
import streamlit as st
from .config import SPREADSHEET_ID

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
JP_TZ = pytz.timezone('Asia/Tokyo')

# グローバル変数としてloggerを定義
logger = None

class JSTFormatter(logging.Formatter):
    """JSTタイムゾーンに対応したフォーマッタ"""
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, pytz.UTC)
        return dt.astimezone(JP_TZ)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

    def format(self, record):
        # レコードの作成時刻を確実に現在のUTC時刻に
        record.created = time.time()
        return super().format(record)

class JSTStreamHandler(logging.StreamHandler):
    """JSTに対応したStreamHandler"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Windows環境での文字化け対策
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                stream.buffer.write((msg + self.terminator).encode('utf-8'))
            self.flush()
        except Exception:
            self.handleError(record)

class GoogleSheetsHandler(logging.Handler):
    """Google Sheetsにログを保存するハンドラ"""
    def __init__(self, spreadsheet_id, sheet_name='logs'):
        super().__init__()
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.gsheet_connector = self._connect_to_gsheet()
        self._setup_sheet()
    
    def _connect_to_gsheet(self):
        """Streamlitのシークレットを使用してGoogle Sheetsに接続"""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["connections"]["gcs"],
                scopes=SCOPE
            )
            
            def build_request(http, *args, **kwargs):
                new_http = google_auth_httplib2.AuthorizedHttp(
                    credentials, http=httplib2.Http()
                )
                return HttpRequest(new_http, *args, **kwargs)
                
            authorized_http = google_auth_httplib2.AuthorizedHttp(
                credentials, http=httplib2.Http()
            )
            
            service = build(
                "sheets",
                "v4",
                requestBuilder=build_request,
                http=authorized_http
            )
            return service.spreadsheets()
        except Exception as e:
            print(f"Google Sheets接続エラー: {str(e)}")
            self.handleError(None)
            raise

    def _setup_sheet(self):
        """シートの存在確認と初期設定"""
        try:
            spreadsheet = self.gsheet_connector.get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            if self.sheet_name not in sheet_names:
                request = {
                    'addSheet': {
                        'properties': {
                            'title': self.sheet_name
                        }
                    }
                }
                self.gsheet_connector.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
            
            headers = ['Log Message']
            self.gsheet_connector.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            
        except HttpError as e:
            print(f"シートの初期化中にエラーが発生: {e}")
            self.handleError(None)
            raise

    def add_row_to_gsheet(self, row_data):
        """Google Sheetsに1行のデータを追加"""
        try:
            self.gsheet_connector.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:A',
                valueInputOption='USER_ENTERED',
                body={'values': [[row_data]]}
            ).execute()
            return True
        except Exception as e:
            print(f"行の追加中にエラーが発生: {str(e)}")
            self.handleError(None)
            return False

    def emit(self, record):
        """ログレコードをGoogle Sheetsに書き込む"""
        try:
            formatted_message = self.format(record)
            self.add_row_to_gsheet(formatted_message)
        except Exception as e:
            print(f"Google Sheetsへのログ書き込み中にエラーが発生: {str(e)}")
            self.handleError(record)

def setup_logger(
    spreadsheet_id=SPREADSHEET_ID,
    log_level=logging.INFO,
    user_id=None,
    encoding='utf-8'
):
    """新しいロガーインスタンスを設定して返す"""
    global logger
    
    if logger is not None:
        return logger

    logger_name = f'xlsx_data_app_{user_id}' if user_id else 'xlsx_data_app'
    logger = logging.getLogger(logger_name)
    
    # 既存のハンドラがある場合はクリア
    logger.handlers.clear()
    
    try:
        # Google Sheetsハンドラの設定
        sheets_handler = GoogleSheetsHandler(spreadsheet_id)
        sheets_handler.setLevel(log_level)
        
        # コンソールハンドラの設定
        console_handler = JSTStreamHandler()
        console_handler.setLevel(log_level)
        
        # フォーマッタの設定
        formatter = JSTFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S %Z'
        )
        
        sheets_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(sheets_handler)
        logger.addHandler(console_handler)
        
        logger.setLevel(log_level)
        
        # 初期ログ
        now_jst = datetime.now(JP_TZ)
        logger.info(f"新しいログセッションを開始しました [{now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}]")
        
        return logger
        
    except Exception as e:
        print(f"ログ設定中にエラーが発生しました: {str(e)}")
        raise

def get_logs(
    spreadsheet_id,
    user_id=None,
    level=None,
    limit=100
):
    """Google Sheetsからログを取得"""
    try:
        handler = GoogleSheetsHandler(spreadsheet_id)
        result = handler.gsheet_connector.values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{handler.sheet_name}!A:A'
        ).execute()
        
        values = result.get('values', [])[1:]  # ヘッダーを除外
        
        filtered_values = []
        for row in values:
            if len(row) > 0:  # 空行をスキップ
                log_message = row[0]
                if user_id and f"ユーザー[{user_id}]" not in log_message:
                    continue
                if level and f" - {level} - " not in log_message:
                    continue
                filtered_values.append(row)
        
        return filtered_values[-limit:]
        
    except HttpError as e:
        print(f"ログの取得エラー: {e}")
        return []

# デフォルトロガーの初期化を防ぐ
if not logger:
    logger = setup_logger()