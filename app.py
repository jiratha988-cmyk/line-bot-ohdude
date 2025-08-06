from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, PushMessageRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent, JoinEvent, LeaveEvent, MemberLeftEvent
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# ใช้ .env หรือระบบ Env ของ Render
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# ตั้งชื่อกลุ่มที่ต้องล็อคไว้
LOCKED_GROUP_NAME = "Oh!dude Vape Club"

# รายชื่อผู้ดูแลกลุ่ม
ADMINS = [
    'USER_ID_ADMIN1',
    'USER_ID_ADMIN2'
]

# Domain ที่อนุญาตให้ส่งในกลุ่ม
ALLOWED_LINK = "ohshop"

# เก็บชื่อกลุ่มเดิมไว้
original_group_name = {}

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def contains_unauthorized_link(text):
    if ALLOWED_LINK not in text and "line.me" in text:
        return True
    if re.search(r"https?://(?!.*ohshop).*line\.me", text):
        return True
    return False

@handler.add(MessageEvent)
def handle_message(event: MessageEvent):
    if not isinstance(event.message, TextMessageContent):
        return

    user_id = event.source.user_id
    group_id = event.source.group_id
    text = event.message.text

    # ป้องกันส่งลิงก์ไม่พึงประสงค์
    if contains_unauthorized_link(text) and user_id not in ADMINS:
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="ห้ามส่งลิงก์อื่นที่ไม่ใช่ของร้าน ohshop")]
                )
            )
            line_bot_api.kickout_from_group(group_id, user_id)
        except:
            pass

@handler.add(JoinEvent)
def handle_join(event: JoinEvent):
    group_id = event.source.group_id
    try:
        # เก็บชื่อกลุ่มเดิมไว้
        summary = line_bot_api.get_group_summary(group_id)
        original_group_name[group_id] = summary.group_name
    except:
        pass

@handler.add(MemberLeftEvent)
def handle_member_left(event: MemberLeftEvent):
    group_id = event.source.group_id
    left_user_id = event.left.members[0].user_id if event.left.members else "(ไม่ทราบ ID)"

    # แจ้งเตือนคนโดนเตะออก
    try:
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text=f"สมาชิก {left_user_id} ออกจากกลุ่มหรืออาจถูกเตะออก ❗")]
            )
        )
    except:
        pass

@handler.add(LeaveEvent)
def handle_leave(event: LeaveEvent):
    # บอทโดนเตะออกจากกลุ่ม - ไม่สามารถทำอะไรได้โดยตรง
    # แนะนำให้ทำ Webhook Monitor แยกถ้าต้อง track
    pass

if __name__ == "__main__":
    app.run(debug=True)
