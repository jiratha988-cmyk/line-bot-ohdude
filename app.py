from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    JoinEvent,
    MemberLeftEvent,
    MemberJoinedEvent,
    UnfollowEvent,
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.models import Configuration
import os
import re
import logging

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)

# ENV
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(configuration)

# ตั้งชื่อกลุ่มเดิมที่ต้องการ
DEFAULT_GROUP_NAME = "ลูกค้า Oh!dudeVip (6)"

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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text

    # รีพลายข้อความปกติ
    if event.reply_token:
        # บล็อกลิงก์ไลน์ที่ไม่ใช่ ohshop
        if "line.me" in user_message and "ohshop" not in user_message:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="❌ ห้ามแชร์ลิงก์ LINE อื่นที่ไม่ใช่ของร้าน Oh!shop ในกลุ่มนี้")]
                )
            )
            return

        # รีพลายข้อความปกติ
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"คุณพิมพ์ว่า: {user_message}")]
            )
        )

@handler.add(MemberLeftEvent)
def handle_member_left(event):
    left_user_id = event.left.members[0].user_id
    group_id = event.source.group_id

    try:
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text="🚫 มีคนถูกลบออกจากกลุ่ม")]
            )
        )
    except Exception as e:
        logging.error(f"Error sending member left message: {e}")

@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    joined_user_id = event.joined.members[0].user_id
    group_id = event.source.group_id

    try:
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text="👋 ยินดีต้อนรับเข้าสู่กลุ่ม Oh!dude")]
            )
        )
    except Exception as e:
        logging.error(f"Error sending welcome message: {e}")

@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id

    try:
        # แจ้งว่าเข้าแล้วตั้งชื่อกลับ (ถ้าถูกเปลี่ยน)
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text="🤖 บอทถูกเพิ่มเข้ากลุ่มแล้ว จะคอยดูแลชื่อกลุ่ม และความปลอดภัยให้นะครับ")]
            )
        )
    except Exception as e:
        logging.error(f"Error on join: {e}")

# ตรวจสอบการเปลี่ยนชื่อกลุ่ม — ต้องตั้ง webhook ให้รับ GroupNameUpdateEvent (ยังไม่มีใน v3 SDK แต่ถ้ามี event นี้ใช้ logic ด้านล่างได้)
# สามารถดัดแปลงโดยใช้ cron job หรือ manual API get group summary

if __name__ == "__main__":
    app.run()
