import discord
from features.voice_card import create_voice_card, fetch_answers


async def setup(bot: discord.Client):
    @bot.tree.command(name="meishi", description="自分のメイシを表示します")
    async def meishi(interaction: discord.Interaction):
        member = interaction.user

        answers = fetch_answers(member.id)
        if not answers:
            await interaction.response.send_message(
                "まだ自己紹介が未設定です！ `/add_card` で登録してみてね！", ephemeral=True
            )
            return

        image = create_voice_card(member)
        await interaction.response.send_message(
            file=discord.File(image, filename="voice_card.png")
        )
