import discord
from discord import app_commands
from db import save_answer
from discord.ext import commands

# 質問のリスト
QUESTIONS = [
    "好きな食べ物は？",
    "好きなコンテンツは？",
    "好きなアーティストは？",
    "最近ハマってる趣味は？",
    "私はこんな人"
]

async def setup(bot):
    @bot.tree.command(name="add_card", description="質問に対する答えを保存します")
    @app_commands.describe(question="答える質問を選んでください", answer="答えを入力してください")
    @app_commands.choices(
        question=[
            app_commands.Choice(name=QUESTIONS[i], value=i) for i in range(len(QUESTIONS))
        ]
    )
    async def add_card(interaction: discord.Interaction, question: app_commands.Choice[int], answer: str):
        # ユーザーIDを取得
        user_id = interaction.user.id
        
        # 質問を取得
        question_text = QUESTIONS[question.value]
        
        # データベースに保存
        save_answer(user_id, question_text, answer)

        # ユーザーに保存完了メッセージを送信
        await interaction.response.send_message(f"質問「{question_text}」への答え「{answer}」が保存されました。")
