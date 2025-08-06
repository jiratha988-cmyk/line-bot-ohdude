from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent,
    MemberJoinedEvent, MemberLeftEvent
)
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

ADMINS = ['USERID_ADMIN1', 'USERID_ADMIN2']
DEFAULT_GROUP_NAME = "Oh!dude Group"

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

def is_unauthorized_link(text):
    return "line.me" in text and "ohshop" not in text.lower()

def contains_generic_link(text):
    return bool(re.search(r"(https?://[^\s]+)", text))

@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id
    group_id = event.source.group_id
    text = event.message.text if isinstance(event.message, TextMessageContent) else ""

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
                print(f"เตะผู้ใช้ไม่ได้: {e}")

@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    group_id = event.source.group_id
    joined_user_id = event.joined.members[0].user_id

    if joined_user_id not in ADMINS:
        try:
            line_bot_api.leave_group(group_id)
        except Exception as e:
            print(f"เตะไม่ได้: {e}")

@handler.add(MemberLeftEvent)
def handle_member_left(event):
    group_id = event.source.group_id
    left_user_id = event.left.members[0].user_id

    line_bot_api.push_message(
        to=group_id,
        messages=[TextMessage(text=f"⚠️ มีคนโดนเตะออกจากกลุ่ม: {left_user_id}")]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
