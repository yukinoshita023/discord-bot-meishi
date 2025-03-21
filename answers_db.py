from firebase_config import db

# 質問と回答をFirestoreに保存
from firebase_config import db

def save_answer(user_id: int, question: str, answer: str):
    user_doc = db.collection("users").document(str(user_id))
    user_doc.set({
        question: answer
    }, merge=True)

# ユーザーの回答履歴を取得
def get_user_answers(user_id: int):
    user_doc = db.collection("users").document(str(user_id)).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        return list(data.items())  # [(question, answer), ...]
    else:
        return []
