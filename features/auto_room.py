import random
import discord
from features.voice_card import create_voice_card, fetch_answers

FREE_CREATION_CHANNELS = {
    1512049216816545864: "モクモク",
    1512052757375484074: "ノンビリ",
    1512052850925109339: "ワイワイ",
}

STATIC_VOICE_CHANNELS = {
    847514073964740679,  # モクモク
    860122545381572608,  # ノンビリ
    847158182257754116,  # ワイワイ
}

LOCATIONS = [
    ("🌾", "草原"),
    ("🌲", "森"),
    ("🌷", "花畑"),
    ("🌴", "オアシス"),
    ("🏜️", "砂漠"),
    ("🏞️", "渓谷"),
    ("🌋", "火山"),
    ("🗻", "山"),
    ("🏖️", "砂浜"),
    ("🏔️", "氷河"),
    ("🏝️", "孤島"),
    ("🌊", "海"),
    ("🏙️", "都市"),
    ("⛲", "広場"),
    ("🎪", "市場"),
    ("⚓", "港町"),
    ("🏮", "路地裏"),
    ("📚", "図書館"),
    ("☕", "喫茶店"),
    ("🎡", "遊園地"),
    ("🏕️", "集落"),
    ("🌅", "浜辺"),
    ("🥋", "道場"),
    ("🔭", "天文台"),
    ("📡", "基地"),
    ("🌌", "空庭"),
    ("☄️", "クレーター"),
    ("🚀", "発射場"),
    ("💠", "洞窟"),
    ("🔬", "研究所"),
    ("🏛️", "遺跡"),
    ("🎈", "浮島"),
    ("🪴", "温室"),
    ("🪽", "桃源郷"),
    ("🍐", "果樹園"),
]

CATEGORY_HIRAGANA = {
    "モクモク": "もくもく",
    "ノンビリ": "のんびり",
    "ワイワイ": "わいわい",
}

# {vc_id: {"creator_id": int, "messages": {member_id: message_id}}}
auto_rooms: dict = {}

# {(channel_id, member_id): message_id}
static_messages: dict = {}


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

    before_id = before.channel.id if before.channel else None
    after_id = after.channel.id if after.channel else None
    if before_id == after_id:
        return

    # 定常VCから退出した場合
    if before.channel and before.channel.id in STATIC_VOICE_CHANNELS:
        key = (before.channel.id, member.id)
        if key in static_messages:
            try:
                msg = await before.channel.fetch_message(static_messages.pop(key))
                await msg.delete()
            except discord.NotFound:
                pass

    # 定常VCに入った場合
    if after.channel and after.channel.id in STATIC_VOICE_CHANNELS:
        msg_id = await _post_meishi(member, after.channel)
        if msg_id:
            static_messages[(after.channel.id, member.id)] = msg_id

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
        emoji, location = random.choice(LOCATIONS)
        room_name = f"{emoji}{CATEGORY_HIRAGANA[category_name]}の{location}"

        new_vc = await member.guild.create_voice_channel(
            name=room_name,
            category=category,
        )

        auto_rooms[new_vc.id] = {
            "creator_id": member.id,
            "messages": {member.id: None},  # 2重投稿防止のプレースホルダー
        }

        await member.move_to(new_vc)

        await new_vc.send(f"**{member.display_name}** さんが {room_name} を作成しました！")
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
