from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, PushMessageRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent, MemberLeftEvent
from linebot.v3.exceptions import InvalidSignatureError
import os
import random

app = Flask(__name__)

# ENV variables
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# ตั้งค่าชื่อกลุ่มที่ถูกต้องและ Group ID จริง
EXPECTED_GROUP_NAME = "ลูกค้าOh!dudeVip"
EXPECTED_GROUP_ID = "YOUR_REAL_GROUP_ID_HERE"  # <--- ใส่ groupId ที่ได้จาก Developer Console

# ข้อความต้อนรับแบบสุ่ม
greetings = [
    "👋 ยินดีต้อนรับน้าาา!",
    "สวัสดีจ้า เข้ากลุ่ม Oh!dude ต้องเฮฮา 💨",
    "🥳 ยินดีที่ได้รู้จักจ้า มาดูดดื่มกันอย่างปลอดภัย"
]

@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        msg = event.message.text.lower()

        # 🚫 บล็อกลิงก์ที่ไม่น่าไว้ใจ
        if any(x in msg for x in ["http", "https", "line.me", "bit.ly", "tinyurl", "qr", "คิวอาร์", "แอดไลน์", "t.me", "ig.me", "@"]) and "ohshop" not in msg:
            warning = "🚫 กรุณางดส่งลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้องกับร้าน Ohshop"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=warning)]
                )
            )

        # ⚠️ ตรวจสอบชื่อกลุ่มและ Group ID
        if event.source.type == "group":
            try:
                group_id = event.source.group_id

                # ตรวจ group_id ปลอม → ให้ออกจากกลุ่ม
                if group_id != EXPECTED_GROUP_ID:
                    line_bot_api.leave_group(group_id)
                    return

                group_summary = line_bot_api.get_group_summary(group_id)
                current_name = group_summary.group_name

                if current_name != EXPECTED_GROUP_NAME:
                    alert = f"⚠️ ระบบตรวจพบว่าชื่อกลุ่มถูกเปลี่ยน กรุณาเปลี่ยนกลับเป็น: {EXPECTED_GROUP_NAME}"
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=alert)]
                        )
                    )
            except Exception as e:
                print("❌ ดึงชื่อกลุ่มไม่สำเร็จ:", e)

        # ✨ ฟีเจอร์ /help
        if msg == "/help":
            help_text = (
                "🤖 คำสั่งใช้งานของบอท:\n"
                "• ป้องกันลิงก์ไม่เกี่ยวข้อง\n"
                "• แจ้งเตือนชื่อกลุ่มถูกเปลี่ยน\n"
                "• แจ้งเมื่อสมาชิกออกจากกลุ่ม\n"
                "• ต้อนรับสมาชิกใหม่แบบสุ่ม\n"
                "• ตรวจสอบกลุ่มปลอม\n"
                "พิมพ์ /help ได้ตลอดนะจ๊ะ ❤️"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=help_text)]
                )
            )

@handler.add(MemberLeftEvent)
def handle_member_left(event):
    try:
        group_id = event.source.group_id
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text="⚠️ แจ้งเตือน: มีสมาชิกออกจากกลุ่ม อาจจะโดนเตะหรือออกเอง")]
            )
        )
    except Exception as e:
        print("❌ แจ้งเตือนคนออกกลุ่มไม่สำเร็จ:", e)

@handler.add(JoinEvent)
def handle_join(event):
    welcome_msg = random.choice(greetings)
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=welcome_msg)]
        )
    )

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
