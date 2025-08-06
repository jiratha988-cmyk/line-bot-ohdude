from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, LeaveEvent, JoinEvent
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

GROUP_NAME_DEFAULT = "ชื่อกลุ่มที่ต้องการให้เป็น"

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_msg = event.message.text
    user_id = event.source.user_id
    group_id = event.source.group_id if hasattr(event.source, 'group_id') else None

    # ✅ กันไม่ให้ส่งลิงก์ LINE ที่ไม่ใช่ของแบรนด์ (ohshop)
    if "line.me" in user_msg and "ohshop" not in user_msg:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="❌ ห้ามส่งลิงก์ LINE ที่ไม่ใช่ของ Ohshop นะครับ")]
            )
        )

@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="👋 บอทเข้ากลุ่มแล้วจ้า! จะคอยช่วยดูแลนะครับ")]
        )
    )

@handler.add(LeaveEvent)
def handle_leave(event):
    # บอทโดนเตะออก — ไม่สามารถแจ้งในกลุ่มได้แล้ว
    # ถ้าต้องการแจ้ง admin ต้องใช้ LINE Notify หรือ Push ออกนอกระบบ
    print("❌ บอทโดนเตะออกจากกลุ่ม")

if __name__ == "__main__":
    app.run()
