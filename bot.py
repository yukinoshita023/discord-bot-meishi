import discord
from config import TOKEN
from commands import setup_commands
from voice_card import handle_voice_state_update
from role_manager import assign_role_to_member, remove_role_from_member

from firebase_config import db

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        await setup_commands(self)
        print("全コマンドを追加しました")

        await self.tree.sync()
        print("スラッシュコマンドを同期しました")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    await handle_voice_state_update(member, before, after)

    if before.channel != after.channel:
        if after.channel:
            await assign_role_to_member(member, after.channel.id)
        elif before.channel:
            await remove_role_from_member(member, before.channel.id)

bot.run(TOKEN)
