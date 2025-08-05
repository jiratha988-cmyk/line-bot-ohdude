from flask import Flask, request, abort
from linebot.v3.webhooks import WebhookHandler, MessageEvent, TextMessageContent, JoinEvent, MemberLeftEvent
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest, TextMessage, PushMessageRequest
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# ✅ ใช้ Configuration แทนการส่ง token ตรง ๆ
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

config = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(config)

EXPECTED_GROUP_NAME = "ลูกค้าOh!dudeVip"  # 👈 ชื่อกลุ่มที่ต้องการให้คงไว้

# 🚫 บล็อกลิงก์ + ตรวจชื่อกลุ่ม
@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        msg = event.message.text.lower()

        # ตรวจลิงก์ที่ไม่เกี่ยวข้อง
        if ("http://" in msg or "https://" in msg or "line.me" in msg or "qr" in msg or "คิวอาร์" in msg) and "ohshop" not in msg:
            warning = "🚫 กรุณางดส่งลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้องกับร้าน Ohshop"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=warning)]
                )
            )

        # ✅ ตรวจชื่อกลุ่ม
        if event.source.type == "group":
            try:
                group_id = event.source.group_id
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
                print("❌ ไม่สามารถดึงชื่อกลุ่มได้:", e)

# 👋 เมื่อบอทถูกเชิญเข้ากลุ่ม
@handler.add(JoinEvent)
def handle_join(event):
    welcome_msg = "👋 สวัสดีจ้า! บอทนี้จะช่วยดูแลไม่ให้เปลี่ยนชื่อกลุ่มหรือส่งลิงก์ที่ไม่เกี่ยวกับ Ohshop นะจ๊ะ"
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=welcome_msg)]
        )
    )

# 👤 มีคนออกจากกลุ่ม
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    try:
        group_id = event.source.group_id
        alert = "⚠️ แจ้งเตือน: มีสมาชิกออกจากกลุ่ม อาจจะโดนเตะหรือออกเอง"
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text=alert)]
            )
        )
    except Exception as e:
        print("❌ แจ้งเตือนคนออกจากกลุ่มล้มเหลว:", e)

# -------------------------------
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
