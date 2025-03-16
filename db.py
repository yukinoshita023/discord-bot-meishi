import sqlite3

# データベースの初期化
def init_db():
    conn = sqlite3.connect('answers.db')
    c = conn.cursor()
    # テーブルが存在しない場合は作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 質問と回答をデータベースに保存
def save_answer(user_id, question, answer):
    conn = sqlite3.connect('answers.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO answers (user_id, question, answer)
        VALUES (?, ?, ?)
    ''', (user_id, question, answer))
    conn.commit()
    conn.close()

# ユーザーの回答履歴を取得
def get_user_answers(user_id):
    conn = sqlite3.connect('answers.db')
    c = conn.cursor()
    c.execute('SELECT question, answer FROM answers WHERE user_id = ?', (user_id,))
    answers = c.fetchall()
    conn.close()
    return answers
