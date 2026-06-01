import os
import logging
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    ContextTypes,
)
from telegram.error import TelegramError

import database as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

CHANNEL_1 = "@Milliy_sertifikat_lider"
CHANNEL_2 = -1003945305522
GIFT_CHANNEL = -1003763206013

REQUIRED = 5

ADMIN_IDS = {6987211321, 5523761749}
BOT_USERNAME = "msliderbot"


def ref_link(uid: int):
    return f"https://t.me/{BOT_USERNAME}?start=ref{uid}"


async def check_ch1(bot, uid):
    try:
        m = await bot.get_chat_member(CHANNEL_1, uid)
        return m.status in ("member", "administrator", "creator")
    except TelegramError:
        return False


async def check_ch2(bot, uid):
    try:
        m = await bot.get_chat_member(CHANNEL_2, uid)
        if m.status in ("member", "administrator", "creator"):
            return True
    except TelegramError:
        pass

    return db.has_join(uid)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    db.add_user(uid, user.first_name or "User")

    if context.args and context.args[0].startswith("ref"):
        try:
            ref = int(context.args[0][3:])
            if ref != uid:
                db.add_ref(ref, uid)
        except:
            pass

    if db.is_verified(uid):
        c = db.ref_count(uid)
        if c >= REQUIRED:
            await update.message.reply_text("🎁 Sovg'a tayyor!")
        else:
            await send_ref(update, uid)
        return

    kb = [
        [
            InlineKeyboardButton("1-kanal", url=f"https://t.me/{CHANNEL_1[1:]}"),
            InlineKeyboardButton("2-kanal", url="https://t.me/+zfIZNpX9BLplMTBi")
        ],
        [InlineKeyboardButton("Tasdiqlash", callback_data="verify")]
    ]

    await update.message.reply_text(
        "Assalomu alaykum!",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def send_ref(update, uid):
    c = db.ref_count(uid)
    await update.message.reply_text(
        f"Referral: {ref_link(uid)}\n{c}/{REQUIRED}"
    )


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if not await check_ch1(context.bot, uid):
        await q.answer("1-kanal yo'q", show_alert=True)
        return

    if not await check_ch2(context.bot, uid):
        await q.answer("2-kanal request yo'q", show_alert=True)
        return

    db.verify(uid)

    await q.edit_message_text("✅ Tasdiqlandi")
    await send_ref(q, uid)


async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = update.chat_join_request
    if r.chat.id == CHANNEL_2:
        db.add_join(r.from_user.id)


async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if db.has_received_gift(uid):
        await q.answer("Allaqachon olgansiz", show_alert=True)
        return

    if db.ref_count(uid) < REQUIRED:
        await q.answer("Yetarli referral yo'q", show_alert=True)
        return

    try:
        link = await context.bot.create_chat_invite_link(
            GIFT_CHANNEL,
            member_limit=1
        )

        db.mark_gift_received(uid)

        await q.edit_message_text(f"🎁 Link: {link.invite_link}")

    except TelegramError:
        await q.answer("Xatolik", show_alert=True)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(gift, pattern="gift"))
    app.add_handler(ChatJoinRequestHandler(join_request))

    async def run():
        await app.initialize()
        await app.start()

        await app.updater.start_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            webhook_url=f"{WEBHOOK_URL}/webhook",
            url_path="webhook",
        )

        await app.updater.idle()

    asyncio.run(run())


if __name__ == "__main__":
    main()
