import os
import re
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, MemberLeftEvent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# === โหลดค่าจาก Environment Variables ===
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
admin_user_id = os.getenv("LINE_BOT_ADMIN_ID")  # <- ต้องใส่ใน env ด้วย

# === ตั้งค่า LINE Bot ===
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(configuration)

# === ตั้งค่าผู้ดูแลกลุ่ม ===
ADMINS = [U11143320df8fd84ab1d58e6b341c2c08]

# === ลิงก์ที่อนุญาตให้แชร์ในกลุ่ม (whitelist) ===
ALLOWED_LINK_PREFIXES = [
    "https://rebrand.ly/ohdudeshopv1",
    "https://ohdudeth.com/"
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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    group_id = getattr(event.source, 'group_id', None)
    message_text = event.message.text

    # === เช็คลิงก์ LINE ว่าเป็นของที่อนุญาตไหม ===
    if "https://line.me/" in message_text:
        if not any(message_text.startswith(prefix) for prefix in ALLOWED_LINK_PREFIXES):
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="❌ ห้ามแชร์ลิงก์ LINE ที่ไม่ได้รับอนุญาต!")]
                )
            )
            return

    # === เช็คว่ามีลิงก์น่าสงสัยอื่น ๆ เช่น youtube, tiktok ===
    if re.search(r"https?://", message_text) and not any(message_text.startswith(prefix) for prefix in ALLOWED_LINK_PREFIXES):
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="⚠️ มีลิงก์ที่ไม่ได้รับอนุญาต โปรดตรวจสอบ")]
            )
        )
        return

    # === ตอบกลับข้อความตามปกติ (หากไม่ใช่ลิงก์ต้องห้าม) ===
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=f"คุณพิมพ์ว่า: {message_text}")]
        )
    )

@handler.add(MemberLeftEvent)
def handle_member_left(event):
    left_user_ids = [left_member.user_id for left_member in event.left.members]
    for uid in left_user_ids:
        print(f"สมาชิกออกจากกลุ่ม: {uid}")
        # ส่งแจ้งเตือนแอดมิน
        line_bot_api.push_message(
            to=admin_user_id,
            messages=[TextMessage(text=f"📢 สมาชิก {uid} ออกจากกลุ่มแล้ว")]
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
