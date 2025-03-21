import discord
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from firebase_config import db
from PIL import ImageEnhance

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

# ユーザーのメッセージIDを記録するキャッシュ
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
    # 順番通りかつ回答があるものだけを抽出
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
        # 全角なら +2、それ以外は +1
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
        # 背景画像を開く
        image = Image.open("card-images/card-space.png").convert("RGB")

        # 台紙の明るさを調整（値を 0.7 にすると30% 暗くなる）
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.2)  # 1.0 より小さい値で暗くする
    except IOError:
        raise FileNotFoundError("card-images/card-space.png が見つかりません！")

    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # 日本語対応フォント（ユーザー名は大きく 50px）
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 50)  # Noto Sans CJK
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 24)  # 通常テキスト
    except IOError:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 50)  # Takao Pゴシック
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 24)
        except IOError:
            font_large = font_normal = ImageFont.load_default()  # どれもなければデフォルトフォント

    # ユーザー名取得
    username = truncate_text(member.display_name, 28)

    # ユーザーアイコン取得
    avatar_url = member.avatar.url
    avatar = Image.open(io.BytesIO(requests.get(avatar_url).content))
    avatar_size = 100  # アイコンのサイズを 100x100 にする
    avatar = avatar.resize((avatar_size, avatar_size))  

    # アイコンの描画位置（左上に配置）
    avatar_x = 30
    avatar_y = 30
    image.paste(avatar, (avatar_x, avatar_y))

    # ユーザー名の描画位置（アイコンの右側に配置）
    username_x = avatar_x + avatar_size + 30  # アイコンの右 + 30px の間隔
    username_y = avatar_y + 10  # アイコン +10px の位置
    draw.text((username_x, username_y), username, fill=(255, 255, 255), font=font_large)

    # ユーザーの回答データを取得
    answers = fetch_answers(member.id)

    # 質問と回答を描画（白色）
    y_offset = avatar_y + avatar_size + 10  # アイコンの下に余白を開けて描画
    question_x = 75  # 質問を揃えるX座標
    answer_x = 350  # 答えを質問の横に配置

    for question, answer in answers:
        answer = truncate_text(answer, 44)  # 全角22文字 = 44カウント
        draw.text((question_x, y_offset), question, fill=(255, 255, 255), font=font_normal)
        draw.text((answer_x, y_offset), answer, fill=(255, 255, 255), font=font_normal)
        y_offset += 50

    # **下側に正方形を5つ描画**
    square_size = 120  # 正方形のサイズ
    padding = 30  # 左右の余白
    spacing = (width - padding * 2 - square_size * 5) // 4  # 正方形間の間隔
    square_y = height - square_size - 30  # 下から20pxの位置

    for i in range(5):
        square_x = padding + (square_size + spacing) * i
        draw.rectangle(
            [(square_x, square_y), (square_x + square_size, square_y + square_size)],
            outline=(255, 255, 255),  # 白い枠線
            width=3  # 枠線の太さ
        )

    # 画像をバイトデータに変換
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes




async def handle_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """
    ボイスチャンネルに入った時、対応するテキストチャンネルへメイシ画像を送信し、
    出た時や移動時に以前のメイシを削除する
    """

    # === 1. 退出・移動時の削除処理（beforeが登録チャンネルの場合）
    if before.channel and before.channel.id in CHANNEL_PAIRS:
        if member.id in message_cache:
            cached_channel_id, message_id = message_cache.pop(member.id, (None, None))
            text_channel = member.guild.get_channel(cached_channel_id)

            if text_channel and message_id:
                try:
                    message = await text_channel.fetch_message(message_id)
                    await message.delete()
                except discord.NotFound:
                    pass  # すでに削除されていた場合は無視

    # === 2. 参加・移動時のメイシ送信処理（afterが登録チャンネルの場合）
    if after.channel and after.channel.id in CHANNEL_PAIRS:
        text_channel_id = CHANNEL_PAIRS[after.channel.id]
        text_channel = member.guild.get_channel(text_channel_id)

        if text_channel:
            try:
                image = create_voice_card(member)
                file = discord.File(image, filename="voice_card.png")
                message = await text_channel.send(file=file, content=f"{member.mention} がVCに参加しました！")

                # 新しいメッセージを記録
                message_cache[member.id] = (text_channel.id, message.id)
            except Exception as e:
                print(f"メイシ生成・送信エラー: {e}")