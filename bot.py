import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
ContextTypes, ChatJoinRequestHandler
)
from telegram.error import TelegramError

import database as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(**name**)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

CHANNEL_1 = "@Milliy_sertifikat_lider"
CHANNEL_2_ID = -1003945305522
GIFT_CHANNEL_ID = -1003763206013

REQUIRED_REF = 5

ADMIN_IDS = {6987211321, 5523761749}
BOT_USERNAME = "msliderbot"

def ref_link(user_id: int):
return f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"

async def check_channel1(bot, user_id: int):
try:
m = await bot.get_chat_member(CHANNEL_1, user_id)
return m.status in ("member", "administrator", "creator")
except TelegramError:
return False

async def check_channel2(bot, user_id: int):
try:
m = await bot.get_chat_member(CHANNEL_2_ID, user_id)
if m.status in ("member", "administrator", "creator"):
return True
except TelegramError:
pass

```
return db.has_join_request(user_id)
```

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
uid = user.id
name = user.first_name or "Do'st"

```
db.register_user(uid, name)

args = context.args

if args and args[0].startswith("ref"):
    try:
        ref = int(args[0][3:])
        if ref != uid:
            db.add_referral(ref, uid)
    except:
        pass

if db.is_verified(uid):
    count = db.get_referral_count(uid)

    if count >= REQUIRED_REF:
        await update.message.reply_text("🎁 Siz tayyorsiz. Sovg'ani oling.")
    else:
        await send_ref_msg(update, uid)
    return

text = (
    f"Assalomu alaykum {name}, botga xush kelibsiz.\n\n"
    "Davom etish uchun kanallarga a'zo bo'ling."
)

keyboard = [
    [
        InlineKeyboardButton("1-Kanal", url=f"https://t.me/{CHANNEL_1.lstrip('@')}"),
        InlineKeyboardButton("2-Kanal", url="https://t.me/+zfIZNpX9BLplMTBi")
    ],
    [InlineKeyboardButton("Tasdiqlash", callback_data="verify")]
]

await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
```

async def send_ref_msg(update, uid):
link = ref_link(uid)
count = db.get_referral_count(uid)
left = max(0, REQUIRED_REF - count)

```
await update.message.reply_text(
    f"5 ta do'st taklif qiling.\n\n"
    f"Sizning link: {link}\n"
    f"{count}/{REQUIRED_REF} | yana {left}"
)
```

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
uid = q.from_user.id

```
await q.answer("Tekshirilmoqda...")

if not await check_channel1(context.bot, uid):
    await q.answer("1-kanalga a'zo bo'ling", show_alert=True)
    return

if not await check_channel2(context.bot, uid):
    await q.answer("2-kanalga request yuboring", show_alert=True)
    return

db.set_verified(uid)

await q.edit_message_text("✅ Tasdiqlandingiz")

await send_ref_msg(q, uid)
```

async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
req = update.chat_join_request

```
if req.chat.id == CHANNEL_2_ID:
    db.record_join_request(req.from_user.id)
```

async def get_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
uid = q.from_user.id

```
await q.answer()

if db.has_received_gift(uid):
    await q.answer("Allaqachon olgansiz", show_alert=True)
    return

if db.get_referral_count(uid) < REQUIRED_REF:
    await q.answer("Yetarli referral yo'q", show_alert=True)
    return

try:
    link = await context.bot.create_chat_invite_link(
        GIFT_CHANNEL_ID,
        member_limit=1
    )

    db.mark_gift_received(uid)

    await q.edit_message_text(f"🎁 Link: {link.invite_link}")

except TelegramError:
    await q.answer("Xatolik", show_alert=True)
```

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id not in ADMIN_IDS:
return

```
await update.message.reply_text(
    "/odam - users\n/xabar - broadcast"
)
```

async def odam(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id not in ADMIN_IDS:
return

```
count = db.get_user_count()
await update.message.reply_text(f"Users: {count}")
```

async def xabar(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id not in ADMIN_IDS:
return

```
msg = " ".join(context.args)
users = db.get_all_user_ids()

for u in users:
    try:
        await context.bot.send_message(u, msg)
    except:
        pass
```

def main():
app = Application.builder().token(BOT_TOKEN).build()

```
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("odam", odam))
app.add_handler(CommandHandler("xabar", xabar))

app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
app.add_handler(CallbackQueryHandler(get_gift, pattern="gift"))

app.add_handler(ChatJoinRequestHandler(join_request))

port = int(os.getenv("PORT", 10000))

app.run_webhook(
    listen="0.0.0.0",
    port=port,
    webhook_url=f"{WEBHOOK_URL}/webhook",
    url_path="webhook"
)
```

if **name** == "**main**":
main()
