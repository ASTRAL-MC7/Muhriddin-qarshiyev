import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from telegram.error import TelegramError
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # e.g. https://your-app.onrender.com

CHANNEL_1_USERNAME = "Milliy_sertifikat_lider"   # @Milliy_sertifikat_lider
CHANNEL_2_ID = -1003945305522
GIFT_CHANNEL_ID = -1003763206013
REQUIRED_REFERRALS = 5
ADMIN_IDS = [6987211321, 5523761749]

BOT_USERNAME = "msliderbot"


# ─── HELPERS ────────────────────────────────────────────────────────────────

def get_referral_link(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"


async def check_channel1(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_1_USERNAME}", user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramError:
        return False


async def check_channel2_request(bot, user_id: int) -> bool:
    """Check if user has a pending or accepted join request in channel 2."""
    try:
        # If user is already member
        member = await bot.get_chat_member(CHANNEL_2_ID, user_id)
        if member.status in ("member", "administrator", "creator"):
            return True
    except TelegramError:
        pass
    # Check pending join requests stored in our DB
    return db.has_join_request(user_id)


async def approve_channel2_request(bot, user_id: int):
    try:
        await bot.approve_chat_join_request(CHANNEL_2_ID, user_id)
    except TelegramError as e:
        logger.warning(f"Could not approve join request for {user_id}: {e}")


async def send_verification_message(update_or_message, context):
    """Send the subscription check message with inline buttons."""
    keyboard = [
        [
            InlineKeyboardButton("📢 1-Kanal", url=f"https://t.me/{CHANNEL_1_USERNAME}"),
            InlineKeyboardButton("📢 2-Kanal", url="https://t.me/+zfIZNpX9BLplMTBi"),
        ],
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="verify")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = (
        "📋 Davom etish uchun quyidagi kanallarga obuna bo'ling:\n\n"
        "1️⃣ @Milliy_sertifikat_lider — Kanalga a'zo bo'ling\n"
        "2️⃣ 2-Kanal — So'rov yuboring (REQUEST)\n\n"
        "Tayyor bo'lgach ✅ <b>Tasdiqlash</b> tugmasini bosing."
    )
    if hasattr(update_or_message, "reply_text"):
        await update_or_message.reply_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await update_or_message.message.reply_text(text, reply_markup=markup, parse_mode="HTML")


async def send_referral_message(message, user_id: int):
    ref_link = get_referral_link(user_id)
    ref_count = db.get_referral_count(user_id)
    remaining = max(0, REQUIRED_REFERRALS - ref_count)
    text = (
        f"🎁 Sovg'ani olish uchun atigi <b>{REQUIRED_REFERRALS} ta</b> do'stingizni taklif qiling!\n\n"
        f"🔗 Sizning referal havolangiz:\n<code>{ref_link}</code>\n\n"
        f"👥 Hozirgi holat: <b>{ref_count}/{REQUIRED_REFERRALS}</b> do'st\n"
        f"⏳ Yana <b>{remaining}</b> ta odam kerak!"
    )
    await message.reply_text(text, parse_mode="HTML")


# ─── HANDLERS ───────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "Do'st"
    args = context.args

    # Register user
    is_new = db.register_user(user_id, first_name)

    # Handle referral
    if args and args[0].startswith("ref"):
        try:
            referrer_id = int(args[0][3:])
            if referrer_id != user_id:
                db.add_referral_if_needed(referrer_id, user_id)
        except ValueError:
            pass

    # Check if already fully verified
    if db.is_verified(user_id):
        ref_count = db.get_referral_count(user_id)
        if ref_count >= REQUIRED_REFERRALS:
            await send_gift_ready_message(update.message, user_id)
        else:
            await send_referral_message(update.message, user_id)
        return

    # Welcome message
    welcome_text = (
        f"Assalomu alaykum <b>{first_name}</b>, botga xush kelibsiz! 🎉\n\n"
        "Bu bot orqali siz <b>Muhriddin Qarshiyev</b>ning Kurslari uchun "
        "<b>50% chegirma</b> va <b>Bepul darslariga</b> ega bo'la olasiz."
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")
    await send_verification_message(update.message, context)


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id

    await query.answer("Tekshirilmoqda...")

    joined_ch1 = await check_channel1(context.bot, user_id)
    if not joined_ch1:
        await query.answer(
            "❌ Siz hali 1-kanalga a'zo bo'lmadingiz! Iltimos, avval @Milliy_sertifikat_lider kanaliga a'zo bo'ling.",
            show_alert=True
        )
        return

    joined_ch2 = await check_channel2_request(context.bot, user_id)
    if not joined_ch2:
        await query.answer(
            "❌ Siz hali 2-kanalga so'rov yubormadingiz! Iltimos, 2-kanal havolasiga kiring va so'rov yuboring.",
            show_alert=True
        )
        return

    # Approve channel 2 join request
    await approve_channel2_request(context.bot, user_id)

    # Mark as verified
    db.set_verified(user_id)

    await query.edit_message_text(
        "✅ <b>Tasdiqlandingiz!</b> Barcha kanallarga a'zo bo'ldingiz.",
        parse_mode="HTML"
    )

    # Check referral progress & notify referrers
    await notify_referrer_on_new_join(context.bot, user_id)

    # Send referral message
    await send_referral_message(query.message, user_id)


async def notify_referrer_on_new_join(bot, new_user_id: int):
    """When a new verified user joined via referral, notify the referrer."""
    referrer_id = db.get_referrer(new_user_id)
    if not referrer_id:
        return

    ref_count = db.get_referral_count(referrer_id)
    remaining = max(0, REQUIRED_REFERRALS - ref_count)

    if ref_count >= REQUIRED_REFERRALS:
        # Referrer has completed!
        try:
            await bot.send_message(
                referrer_id,
                "🎉 <b>Tabriklaymiz!</b> Siz 5 ta do'stingizni taklif qildingiz!\nEndi sovg'ani olishingiz mumkin 👇",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎁 Sovg'ani olish", callback_data="get_gift")]
                ])
            )
        except TelegramError:
            pass
    else:
        try:
            await bot.send_message(
                referrer_id,
                f"👥 Sizda <b>+1</b> ta do'st, jami <b>{ref_count}</b> ta, sizga yana <b>{remaining}</b> ta odam kerak!",
                parse_mode="HTML"
            )
        except TelegramError:
            pass


async def send_gift_ready_message(message, user_id: int):
    keyboard = [[InlineKeyboardButton("🎁 Sovg'ani olish", callback_data="get_gift")]]
    await message.reply_text(
        "🎉 <b>Tabriklaymiz!</b> Siz barcha shartlarni bajardingiz!\nQuyidagi tugmani bosib sovg'angizni oling 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def get_gift_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    # Check if already received gift
    if db.has_received_gift(user_id):
        await query.answer("⚠️ Siz allaqachon sovg'ani olib bo'lgansiz!", show_alert=True)
        return

    # Check referral count
    ref_count = db.get_referral_count(user_id)
    if ref_count < REQUIRED_REFERRALS:
        remaining = REQUIRED_REFERRALS - ref_count
        await query.answer(
            f"❌ Sizda hali yetarli referal yo'q. Yana {remaining} ta odam kerak!",
            show_alert=True
        )
        return

    # Generate one-time invite link
    try:
        link = await context.bot.create_chat_invite_link(
            GIFT_CHANNEL_ID,
            member_limit=1,
            name=f"gift_{user_id}"
        )
        db.mark_gift_received(user_id)
        await query.edit_message_text(
            f"🎁 <b>Tabriklaymiz!</b> Mana sizning sovg'a linkingiz:\n\n{link.invite_link}\n\n"
            "⚠️ Bu link faqat <b>1 marta</b> ishlatilishi mumkin!",
            parse_mode="HTML"
        )
    except TelegramError as e:
        logger.error(f"Failed to create invite link: {e}")
        await query.answer("❌ Xatolik yuz berdi, admin bilan bog'laning.", show_alert=True)


# ─── JOIN REQUEST HANDLER ────────────────────────────────────────────────────

async def chat_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when someone sends a join request to channel 2."""
    request = update.chat_join_request
    if request.chat.id == CHANNEL_2_ID:
        db.record_join_request(request.from_user.id)


# ─── ADMIN COMMANDS ──────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = (
        "🛠 <b>Admin Panel</b>\n\n"
        "/panel — Ushbu panel\n"
        "/odam — Botdan foydalangan foydalanuvchilar soni\n"
        "/xabar [matn] — Hammaga xabar yuborish"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def odam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    count = db.get_user_count()
    await update.message.reply_text(f"👥 Botga /start bosgan foydalanuvchilar soni: <b>{count}</b>", parse_mode="HTML")


async def xabar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /xabar [matn]")
        return

    text = " ".join(context.args)
    users = db.get_all_user_ids()
    sent, failed = 0, 0

    status_msg = await update.message.reply_text(f"📤 Xabar yuborilmoqda... (0/{len(users)})")

    for i, uid in enumerate(users):
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except TelegramError:
            failed += 1
        if (i + 1) % 20 == 0:
            try:
                await status_msg.edit_text(f"📤 Xabar yuborilmoqda... ({i+1}/{len(users)})")
            except TelegramError:
                pass

    await status_msg.edit_text(
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"✔️ Muvaffaqiyatli: <b>{sent}</b>\n"
        f"❌ Yuborilmadi: <b>{failed}</b>",
        parse_mode="HTML"
    )


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("odam", odam))
    app.add_handler(CommandHandler("xabar", xabar))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(get_gift_callback, pattern="^get_gift$"))
    from telegram.ext import ChatJoinRequestHandler
    app.add_handler(ChatJoinRequestHandler(chat_join_request))

    port = int(os.environ.get("PORT", 8443))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"{WEBHOOK_URL}/webhook",
        url_path="webhook",
    )


if __name__ == "__main__":
    main()
