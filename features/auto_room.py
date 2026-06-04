import discord
from features.voice_card import create_voice_card, fetch_answers

FREE_CREATION_CHANNELS = {
    1512049216816545864: "モクモク",
    1512052757375484074: "ノンビリ",
    1512052850925109339: "ワイワイ",
}

# {vc_id: {"creator_id": int, "messages": {member_id: message_id}}}
auto_rooms: dict = {}


async def _post_meishi(member: discord.Member, vc: discord.VoiceChannel):
    try:
        answers = fetch_answers(member.id)
        if not answers:
            howto_channel_id = 1387334572613697587
            howto_url = f"https://discord.com/channels/{member.guild.id}/{howto_channel_id}"
            msg = await vc.send(
                content=f"{member.mention} さん、まだ自己紹介が未設定です！ `/add_card` で登録してみてね！登録方法はこちら 👉 {howto_url}"
            )
        else:
            image = create_voice_card(member)
            msg = await vc.send(file=discord.File(image, filename="voice_card.png"), content="VCに参加しました！")
        return msg.id
    except Exception as e:
        print(f"メイシ投稿エラー: {e}")
        return None


async def handle_auto_room(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return

    # 自動作成部屋から退出した場合
    if before.channel and before.channel.id in auto_rooms:
        room = auto_rooms[before.channel.id]

        if member.id in room["messages"]:
            try:
                msg = await before.channel.fetch_message(room["messages"].pop(member.id))
                await msg.delete()
            except discord.NotFound:
                pass

        # Botを除いて誰もいなくなったら削除
        remaining = [m for m in before.channel.members if not m.bot]
        if not remaining:
            try:
                await before.channel.delete()
            except discord.NotFound:
                pass
            del auto_rooms[before.channel.id]

    # 自由作成VCに入った場合
    if after.channel and after.channel.id in FREE_CREATION_CHANNELS:
        category = after.channel.category
        category_name = FREE_CREATION_CHANNELS[after.channel.id]

        new_vc = await member.guild.create_voice_channel(
            name=f"{member.display_name}/{category_name}/部屋",
            category=category,
        )

        auto_rooms[new_vc.id] = {
            "creator_id": member.id,
            "messages": {member.id: None},  # 2重投稿防止のプレースホルダー
        }

        await member.move_to(new_vc)

        msg_id = await _post_meishi(member, new_vc)
        if msg_id:
            auto_rooms[new_vc.id]["messages"][member.id] = msg_id
        return

    # 既存の自動作成部屋に入った場合
    if after.channel and after.channel.id in auto_rooms:
        room = auto_rooms[after.channel.id]

        if member.id not in room["messages"]:
            msg_id = await _post_meishi(member, after.channel)
            if msg_id:
                room["messages"][member.id] = msg_id
