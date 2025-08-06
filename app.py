from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration, MessagingApi, ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
import os

app = Flask(__name__)

# โหลดค่าจาก Environment Variables
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

# ตั้งค่า LINE API
config = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(config)
handler = WebhookHandler(channel_secret)

# Endpoint เช็กว่าเซิร์ฟเวอร์ยังทำงาน
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

# Webhook Endpoint
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ✅ Event: เมื่อมีข้อความเข้ามา
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print("🔥 ได้รับข้อความจากผู้ใช้:", event.message.text)

    user_message = event.message.text
    reply_message = TextMessage(text=f"คุณพิมพ์ว่า: {user_message}")
    reply_request = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[reply_message]
    )
    line_bot_api.reply_message(reply_request)

# สำหรับรันบนเครื่อง/Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
