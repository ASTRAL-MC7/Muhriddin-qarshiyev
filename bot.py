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
log = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK = os.getenv("WEBHOOK_URL")

CHANNEL1 = "@Milliy_sertifikat_lider"
CHANNEL2 = -1003945305522
GIFT = -1003763206013

REQ = 5
ADMIN = {6987211321, 5523761749}
BOT = "msliderbot"


def link(uid):
    return f"https://t.me/{BOT}?start=ref{uid}"


async def c1(bot, uid):
    try:
        m = await bot.get_chat_member(CHANNEL1, uid)
        return m.status in ("member", "creator", "administrator")
    except:
        return False


async def c2(bot, uid):
    try:
        m = await bot.get_chat_member(CHANNEL2, uid)
        if m.status in ("member", "creator", "administrator"):
            return True
    except:
        pass
    return db.has_join(uid)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = u.id
    name = u.first_name or "user"

    db.add_user(uid, name)

    if context.args and context.args[0].startswith("ref"):
        try:
            ref = int(context.args[0][3:])
            if ref != uid:
                db.add_ref(ref, uid)
        except:
            pass

    if db.is_verified(uid):
        if db.ref_count(uid) >= REQ:
            await update.message.reply_text("🎁 Sovg‘a tayyor")
        else:
            await show_ref(update, uid)
        return

    kb = [
        [
            InlineKeyboardButton("1-kanal", url=f"https://t.me/{CHANNEL1[1:]}"),
            InlineKeyboardButton("2-kanal", url="https://t.me/+zfIZNpX9BLplMTBi")
        ],
        [InlineKeyboardButton("Tasdiqlash", callback_data="v")]
    ]

    await update.message.reply_text(
        f"Assalomu alaykum {name}",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def show_ref(update, uid):
    c = db.ref_count(uid)
    await update.message.reply_text(
        f"Referal: {link(uid)}\n{c}/{REQ}"
    )


async def verify(update: Update, context):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if not await c1(context.bot, uid):
        await q.answer("1-kanal yo‘q", show_alert=True)
        return

    if not await c2(context.bot, uid):
        await q.answer("2-kanal request yo‘q", show_alert=True)
        return

    db.verify(uid)

    await q.edit_message_text("Tasdiqlandi")
    await show_ref(q, uid)


async def join(update: Update, context):
    r = update.chat_join_request
    if r.chat.id == CHANNEL2:
        db.add_join(r.from_user.id)


async def gift(update: Update, context):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if db.has_join(uid) and db.ref_count(uid) >= REQ:
        try:
            link = await context.bot.create_chat_invite_link(
                GIFT, member_limit=1
            )
            await q.edit_message_text(link.invite_link)
        except:
            await q.answer("error", show_alert=True)
    else:
        await q.answer("yetarli emas", show_alert=True)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="v"))
    app.add_handler(ChatJoinRequestHandler(join))
    app.add_handler(CallbackQueryHandler(gift, pattern="gift"))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        webhook_url=f"{WEBHOOK}/webhook",
        url_path="webhook"
    )


if __name__ == "__main__":
    main()
