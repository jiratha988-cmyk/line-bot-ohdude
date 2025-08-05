from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent
from linebot.v3.exceptions import InvalidSignatureError
import os

app = Flask(__name__)

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

EXPECTED_GROUP_NAME = "ลูกค้าOh!DudeVip"  # 👈 ตั้งชื่อกลุ่มที่ต้องการให้คงไว้

@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        msg = event.message.text.lower()

        # 🚫 ตรวจจับลิงก์ที่ไม่เกี่ยวกับ ohshop
        if ("http://" in msg or "https://" in msg or "line.me" in msg or "qr" in msg or "คิวอาร์" in msg) and "ohshop" not in msg:
            warning = "🚫 กรุณางดส่งลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้องกับร้าน Ohshop"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=warning)]
                )
            )

        # ✅ ตรวจสอบชื่อกลุ่ม
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
                print("❌ ดึงชื่อกลุ่มไม่สำเร็จ:", e)

@handler.add(JoinEvent)
def handle_join(event):
    welcome_msg = "👋 สวัสดีจ้า! บอทนี้จะช่วยดูแลไม่ให้เปลี่ยนชื่อกลุ่มหรือส่งลิงก์ที่ไม่เกี่ยวกับ OhShop นะจ๊ะ"
    line_bot_api.reply_message
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
