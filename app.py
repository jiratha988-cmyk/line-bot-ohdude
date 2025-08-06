from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, JoinEvent, LeaveEvent,
    MemberLeftEvent, MemberJoinedEvent, GroupNameUpdateEvent
)
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# ใช้ ENV จาก Render (หรือใส่ตรงๆ ก็ได้)
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# กำหนดชื่อกลุ่มเริ่มต้น (ใช้จริงอาจต้อง fetch มาก่อน)
DEFAULT_GROUP_NAME = "Oh!dude Group"
ADMINS = ['YOUR_ADMIN_USER_ID1', 'YOUR_ADMIN_USER_ID2']  # ใส่ User ID จริง

# -------- HOME ----------
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

# -------- CALLBACK ----------
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# -------- ฟังก์ชันตรวจลิงก์ที่ไม่ใช่ของ OhShop ----------
def is_unauthorized_link(text):
    if "line.me" in text or "lin.ee" in text:
        if "ohshop" not in text.lower():
            return True
    return False

# -------- ตรวจลิงก์ทั่วไปหรือคิวอาร์ ----------
def contains_generic_link(text):
    pattern = r"(https?://[^\s]+)"
    return bool(re.search(pattern, text))

# -------- Message Event ----------
@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id
    group_id = event.source.group_id
    text = ""

    if isinstance(event.message, TextMessageContent):
        text = event.message.text

    print(f"[Message] From {user_id}: {text}")

    if user_id not in ADMINS:
        if is_unauthorized_link(text) or contains_generic_link(text):
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="🚫 ห้ามส่งลิงก์หรือ QR Code ที่ไม่ได้รับอนุญาต")]
                )
            )
            try:
                line_bot_api.leave_group(group_id)
            except Exception as e:
                print(f"❗ เตะผู้ใช้ไม่ได้: {e}")

# -------- ป้องกันคนโดนเตะออก ----------
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    group_id = event.source.group_id
    left_user_id = event.left.members[0].user_id

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=f"⚠️ มีคนโดนเตะออกจากกลุ่ม: {left_user_id}")]
        )
    )

# -------- ป้องกันการเชิญคน (ต้องเป็นแอดมิน) ----------
@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    group_id = event.source.group_id
    joined_user_id = event.joined.members[0].user_id

    if joined_user_id not in ADMINS:
        try:
            line_bot_api.leave_group(group_id)
        except Exception as e:
            print(f"❗ เตะผู้ใช้ไม่ได้: {e}")

# -------- ป้องกันเปลี่ยนชื่อกลุ่ม ----------
@handler.add(GroupNameUpdateEvent)
def handle_group_name_change(event):
    group_id = event.source.group_id
    user_id = event.source.user_id
    new_name = event.new_group_name

    if user_id not in ADMINS:
        try:
            # เปลี่ยนกลับเป็นชื่อเดิม
            line_bot_api.set_group_name(group_id, DEFAULT_GROUP_NAME)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="🚫 ไม่สามารถเปลี่ยนชื่อกลุ่มได้")]
                )
            )
        except Exception as e:
            print(f"❗ ไม่สามารถ revert ชื่อกลุ่ม: {e}")

# -------- ป้องกันเปลี่ยนรูปกลุ่ม (ด้วยข้อความแจ้งเตือนเท่านั้น) ----------
@handler.add(LeaveEvent)
def handle_group_photo_change(event):
    group_id = event.source.group_id
    line_bot_api.push_message(
        to=group_id,
        messages=[TextMessage(text="⚠️ มีความพยายามเปลี่ยนรูปภาพกลุ่ม โปรดตรวจสอบ")]
    )

# -------- Main ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
