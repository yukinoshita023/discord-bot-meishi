import discord
from discord import app_commands
from db import save_answer
from discord.ext import commands

# 質問のリスト
QUESTIONS = [
    "好きな色は何ですか？",
    "好きな食べ物は何ですか？",
    "好きな映画は何ですか？",
    "好きな本は何ですか？",
    "好きな音楽のジャンルは何ですか？"
]

async def setup(bot):
    @bot.tree.command(name="add_card", description="質問に対する答えを保存します")
    async def add_card(interaction: discord.Interaction, question_index: int, answer: str):
        # 質問インデックスが範囲内か確認
        if question_index < 0 or question_index >= len(QUESTIONS):
            await interaction.response.send_message("無効な質問番号です。")
            return
        
        # 質問と答えを取得
        question = QUESTIONS[question_index]
        
        # ユーザーIDを取得
        user_id = interaction.user.id
        
        # データベースに保存
        save_answer(user_id, question, answer)

        # ユーザーに保存完了メッセージを送信
        await interaction.response.send_message(f"質問「{question}」への答え「{answer}」が保存されました。")
