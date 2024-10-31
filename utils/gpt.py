from openai import OpenAI
from utils.logger import setup_logger
import asyncio
from .config import SPREADSHEET_ID, OPENAI_API_KEY

# OpenAI クライアントの初期化
client = OpenAI(api_key=OPENAI_API_KEY)

# loggerの初期化
logger = setup_logger(spreadsheet_id=SPREADSHEET_ID, user_id="gpt")

async def evaluate_answer_with_gpt(question, options, user_answer):
    """GPTによる回答評価を行い、結果を返す"""
    prompt = f"""
    問題: {question}
    選択肢: {options}
    ユーザーの回答: {user_answer}

    以下の手順でユーザーの回答を評価し、必ず指定された形式で回答してください：

    1. 問題文と選択肢から最も適切な選択肢を１つ選んでください。（この内容は出力しないでください）
    2. ユーザーの回答が最も適切な選択肢と一致するか評価してください。（この内容は出力しないでください）
    3. 以下のフォーマットで厳密に回答してください：

    RESULT:[CORRECT] または RESULT:[INCORRECT]
    あなたの回答: [ユーザーの回答]
    正解: [適切な選択肢]
    解説: [簡潔な解説]
    """

    try:
        logger.info(f"GPT評価開始 - 問題: {question}, ユーザー回答: {user_answer}")
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4",
            temperature=0.4,
            messages=[
                {"role": "system", "content": "あなたは海外旅行の豊富な知識を持っていて、ユーザーの回答を評価する優秀な採点者です。必ず指定された形式で回答してください。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        gpt_response = response.choices[0].message.content
        logger.info(f"GPT評価完了 - 結果: {gpt_response}")
        
        return gpt_response

    except Exception as e:
        error_msg = f"エラーが発生しました: {str(e)}"
        logger.error(error_msg)
        return f"""
        RESULT:[INCORRECT]
        あなたの回答: {user_answer}
        正解: 評価中にエラーが発生しました
        解説: 申し訳ありません。回答の評価中にエラーが発生しました。もう一度お試しください。
        """