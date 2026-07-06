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

    @bot.tree.command(name="room_limit", description="自動作成した部屋の人数制限を設定します")
    @app_commands.describe(limit="人数制限（0で無制限）")
    async def room_limit(interaction: discord.Interaction, limit: int):
        member = interaction.user
        vc = member.voice.channel if member.voice else None

        if not vc or vc.id not in auto_rooms:
            await interaction.response.send_message("自動作成した部屋にいるときに使用してください。", ephemeral=True)
            return

        if limit < 0 or limit > 99:
            await interaction.response.send_message("人数制限は0〜99の範囲で指定してください。", ephemeral=True)
            return

        await vc.edit(user_limit=limit)
        msg = f"人数制限を {limit} 人に設定しました。" if limit > 0 else "人数制限を解除しました。"
        await interaction.response.send_message(msg, ephemeral=True)
