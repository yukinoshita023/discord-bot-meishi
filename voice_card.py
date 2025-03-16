import discord
from PIL import Image, ImageDraw, ImageFont
import io

# ボイスチャンネルIDとテキストチャンネルIDを設定
VOICE_CHANNEL_ID = 860122545381572608  # ここに対象のボイスチャンネルIDを入れる
TEXT_CHANNEL_ID = 1350699397654122517  # ここに投稿するテキストチャンネルのIDを入れる

# ユーザーのメッセージIDを記録するキャッシュ
message_cache = {}

def create_voice_card(username: str) -> io.BytesIO:
    """
    ユーザー名が入った横長のメイシ画像を生成する
    """
    width, height = 400, 100
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # フォントの設定（適切なフォントパスを指定）
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
    
    # `textbbox()` を使ってテキストサイズを取得
    bbox = draw.textbbox((0, 0), username, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    draw.text((text_x, text_y), username, fill=(0, 0, 0), font=font)
    
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
        # VCに参加した場合（新しく入った時のみ）
        if after.channel and after.channel.id == VOICE_CHANNEL_ID:
            if text_channel:
                image = create_voice_card(member.name)
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
