import discord

# ボイスチャンネルIDとロールIDのマッピング（ボイスチャンネルID -> ロールID）
VOICE_CHANNEL_TO_ROLE = {
    847514073964740679: 1350763127389687913,  # モクモク1
    905313176277626880: 1350762922724294688,  # モクモク2
    905313335715713084: 1350763241550123038,  # モクモク3
    860122545381572608: 1350763276186681354,  # ノンビリ1
    905329359244656710: 1350763307639898132,  # ノンビリ2
    905329383630340117: 1350763336152780810,  # ノンビリ3
    847158182257754116: 1350763367228248185,  # ワイワイ1
    905332813853765642: 1350763406474612736,  # ワイワイ2
    905332899421769728: 1350763431363612693,  # ワイワイ3
}

async def assign_role_to_member(member: discord.Member, channel_id: int):
    """
    ボイスチャンネルに接続したユーザーに対応するロールを付与する
    """
    role_id = VOICE_CHANNEL_TO_ROLE.get(channel_id)
    if role_id:
        role = discord.utils.get(member.guild.roles, id=role_id)
        if role:
            await member.add_roles(role)
            print(f"{member.name} にロール {role.name} を付与しました")
        else:
            print(f"ロールが見つかりませんでした: {role_id}")
    else:
        print(f"チャンネルID {channel_id} に対応するロールが設定されていません")

async def remove_role_from_member(member: discord.Member, channel_id: int):
    """
    ボイスチャンネルから退出したユーザーのロールを削除する
    """
    role_id = VOICE_CHANNEL_TO_ROLE.get(channel_id)
    if role_id:
        role = discord.utils.get(member.guild.roles, id=role_id)
        if role:
            await member.remove_roles(role)
            print(f"{member.name} からロール {role.name} を削除しました")
        else:
            print(f"ロールが見つかりませんでした: {role_id}")
    else:
        print(f"チャンネルID {channel_id} に対応するロールが設定されていません")
