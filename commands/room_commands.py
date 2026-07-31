import discord
from discord import app_commands
from features.auto_room import auto_rooms


async def setup(bot: discord.Client):
    @bot.tree.command(name="room_name", description="自動作成した部屋の名前を変更します")
    @app_commands.describe(name="新しい部屋名")
    async def room_name(interaction: discord.Interaction, name: str):
        member = interaction.user
        vc = member.voice.channel if member.voice else None

        if not vc or vc.id not in auto_rooms:
            await interaction.response.send_message("自動作成した部屋にいるときに使用してください。", ephemeral=True)
            return

        await vc.edit(name=name)
        await interaction.response.send_message(f"部屋名を「{name}」に変更しました。", ephemeral=True)
