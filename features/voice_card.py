import discord
from PIL import Image, ImageDraw, ImageFont
import io
import requests
from firebase_config import db
from PIL import ImageEnhance


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
    全角=2文字、半角=1文字でカウントして制限する。
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

def points_to_time_str(pt: int) -> str:
    minutes = pt * 5
    if minutes < 60:
        return f"{minutes}分"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}時間"
    return f"{hours}時間{mins}分"


def create_voice_card(member: discord.Member) -> io.BytesIO:
    answers = fetch_answers(member.id)
    points = fetch_points(member.id)

    card_width = 907
    card_height = 150 + len(answers) * 45 + 20 + 120 + 30 + 30 + 25

    GOLD_ROLE_ID = 1513536556323963110
    RED_PLANET_ROLE_ID = 1543216546086785135
    has_gold_role = any(r.id == GOLD_ROLE_ID for r in member.roles)
    has_red_planet_role = any(r.id == RED_PLANET_ROLE_ID for r in member.roles)

    if has_red_planet_role:
        bg_path = "card-images/card-space-red.png"
    elif has_gold_role:
        bg_path = "card-images/card-space-gold.png"
    else:
        bg_path = "card-images/card-space.png"

    try:
        bg = Image.open(bg_path).convert("RGB")
        bg = bg.resize((card_width, card_height), Image.LANCZOS)
        enhancer = ImageEnhance.Brightness(bg)
        image = enhancer.enhance(0.2 if (has_gold_role or has_red_planet_role) else 0.1)
    except IOError:
        raise FileNotFoundError(f"{bg_path} が見つかりません！")

    draw = ImageDraw.Draw(image)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 50)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 24)
    except IOError:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 50)
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/takao/TakaoPGothic.ttf", 24)
        except IOError:
            font_large = font_normal = ImageFont.load_default()

    # --- Header ---
    username = truncate_text(member.display_name, 28)
    avatar_asset = member.guild_avatar or member.display_avatar
    avatar = Image.open(io.BytesIO(requests.get(avatar_asset.url).content))
    avatar = avatar.resize((100, 100))

    image.paste(avatar, (30, 30))

    username_x = 160
    username_y = 40
    draw.text((username_x, username_y), username, fill=(255, 255, 255), font=font_large)

    wakusei_pt = int(points.get("わくせい", 0))
    username_bbox = draw.textbbox((0, 0), username, font=font_large)
    username_width = username_bbox[2] - username_bbox[0]
    draw.text((username_x + username_width + 20, username_y), f"{wakusei_pt}WP", fill=(255, 220, 80), font=font_large)

    # --- Q&A ---
    y_offset = 150
    for question, answer in answers:
        answer = truncate_text(answer, 44)
        draw.text((75, y_offset), question, fill=(160, 160, 255), font=font_normal)
        draw.text((370, y_offset), answer, fill=(255, 255, 255), font=font_normal)
        y_offset += 45

    # --- Divider ---
    divider_y = y_offset + 10
    draw.line([(30, divider_y), (card_width - 30, divider_y)], fill=(180, 180, 180), width=1)

    # --- Badges (横並び + 下にラベル・値) ---
    BADGE_SLOTS = [
        ("mokumoku",  "モクモク",     "time"),
        ("nonbiri",   "ノンビリ",     "time"),
        ("waiwai",    "ワイワイ",     "time"),
        ("reaction",  "リアクション", "reaction"),
        ("event",     "イベント",     "event"),
    ]

    badge_size = 120
    padding = 20
    spacing = (card_width - padding * 2 - badge_size * 5) // 4
    badge_section_y = divider_y + 15

    for i, (slot_eng, firestore_key, slot_type) in enumerate(BADGE_SLOTS):
        badge_x = padding + (badge_size + spacing) * i
        badge_center_x = badge_x + badge_size // 2

        value = int(points.get(firestore_key, 0))
        if slot_type == "time":
            level = get_badge_level(value)
        elif slot_type == "reaction":
            level = get_reaction_badge_level(value)
        else:
            level = get_event_badge_level(value)

        badge_path = f"badges/{slot_eng}/{slot_eng}-{level}.png"
        try:
            badge = Image.open(badge_path).convert("RGBA")
            badge = badge.resize((badge_size, badge_size))
            image.paste(badge, (badge_x, badge_section_y), badge)
        except IOError:
            pass

        name_bbox = draw.textbbox((0, 0), firestore_key, font=font_normal)
        name_w = name_bbox[2] - name_bbox[0]
        draw.text((badge_center_x - name_w // 2, badge_section_y + badge_size + 6), firestore_key, fill=(255, 255, 255), font=font_normal)

        value_str = points_to_time_str(value) if slot_type == "time" else f"{value}回"
        val_bbox = draw.textbbox((0, 0), value_str, font=font_normal)
        val_w = val_bbox[2] - val_bbox[0]
        draw.text((badge_center_x - val_w // 2, badge_section_y + badge_size + 34), value_str, fill=(200, 200, 200), font=font_normal)

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes


def get_badge_level(point: int) -> str:
    if point < 12:
        return "iron"
    elif point < 300:
        return "copper"
    elif point < 1000:
        return "silver"
    elif point < 3000:
        return "gold"
    else:
        return "rainbow"

def get_reaction_badge_level(value: int) -> str:
    if value < 10:
        return "iron"
    elif value < 100:
        return "copper"
    elif value < 300:
        return "silver"
    elif value < 1000:
        return "gold"
    else:
        return "rainbow"
    
def get_event_badge_level(value: int) -> str:
    if value <= 0:
        return "iron"
    elif value == 1:
        return "copper"
    elif value == 2:
        return "silver"
    elif value == 3:
        return "gold"
    else:
        return "rainbow"

def fetch_points(user_id: int) -> dict:
    doc_ref = db.collection("users").document(str(user_id))
    doc = doc_ref.get()
    if not doc.exists:
        return {}

    data = doc.to_dict()
    return data.get("points", {})