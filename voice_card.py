import discord
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import sqlite3
from PIL import ImageEnhance

# ボイスチャンネルIDとテキストチャンネルIDを設定
VOICE_CHANNEL_ID = 905313176277626880  # ここに対象のボイスチャンネルIDを入れる
TEXT_CHANNEL_ID = 1350764187697283093  # ここに投稿するテキストチャンネルのIDを入れる

# ユーザーのメッセージIDを記録するキャッシュ
message_cache = {}

def fetch_answers(user_id: int):
    """
    指定したユーザーIDの質問と回答をanswers.dbから取得する
    """
    conn = sqlite3.connect("answers.db")
    cursor = conn.cursor()

    # データ取得
    cursor.execute("SELECT question, answer FROM answers WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()

    conn.close()
    return data  # [(質問1, 答え1), (質問2, 答え2), ...]

def create_voice_card(member: discord.Member) -> io.BytesIO:
    """
    ユーザー名とアイコン、質問と回答を入れた名刺画像を生成する
    """
    try:
        # 背景画像を開く
        image = Image.open("card-images/card-space.png").convert("RGB")

        # 台紙の明るさを調整（値を 0.7 にすると30% 暗くなる）
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.4)  # 1.0 より小さい値で暗くする
    except IOError:
        raise FileNotFoundError("card-images/card-space.png が見つかりません！")

    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # 日本語対応フォントを設定
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 24)  # Noto Sans CJK
    except IOError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 24)  # Takao Pゴシック
        except IOError:
            font = ImageFont.load_default()  # どれもなければデフォルトフォント

    # ユーザー名取得
    username = member.display_name

    # ユーザー名描画（白色）
    draw.text((20, 20), f"ユーザー名: {username}", fill=(255, 255, 255), font=font)

    # ユーザーの回答データを取得
    answers = fetch_answers(member.id)

    # 質問と回答を描画（白色）
    y_offset = 60  # 描画開始Y座標
    for question, answer in answers:
        text = f"Q: {question}\nA: {answer}"
        draw.text((20, y_offset), text, fill=(255, 255, 255), font=font)  # 白文字
        y_offset += 50  # 次の行へ

    # ユーザーアイコン取得
    avatar_url = member.avatar.url
    avatar = Image.open(io.BytesIO(requests.get(avatar_url).content))
    avatar = avatar.resize((50, 50))  # アイコンのサイズ調整
    image.paste(avatar, (width - 70, 20))  # アイコンを右上に配置

    # 画像をバイトデータに変換
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


async def handle_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """
    指定のボイスチャンネルにメンバーが入ったときにメイシを送信し、
    退出したら削除する
    """
    text_channel = member.guild.get_channel(TEXT_CHANNEL_ID)

    # ボイスチャンネルに新しく入った場合
    if before.channel != after.channel:
        # VCに参加した場合
        if after.channel and after.channel.id == VOICE_CHANNEL_ID:
            if text_channel:
                image = create_voice_card(member)
                file = discord.File(image, filename="voice_card.png")
                message = await text_channel.send(file=file, content=f"{member.mention} がVCに参加しました！")

                # メッセージIDを記録
                message_cache[member.id] = message.id

        # VCから退出した場合
        elif before.channel and before.channel.id == VOICE_CHANNEL_ID and after.channel is None:
            if text_channel:
                message_id = message_cache.pop(member.id, None)
                if message_id:
                    try:
                        message = await text_channel.fetch_message(message_id)
                        await message.delete()
                    except discord.NotFound:
                        pass  # 既に削除されていた場合は無視
