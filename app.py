from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent,
    MemberLeftEvent, JoinEvent, LeaveEvent,
    GroupNameUpdateEvent
)
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# ====== ใส่ Token และ Secret จาก LINE Developer Console ======
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# === ค่าเริ่มต้น ===
ORIGINAL_GROUP_NAME = "ลูกค้าOh!dudeVip"
ALLOWED_LINE_DOMAIN = "ohshop"  # ใส่ชื่อแบรนด์ของคุณที่อนุญาตให้แชร์ link ได้

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ================== Event: รับข้อความ =====================
@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        text = event.message.text.lower()

        # 🔒 Block ลิงก์ LINE ที่ไม่ใช่ของแบรนด์
        if "line.me" in text and ALLOWED_LINE_DOMAIN not in text:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="❌ ห้ามส่งลิงก์ไลน์ที่ไม่ใช่ของแบรนด์ในกลุ่มนี้")]
                )
            )
            return

        # ✅ Echo ข้อความกลับ
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="คุณพิมพ์ว่า: " + event.message.text)]
            )
        )

# ================== Event: เปลี่ยนชื่อกลุ่ม =====================
@handler.add(GroupNameUpdateEvent)
def handle_group_rename(event):
    new_name = event.group_name
    if new_name != ORIGINAL_GROUP_NAME:
        # แจ้งเตือน และเปลี่ยนชื่อกลับ
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"⚠️ มีการเปลี่ยนชื่อกลุ่มเป็น '{new_name}'\nขอเปลี่ยนกลับเป็น '{ORIGINAL_GROUP_NAME}' นะครับ")]
            )
        )
        # เปลี่ยนชื่อกลุ่มกลับ (แต่ตอนนี้ LINE ยังไม่เปิดให้ bot เปลี่ยนชื่อ group ได้จริง ต้องใช้ token พิเศษ)
        # ถ้ามีสิทธิ์ admin และ API รองรับ อาจใช้ MessagingApi().update_group_name(group_id, name)

# ================== Event: มีคนโดนเตะออก =====================
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="👋 มีสมาชิกออกจากกลุ่ม หรืออาจถูกเตะออก")]
        )
    )

# ================== Event: Bot ถูกเชิญเข้ากลุ่ม =====================
@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="สวัสดีครับ! ผมคือ Oh!dude Bot 😎")]
        )
    )

# =========== Main ============
if __name__ == "__main__":
    app.run(port=5000)
