import discord
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from firebase_config import db
from PIL import ImageEnhance

# ボイスチャンネルIDとテキストチャンネルIDのマッピング（ボイスチャンネルID -> テキストチャンネルID）
CHANNEL_PAIRS = {
    847514073964740679: 1350763932427489330,  # モクモク1
    905313176277626880: 1350764187697283093,  # モクモク2
    905313335715713084: 1350764458447863818,  # モクモク3
    860122545381572608: 1350699397654122517,  # ノンビリ1
    905329359244656710: 1350764944890789888,  # ノンビリ2
    905329383630340117: 1350765102957068318,  # ノンビリ3
    847158182257754116: 1350765245773250601,  # ワイワイ1
    905332813853765642: 1350765348994940958,  # ワイワイ2
    905332899421769728: 1350765457451515965,  # ワイワイ3
}

message_cache = {}

def fetch_answers(user_id: int):
    """
    Firestoreから指定したユーザーIDの質問と回答を取得する。
    回答のある質問のみ、指定された順序で返す。
    """
    QUESTIONS_ORDER = [
        "好きな食べ物は？",
        "好きなコンテンツは？",
        "好きなアーティストは？",
        "最近ハマってる趣味は？",
        "私はこんな人"
    ]

    doc_ref = db.collection("users").document(str(user_id))
    doc = doc_ref.get()

    if not doc.exists:
        return []

    data = doc.to_dict()
    ordered_answers = [(q, data[q]) for q in QUESTIONS_ORDER if q in data and data[q]]
    return ordered_answers

def truncate_text(text: str, limit: int) -> str:
    """
    全角＝2文字、半角＝1文字でカウントして制限する。
    超えた分はカット。
    """
    result = ''
    count = 0
    for char in text:
        count += 2 if ord(char) > 255 else 1
        if count > limit:
            break
        result += char
    return result

def create_voice_card(member: discord.Member) -> io.BytesIO:
    """
    ユーザー名とアイコン、質問と回答を入れた名刺画像を生成する
    """
    try:
        image = Image.open("card-images/card-space.png").convert("RGB")
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.2) # 台紙の明るさ変更
    except IOError:
        raise FileNotFoundError("card-images/card-space.png が見つかりません！")

    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 50)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 24)
    except IOError:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 50)
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 24)
        except IOError:
            font_large = font_normal = ImageFont.load_default()

    username = truncate_text(member.display_name, 28)

    avatar_url = member.avatar.url
    avatar = Image.open(io.BytesIO(requests.get(avatar_url).content))
    avatar_size = 100
    avatar = avatar.resize((avatar_size, avatar_size))  

    avatar_x = 30
    avatar_y = 30
    image.paste(avatar, (avatar_x, avatar_y))

    username_x = avatar_x + avatar_size + 30
    username_y = avatar_y + 10
    draw.text((username_x, username_y), username, fill=(255, 255, 255), font=font_large)

    answers = fetch_answers(member.id)

    y_offset = avatar_y + avatar_size + 10
    question_x = 75
    answer_x = 350

    for question, answer in answers:
        answer = truncate_text(answer, 44)
        draw.text((question_x, y_offset), question, fill=(255, 255, 255), font=font_normal)
        draw.text((answer_x, y_offset), answer, fill=(255, 255, 255), font=font_normal)
        y_offset += 50

    square_size = 120  # 正方形のサイズ
    padding = 30  # 左右の余白
    spacing = (width - padding * 2 - square_size * 5) // 4  # 正方形間の間隔
    square_y = height - square_size - 30

    points = fetch_points(member.id)
    
    badge_categories = [
    ("mokumoku", "モクモク"),
    ("nonbiri", "ノンビリ"),
    ("waiwai", "ワイワイ"),
    ]

    for i in range(5):
        square_x = padding + (square_size + spacing) * i
        rect_coords = [(square_x, square_y), (square_x + square_size, square_y + square_size)]
        draw.rectangle(rect_coords, outline=(255, 255, 255), width=3)

        if i < 3:
            category_eng, firestore_key = badge_categories[i]
            point = points.get(firestore_key, 0)

            level = get_badge_level(point)
            badge_path = f"badges/{category_eng}/{category_eng}-{level}.png"

            try:
                badge = Image.open(badge_path).convert("RGBA")
                badge = badge.resize((square_size, square_size))
                image.paste(badge, (square_x, square_y), badge)
            except IOError:
                print(f"バッジ画像の読み込み失敗: {badge_path}")

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

IGNORED_BOT_IDS = [
    1347190643113332766, #ノワール
    1349672366082490378, #リリィ
    1350062244725133374, #レオ　の入退出は無視する
]

async def handle_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id in IGNORED_BOT_IDS:
        return

    if before.channel and before.channel.id in CHANNEL_PAIRS and before.channel != after.channel:
        if member.id in message_cache:
            cached_channel_id, message_id = message_cache.pop(member.id, (None, None))
            text_channel = member.guild.get_channel(cached_channel_id)

            if text_channel and message_id:
                try:
                    message = await text_channel.fetch_message(message_id)
                    await message.delete()
                except discord.NotFound:
                    pass

    if after.channel and after.channel.id in CHANNEL_PAIRS and before.channel != after.channel:
        text_channel_id = CHANNEL_PAIRS[after.channel.id]
        text_channel = member.guild.get_channel(text_channel_id)

        if text_channel:
            try:
                answers = fetch_answers(member.id)

                if not answers:
                    howto_channel_id = 1387334572613697587
                    howto_url = f"https://discord.com/channels/{member.guild.id}/{howto_channel_id}"
                    message = await text_channel.send(
                        content=f"{member.mention} さん、まだ自己紹介が未設定のようです！ `/add_card` コマンドで登録してみてね！登録方法はこちら 👉 {howto_url}"
                    )
                    message_cache[member.id] = (text_channel.id, message.id)
                    return

                image = create_voice_card(member)
                file = discord.File(image, filename="voice_card.png")
                message = await text_channel.send(
                    file=file,
                    content="VCに参加しました！"
                )
                message_cache[member.id] = (text_channel.id, message.id)

            except Exception as e:
                print(f"メイシ生成・送信エラー: {e}")

def get_badge_level(point: int) -> str:
    if point < 6:
        return "iron"
    elif point < 36:
        return "copper"
    elif point < 96:
        return "silver"
    elif point < 240:
        return "gold"
    else:
        return "rainbow"
    
    # ノーマル：~30分
    # カッパー：30分~3時間
    # シルバー：3時間~8時間
    # ゴールド：8時間~20時間
    # レインボー：20時間~

def fetch_points(user_id: int) -> dict:
    doc_ref = db.collection("users").document(str(user_id))
    doc = doc_ref.get()
    if not doc.exists:
        return {}

    data = doc.to_dict()
    return data.get("points", {})