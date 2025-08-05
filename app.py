from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# ตอบกลับข้อความทั่วไป
@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        msg = event.message.text.lower()
        reply = f"บอทได้ยินว่า: '{msg}'"
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

# ตรวจจับลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้อง
@handler.add(MessageEvent)
def handle_text(event):
    if isinstance(event.message, TextMessageContent):
        msg = event.message.text.lower()
        if ("http://" in msg or "https://" in msg or "line.me" in msg or "qr" in msg or "คิวอาร์" in msg) and "ohshop" not in msg:
            warning = "🚫 กรุณางดส่งลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้องกับร้าน Ohshop"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=warning)]
                )
            )

# ตอนบอทถูกเชิญเข้ากลุ่ม
@handler.add(JoinEvent)
def handle_join(event):
    welcome_msg = "👋 สวัสดีจ้า! บอทนี้จะช่วยดูแลไม่ให้เปลี่ยนชื่อกลุ่มหรือส่งลิงก์ที่ไม่เกี่ยวกับ Ohshop นะจ๊ะ"
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=welcome_msg)]
        )
    )

# ตรวจจับ event ทุกประเภทเพื่อเช็กว่าอาจมีการเปลี่ยนชื่อกลุ่ม
@handler.default()
def handle_all_events(event):
    # ใช้เช็กว่า event ที่เกิดขึ้นเป็นแบบ update หรือ generic อื่น ๆ
    if hasattr(event.source, "type") and event.source.type == "group":
        if event.type == "update":
            warning = "⚠️ ห้ามเปลี่ยนชื่อกลุ่ม กรุณาเปลี่ยนกลับเป็น: Ohshop Only ✅"
            try:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=warning)]
                    )
                )
            except Exception as e:
                print("❌ แจ้งเตือนการเปลี่ยนชื่อกลุ่มล้มเหลว:", e)

# webhook route
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
