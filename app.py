from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi, ReplyMessageRequest, TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, MemberLeftEvent,
    JoinEvent, LeaveEvent, GroupNameUpdateEvent
)
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# === ตั้งค่าชื่อกลุ่มที่ต้องการล็อกไว้ ===
LOCKED_GROUP_NAME = "ลูกค้าOh!dudeVip (6)"
OHSHOP_KEYWORD = "ohshop"  # ป้องกันลิงก์ไลน์อื่น ๆ ที่ไม่ใช่ของ ohshop

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ====== Event: รับข้อความแล้วตอบกลับ ======
@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        user_message = event.message.text
        reply = f"คุณพิมพ์ว่า: {user_message}"

        # ตรวจสอบลิงก์ไลน์ที่ไม่ใช่ ohshop แล้วเตะออก
        if "line.me" in user_message and OHSHOP_KEYWORD not in user_message.lower():
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="❌ ห้ามส่งลิงก์ไลน์อื่นในกลุ่ม")]
                )
            )
            try:
                line_bot_api.leave_group(event.source.group_id)
            except:
                pass
            return

        # ตอบข้อความปกติ
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

# ====== Event: เปลี่ยนชื่อกลุ่ม ======
@handler.add(GroupNameUpdateEvent)
def handle_group_rename(event):
    old_name = event.source.group_id
    new_name = event.group_name
    if new_name != LOCKED_GROUP_NAME:
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"⚠️ กลุ่มถูกเปลี่ยนชื่อเป็น '{new_name}'\nขออนุญาตเปลี่ยนกลับเป็น '{LOCKED_GROUP_NAME}'")]
                )
            )
            # เปลี่ยนชื่อกลับ (ต้องมีสิทธิ์ admin ในกลุ่ม)
            line_bot_api.update_group_name(event.source.group_id, LOCKED_GROUP_NAME)
        except Exception as e:
            print(f"❌ เปลี่ยนชื่อกลับไม่สำเร็จ: {e}")

# ====== Event: มีคนโดนเตะออก ======
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="👋 มีสมาชิกถูกลบออกจากกลุ่ม")]
        )
    )

# ====== Event: มีคนเข้ากลุ่ม (บอทก็เช่นกัน) ======
@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="สวัสดีค่ะ! บอทพร้อมดูแลความเรียบร้อยในกลุ่มนี้ 😎")]
        )
    )

if __name__ == "__main__":
    app.run()
