from firebase_config import db

from firebase_config import db

def save_answer(user_id: int, question: str, answer: str):
    user_doc = db.collection("users").document(str(user_id))
    user_doc.set({
        question: answer
    }, merge=True)

def get_user_answers(user_id: int):
    user_doc = db.collection("users").document(str(user_id)).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        return list(data.items())  # [(question, answer), ...]
    else:
        return []
