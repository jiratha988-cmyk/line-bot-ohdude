from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    JoinEvent, LeaveEvent
)
import os
import re

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/")
def index():
    return "Bot is running"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ตรวจจับข้อความผิดกฎ
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    user_id = event.source.user_id

    # ลิงก์ทั่วไป
    forbidden_link = re.search(r"(http|https):\/\/", msg)
    # ลิงก์ไลน์
    line_link = re.search(r"(line\.me|line\.me\/R|@|\/ti\/|\/qr)", msg)
    # QR code (เบื้องต้นให้เช็คว่าเขียนว่า QR หรือแนวๆ นี้)
    qr_hint = re.search(r"QR", msg, re.IGNORECASE)
    # เฉพาะของร้าน "Ohshop" ให้ผ่าน
    allowed_shop = re.search(r"ohshop", msg, re.IGNORECASE)

    if (forbidden_link or line_link or qr_hint) and not allowed_shop:
        warning_text = "🚫 ห้ามส่งลิงก์หรือคิวอาร์โค้ดที่ไม่เกี่ยวข้องกับร้าน Ohshop"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=warning_text))
        return

# ตรวจจับการเปลี่ยนชื่อกลุ่มหรือใครมาใหม่
@handler.add(JoinEvent)
def handle_join(event):
    text = "❗️ระบบแจ้งเตือน: มีการเพิ่มบอทเข้ากลุ่ม\nหากมีการเปลี่ยนชื่อกลุ่ม จะมีการบันทึกไว้"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))

@handler.add(LeaveEvent)
def handle_leave(event):
    # กรณีบอทโดนเตะออก ไม่สามารถตอบกลับได้
    pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
