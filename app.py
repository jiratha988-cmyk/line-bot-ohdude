import os
import re
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, MemberLeftEvent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# โหลดค่าจาก Environment Variables
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
admin_user_id = os.getenv("LINE_BOT_ADMIN_ID")  # ใส่ใน Render ด้วย

# ตั้งค่า LINE Bot
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(configuration)

# ผู้ดูแลกลุ่ม (ใช้สำหรับส่งแจ้งเตือนเวลา member ออกจากกลุ่ม)
ADMINS = [admin_user_id] if admin_user_id else []

# ลิงก์ที่อนุญาตให้โพสต์ได้
ALLOWED_LINK_PREFIXES = [
    "https://rebrand.ly/ohdudeshopv1",
    "https://ohdudeth.com/",
    "https://lin.ee/"
]

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# =============================
# ตรวจจับข้อความและลิงก์ต้องห้าม
# =============================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    try:
        message_text = event.message.text
        user_id = getattr(event.source, 'user_id', None)
        group_id = getattr(event.source, 'group_id', None)
        room_id = getattr(event.source, 'room_id', None)

        print("===== [DEBUG] LINE MESSAGE EVENT =====")
        print(f"user_id: {user_id}")
        print(f"group_id: {group_id}")
        print(f"room_id: {room_id}")
        print(f"message_text: {message_text}")
        print("=======================================")

        # ตรวจจับ URL ในข้อความ
        urls = re.findall(r"https?://[^\s]+", message_text)
        for url in urls:
            if not any(url.startswith(prefix) for prefix in ALLOWED_LINK_PREFIXES):
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="❌ ลิงก์นี้ไม่ได้รับอนุญาตในกลุ่ม!")]
                    )
                )
                return

        # ตอบกลับข้อความปกติ
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"คุณพิมพ์ว่า: {message_text}")]
            )
        )

    except Exception as e:
        print("⚠️ Error in handle_message:", e)

# =============================
# แจ้งเตือนเมื่อมีคนออกจากกลุ่ม
# =============================
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    try:
        left_user_ids = [member.user_id for member in event.left.members]
        for uid in left_user_ids:
            for admin_id in ADMINS:
                line_bot_api.push_message(
                    PushMessageRequest(
                        to=admin_id,
                        messages=[
                            TextMessage(text=f"📢 สมาชิก {uid} ออกจากกลุ่มแล้ว")
                        ]
                    )
                )
    except Exception as e:
        print("⚠️ Error in handle_member_left:", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
