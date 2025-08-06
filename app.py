from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration, MessagingApi, ReplyMessageRequest, TextMessage, PushMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, JoinEvent, MemberJoinedEvent, MemberLeftEvent
)
from linebot.v3.exceptions import InvalidSignatureError
import os
import re

app = Flask(__name__)

# Env
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")

config = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(config)
handler = WebhookHandler(channel_secret)

# ตั้งค่ากลุ่มและ admin
ADMINS = ["USER_ID_1", "USER_ID_2"]
OWNER_ID = "OWNER_USER_ID"
GROUP_ID = "YOUR_GROUP_ID"
DEFAULT_GROUP_NAME = "OH! DUDE SHOP ✅"  # ชื่อกลุ่มที่ควรใช้เสมอ

# ===== ตรวจลิงก์ไม่ได้รับอนุญาต =====
def is_unauthorized_content(text):
    return ("line.me" in text and "ohshop" not in text.lower()) or re.search(r"https?://", text)

# ===== Root Check =====
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running."

# ===== Webhook =====
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ===== Handle Message =====
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_id = event.source.user_id
    group_id = event.source.group_id
    text = event.message.text

    # บล็อกลิงก์ที่ไม่ได้มาจาก ohshop
    if is_unauthorized_content(text) and user_id not in ADMINS:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="❌ ห้ามส่งลิงก์ที่ไม่ใช่ของร้าน! กำลังดำเนินการ...")]
            )
        )
        try:
            line_bot_api.leave_group(group_id)
            line_bot_api.kickout_from_group(group_id, user_id)
        except:
            pass
        return

# ===== Handle Group Join =====
@handler.add(MemberJoinedEvent)
def handle_member_join(event):
    joined_user_id = event.joined.members[0].user_id
    group_id = event.source.group_id

    # ถ้าไม่ใช่แอดมิน ห้ามเชิญคนเข้า
    if joined_user_id not in ADMINS and joined_user_id != OWNER_ID:
        try:
            line_bot_api.push_message(
                PushMessageRequest(
                    to=group_id,
                    messages=[TextMessage(text="⚠️ มีสมาชิกถูกเชิญเข้ามาโดยไม่ได้รับอนุญาต กำลังดำเนินการ...")]
                )
            )
            line_bot_api.kickout_from_group(group_id, joined_user_id)
        except:
            pass

# ===== Handle Member Leave =====
@handler.add(MemberLeftEvent)
def handle_member_left(event):
    group_id = event.source.group_id
    left_user_id = event.left.members[0].user_id

    try:
        line_bot_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text=f"⚠️ มีสมาชิกออกจากกลุ่ม (หรือโดนเตะ): {left_user_id}")]
            )
        )
    except:
        pass

# ===== Handle Group Name Change (Auto Revert) =====
@handler.add(JoinEvent)
def on_group_join(event):
    group_id = event.source.group_id

    try:
        group_info = line_bot_api.get_group_summary(group_id)
        if group_info.group_name != DEFAULT_GROUP_NAME:
            line_bot_api.update_group_title(group_id, DEFAULT_GROUP_NAME)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=group_id,
                    messages=[TextMessage(text=f"🚫 กลุ่มถูกเปลี่ยนชื่อโดยไม่ได้รับอนุญาต — เปลี่ยนกลับเป็น '{DEFAULT_GROUP_NAME}' แล้ว")]
                )
            )
    except Exception as e:
        print(f"Group name check failed: {e}")

# ===== สำหรับทดสอบ local เท่านั้น =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
