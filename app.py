import os
import re
from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi,
    ApiClient,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, MemberLeftEvent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# Load environment variables
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
admin_user_id = os.getenv("LINE_BOT_ADMIN_ID")

# Setup API client and handler
configuration = Configuration(access_token=channel_access_token)
api_client = ApiClient(configuration=configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)

# Admins and allowed links
ADMINS = [admin_user_id] if admin_user_id else []
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

# ============ ตรวจจับข้อความและลิงก์ต้องห้าม ============
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    message_text = event.message.text

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

    # ตอบข้อความปกติ
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=f"คุณพิมพ์ว่า: {message_text}")]
        )
    )

# ============ แจ้งเตือนเมื่อมีคนออกจากกลุ่ม ============
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    left_user_ids = [member.user_id for member in event.left.members]
    for uid in left_user_ids:
        for admin_id in ADMINS:
            line_bot_api.push_message(
                PushMessageRequest(
                    to=admin_id,
                    messages=[TextMessage(text=f"📢 สมาชิก {uid} ออกจากกลุ่มแล้ว")]
                )
            )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
