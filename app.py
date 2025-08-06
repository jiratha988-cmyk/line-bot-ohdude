from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration, MessagingApi, ReplyMessageRequest, TextMessage, LeaveGroupRequest, DeleteMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, JoinEvent,
    MemberLeftEvent, MemberJoinedEvent,
    LeaveEvent, PostbackEvent, ThingsEvent,
    UnsendEvent, FollowEvent, UnfollowEvent,
    BeaconEvent, AccountLinkEvent, VideoPlayCompleteEvent,
    BotJoinedEvent, BotLeaveEvent, MemberLeftEvent, GroupNameChangeEvent
)
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# โหลด token จาก environment
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

# ตั้งค่าไลน์ SDK
config = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(config)
handler = WebhookHandler(channel_secret)

# 🟢 ตั้งชื่อกลุ่มที่ถูกต้องไว้ตรงนี้
ORIGINAL_GROUP_NAME = "ลูกค้าOh!dudeVip (6)"

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

# ✅ ตอบข้อความ
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else None

    print(f"🔥 ได้รับข้อความ: {text}")

    # ตรวจสอบลิงก์ LINE ที่ไม่ใช่ของ ohshop
    line_link = re.findall(r"(https?://line\.me/[^\s]+)", text)
    if line_link:
        if not any("ohshop" in link for link in line_link):
            # ❌ เตะออก (optional) หรือแค่ลบ
            # line_bot_api.leave_group(group_id)  # หรือลอง kick ออกถ้ามี permission
            try:
                line_bot_api.delete_message(DeleteMessageRequest(message_id=event.message.id))
                reply = TextMessage(text="❌ ห้ามส่งลิงก์ LINE ที่ไม่ใช่ของ Ohshop!")
                line_bot_api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[reply]
                ))
            except Exception as e:
                print("⚠️ ไม่สามารถลบข้อความได้:", e)
            return

    reply = TextMessage(text=f"คุณพิมพ์ว่า: {text}")
    line_bot_api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[reply]
    ))

# ✅ ตรวจจับการเปลี่ยนชื่อกลุ่ม
@handler.add(GroupNameChangeEvent)
def handle_group_name_change(event):
    group_id = event.source.group_id
    new_name = event.event.group_name
    if new_name != ORIGINAL_GROUP_NAME:
        warning = TextMessage(text=f"⚠️ มีการเปลี่ยนชื่อกลุ่มเป็น \"{new_name}\"")
        restore = TextMessage(text=f"🔄 เปลี่ยนกลับเป็น \"{ORIGINAL_GROUP_NAME}\" แล้วจ้า")
        try:
            line_bot_api.set_group_name(group_id, ORIGINAL_GROUP_NAME)
        except Exception as e:
            print("❌ เปลี่ยนชื่อกลุ่มกลับไม่ได้:", e)
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[warning, restore]
        ))

# ✅ แจ้งเตือนคนถูกเตะออก
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    for member in event.left.members:
        user_id = member.user_id
        message = TextMessage(text=f"👋 มีคนโดนเตะออกจากกลุ่ม: {user_id}")
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[message]
        ))

# ✅ เข้ากลุ่มใหม่
@handler.add(JoinEvent)
def handle_join(event):
    message = TextMessage(text="👋 บอทมาแล้วจ้า! พร้อมช่วยดูแลกลุ่มนี้")
    line_bot_api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[message]
    ))
