from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# Channel Access Token และ Secret Key จาก LINE Developer Console
channel_access_token = os.getenv("nJ8q2oRAeGr6RJu5HaTacbqcSj6V/G6h3+JqybmQOwrKvBc9+fuazOLFtxN+fudlHIz74JfCGVRel7mfchKJ6JKIM5YtNEIAGhERiuQ/RzdMl+4IdKr/7CqazfL4iH/Re28iKweets0hSHtSnNXtCQdB04t89/1O/w1cDnyilFU=")
channel_secret = os.getenv("4786ba44508e1a44a245b5c4833d1eeb")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

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

# ตรวจจับข้อความทั่วไป
@handler.add(event=MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    msg = event.message.text.lower()

    # ห้ามส่งลิงก์ที่ไม่ใช่ของ ohshop
    if ("http://" in msg or "https://" in msg or "line.me" in msg or "qr" in msg or "คิวอาร์" in msg) and "ohshop" not in msg:
        warning = "🚫 กรุณางดส่งลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้องกับร้าน Ohshop"
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=warning)]
            )
        )

# ตรวจจับการแอดบอทเข้ากลุ่ม
@handler.add(event=JoinEvent)
def handle_join(event):
    welcome_msg = "👋 สวัสดีจ้า! บอทนี้จะช่วยดูแลไม่ให้เปลี่ยนชื่อกลุ่มหรือส่งลิงก์ที่ไม่เกี่ยวกับ Ohshop นะจ๊ะ"
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=welcome_msg)]
        )
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
