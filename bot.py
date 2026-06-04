import discord
from config import TOKEN
from commands import setup_commands
from features.auto_room import handle_auto_room

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
    for guild in bot.guilds:
        p = guild.me.guild_permissions
        print(f"[権限チェック] {guild.name}")
        print(f"  manage_channels : {p.manage_channels}")
        print(f"  manage_roles    : {p.manage_roles}")
        print(f"  move_members    : {p.move_members}")

@bot.event
async def on_voice_state_update(member, before, after):
    await handle_auto_room(member, before, after)


bot.run(TOKEN)
