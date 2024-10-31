import streamlit as st
from utils.logger import logger

def show_result_screen(df):
    st.title("🙌クイズ完了")
    
    # quiz_resultsからスコア情報を取得
    if 'quiz_results' not in st.session_state:
        logger.error("quiz_resultsが見つかりません")
        return
        
    results = st.session_state.quiz_results
    total_questions = results['total_questions']  # MAX_QUESTIONS(3)と同じ
    correct_count = results['correct_count']
    
    # 正答率の計算
    accuracy = (correct_count / total_questions) * 100
    
    logger.info(f"クイズ完了 - 正解数: {correct_count}/ {total_questions} , 正答率: {accuracy:.1f}%")
    
    # スコア表示
    st.markdown(f"## 最終スコア")
    st.markdown(f"### {correct_count} / {total_questions} 問 正解！")
    st.markdown(f"### 正答率: {accuracy:.1f}%")
    
    # 回答履歴の表示（オプション）
    if 'answers_history' in results:
        st.markdown("## 回答履歴")
        for q_idx, answer_data in results['answers_history'].items():
            with st.expander(f"問題 {q_idx + 1}: {answer_data['question']}"):
                st.write(f"あなたの回答: {answer_data['user_answer']}")
                st.write(f"結果: {'✅ 正解' if answer_data['is_correct'] else '❌ 不正解'}")
                st.write("解説:")
                st.write(answer_data['explanation'])
    
    # 成績に応じたメッセージ
    if accuracy == 100:
        st.markdown("### 💯 完璧です！素晴らしい成績です！")
    elif accuracy >= 80:
        st.markdown("### 🌟 素晴らしい成績です！")
    elif accuracy >= 60:
        st.markdown("### 👍 よく頑張りました！")
    else:
        st.markdown("### 💪 次は更に良い成績を目指しましょう！")
    
    # リトライボタン
    if st.button("もう一度チャレンジ"):
        reset_session_state()
        st.rerun()

def reset_session_state():
    """クイズの状態を初期化"""
    logger.info("クイズを再スタート")
    
    # 初期化が必要な全てのセッション状態をリセット
    keys_to_reset = {
        'screen': 'quiz',
        'question_index': 0,
        'total_attempted': 0,
        'answered_questions': set(),
        'correct_answers': {},
        'answers_history': {},
        'quiz_results': None
    }
    
    for key, value in keys_to_reset.items():
        st.session_state[key] = value