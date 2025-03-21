import discord
from discord import app_commands
from firebase_config import db  # Firestoreを使うために必要

# 質問のリスト
QUESTIONS = [
    "好きな食べ物は？",
    "好きなコンテンツは？",
    "好きなアーティストは？",
    "最近ハマってる趣味は？",
    "私はこんな人"
]

# Firestore に回答を保存する関数
def save_answer(user_id: int, question: str, answer: str):
    user_doc = db.collection("users").document(str(user_id))
    user_doc.set({
        question: answer
    }, merge=True)

# コマンドのセットアップ
async def setup(bot: discord.Client):
    @bot.tree.command(name="add_card", description="質問に対する答えを保存します")
    @app_commands.describe(question="答える質問を選んでください", answer="答えを入力してください")
    @app_commands.choices(
        question=[
            app_commands.Choice(name=QUESTIONS[i], value=i) for i in range(len(QUESTIONS))
        ]
    )
    async def add_card(interaction: discord.Interaction, question: app_commands.Choice[int], answer: str):
        user_id = interaction.user.id
        question_text = QUESTIONS[question.value]

        save_answer(user_id, question_text, answer)

        await interaction.response.send_message(
            f"質問「{question_text}」への答え「{answer}」が保存されました。", ephemeral=True
        )
