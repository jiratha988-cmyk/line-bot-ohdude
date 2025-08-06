from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    JoinEvent, MemberLeftEvent, GroupNameChangeEvent
)
import os
import re

app = Flask(__name__)

# ใช้ ENV variables
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# ตั้งชื่อกลุ่มเดิมของร้านที่ต้องการใช้
DEFAULT_GROUP_NAME = "ลูกค้าOh!dudeVip"
# ลิงก์ที่อนุญาต เช่น lin.ee/vZzQErv
ALLOWED_LINKS = ["lin.ee/vZzQErv", "line.me/R/ti/p/@ohshop"]

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

# ✅ กรณีถูกเตะออกจากกลุ่ม
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    line_bot_api.push_message(
        event.source.group_id,
        TextSendMessage(text="🚨 มีคนโดนเตะออกจากกลุ่มนะ ตรวจสอบได้เลย!")
    )

# ✅ กรณีมีคนเปลี่ยนชื่อกลุ่ม
@handler.add(GroupNameChangeEvent)
def handle_group_rename(event):
    if event.group_name != DEFAULT_GROUP_NAME:
        line_bot_api.set_group_name(event.source.group_id, DEFAULT_GROUP_NAME)
        line_bot_api.push_message(
            event.source.group_id,
            TextSendMessage(text=f"🚫 เปลี่ยนชื่อกลุ่มไม่ได้! ตั้งกลับเป็น '{DEFAULT_GROUP_NAME}' แล้ว")
        )

# ✅ กรณีมีการส่งข้อความที่เป็นลิงก์
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    # ตรวจจับลิงก์
    urls = re.findall(r'https?://[^\s]+', text)
    for url in urls:
        if not any(allowed in url for allowed in ALLOWED_LINKS):
            # แจ้งเตือนในกลุ่ม
            line_bot_api.push_message(
                event.source.group_id,
                TextSendMessage(text=f"⚠️ ห้ามส่งลิงก์แปลก ๆ ในกลุ่ม: {url}")
            )
            return

    # ไม่ต้องตอบกลับถ้าไม่ใช่ลิงก์นอกแบรนด์
    return
