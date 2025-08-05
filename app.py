from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import re

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/")
def index():
    return "Bot is running..."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ฟังค์ชันตรวจ link
def is_bad_link(text):
    if "http" in text or "https" in text:
        if "ohshop.line.me" not in text:
            return True
    return False

# ตรวจเปลี่ยนชื่อกลุ่ม
@handler.add(SourceGroup, event=JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="สวัสดีจ้า บอทจะช่วยดูแลกลุ่มนี้ไม่ให้ใครเปลี่ยนชื่อกลุ่มหรือส่งลิงค์ร้านอื่นนะจ๊ะ ❤️")
    )

@handler.add(MemberJoinedEvent)
def welcome(event):
    for member in event.joined.members:
        if isinstance(member, SourceUser):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ยินดีต้อนรับ {member.user_id} จ้า ✨")
            )

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text

    # ตรวจลิงก์ต้องห้าม
    if is_bad_link(text):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขออภัย ไม่อนุญาตให้ส่งลิงก์ร้านอื่นในกลุ่มนี้ค่ะ 🚫")
        )
        return

    # ตรวจคำว่า line.me หรือ QR
    if re.search(r"(line\.me|qr code|qr|add me|แอดไลน์)", text, re.IGNORECASE):
        if "ohshop" not in text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ขออภัย ไม่อนุญาตให้แปะไลน์อื่นในกลุ่มนี้ค่ะ ❌")
            )
            return

@handler.add(GroupNameChangedEvent)
def handle_group_name_change(event):
    group_id = event.source.group_id
    original_name = "กลุ่มของร้าน Ohshop"
    line_bot_api.set_group_name(group_id, original_name)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ห้ามเปลี่ยนชื่อกลุ่มนะคะ ชื่อถูกตั้งกลับแล้วจ้า 🔒")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
