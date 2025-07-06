import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import pymongo
import requests
from datetime import datetime, timedelta
import asyncio
import json
from urllib.parse import urlparse

# Configuration
TOKEN = "8089258024:AAFx2ieX_ii_TrI60wNRRY7VaLHEdD3-BP0"
ADMIN_ID = 5637609683
CHANNEL_ID = "@netgoris"
MONGODB_URI = "mongodb+srv://mohsenfeizi1386:RIHPhDJPhd9aNJvC@cluster0.ounkvru.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-app.onrender.com/")  # Set this in Render

# Web services
AI_SERVICES = [
    "https://starsshoptl.ir/Ai/index.php?text={}",
    "https://starsshoptl.ir/Ai/index.php?model=gpt&text={}",
    "https://starsshoptl.ir/Ai/index.php?model=deepseek&text={}"
]
INSTAGRAM_API = "https://pouriam.top/eyephp/instagram?url={}"
SPOTIFY_API = "http://api.cactus-dev.ir/spotify.php?url={}"
PINTEREST_API = "https://haji.s2025h.space/pin/?url={}&client_key=keyvip"
IMAGE_API = "https://v3.api-free.ir/image/?text={}"

# MongoDB setup
client = pymongo.MongoClient(MONGODB_URI)
db = client["telegram_bot"]
users_collection = db["users"]

# Spam protection
SPAM_LIMIT = 4
SPAM_WINDOW = 120  # seconds (2 minutes)

# Keyboards
MAIN_KEYBOARD = ReplyKeyboardMarkup([["راهنما 📖", "پشتیبانی 🛠"]], resize_keyboard=True)
SUPPORT_CANCEL_KEYBOARD = ReplyKeyboardMarkup([["لغو 🚫"]], resize_keyboard=True)
ADMIN_KEYBOARD = ReplyKeyboardMarkup([["بن کاربر 🚫", "آنبن کاربر ✅", "ارسال پیام 📩"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})

    # Notify admin for first-time users
    if not user:
        users_collection.insert_one({"user_id": user_id, "joined": False, "messages": [], "support_mode": False, "banned": False})
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"کاربر جدید استارت کرد:\nID: {user_id}\nUsername: @{update.effective_user.username or 'None'}"
        )

    # Check if user is banned
    if user and user.get("banned", False):
        await update.message.reply_text("⛔ شما از ربات بن شدی! برای اطلاعات بیشتر با پشتیبانی تماس بگیر.")
        return

    # Check if user has joined the channel
    if not await check_channel_membership(context, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 جوین کانال", url=f"https://t.me/netgoris")],
            [InlineKeyboardButton("✅ تأیید", callback_data="check_join")]
        ])
        await update.message.reply_text(
            "لطفاً برای استفاده از ربات، ابتدا در کانال ما جوین کنید!",
            reply_markup=keyboard
        )
        return

    # Welcome message
    welcome_text = (
        "🎉 به ربات ما خوش اومدی!\n"
        "ممنون که جوین کردی! 😊 حالا می‌تونی از امکانات ربات استفاده کنی.\n"
        "برای اطلاعات بیشتر، دکمه راهنما رو بزن."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_KEYBOARD)

async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except telegram.error.TelegramError:
        return False

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    if await check_channel_membership(context, user_id):
        users_collection.update_one({"user_id": user_id}, {"$set": {"joined": True}})
        welcome_text = (
            "🎉 به ربات ما خوش اومدی!\n"
            "ممنون که جوین کردی! 😊 حالا می‌تونی از امکانات ربات استفاده کنی.\n"
            "برای اطلاعات بیشتر، دکمه راهنما رو بزن."
        )
        await query.message.delete()  # Delete join message
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            reply_markup=MAIN_KEYBOARD
        )
    else:
        await query.message.edit_text(
            "❌ هنوز در کانال جوین نکردی!\nلطفاً در کانال جوین کن و دوباره تأیید بزن.",
            reply_markup=query.message.reply_markup
        )

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(context, user_id):
        await update.message.reply_text("لطفاً اول در کانال جوین کن!")
        return

    guide_text = (
        "📖 **راهنمای استفاده از ربات** 📖\n\n"
        "🎯 **چطور از ربات استفاده کنم؟**\n"
        "این ربات بهت کمک می‌کنه تا محتوای اینستاگرام، اسپاتیفای، پینترست و تصاویر تولید شده با هوش مصنوعی رو دانلود کنی. کافیه لینک یا متن مورد نظرت رو بفرستی!\n\n"
        "🔗 **لینک‌های پشتیبانی‌شده**:\n"
        "- اینستاگرام: لینک پست یا ریل\n"
        "- اسپاتیفای: لینک آهنگ\n"
        "- پینترست: لینک پین\n"
        "- ساخت تصویر: متن دلخواه (مثال: `flower`)\n\n"
        "⚠️ **اخطارها و قوانین**:\n"
        "1. فقط لینک‌های معتبر از سرویس‌های بالا ارسال کن. لینک‌های نامعتبر باعث خطا می‌شن.\n"
        "2. اسپم نکن! حداکثر ۴ پیام در ۲ دقیقه می‌تونی بفرستی.\n"
        "3. در صورت تخلف، ممکنه از ربات بن بشی.\n"
        "4. برای هر مشکلی، از دکمه پشتیبانی استفاده کن.\n\n"
        "😊 **سؤالی داشتی؟** دکمه پشتیبانی رو بزن تا بتونیم باهات در ارتباط باشیم!"
    )
    await update.message.reply_text(guide_text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
    await update.message.reply_text("🌟 ما همیشه در خدمت شما هستیم!", reply_markup=MAIN_KEYBOARD)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(context, user_id):
        await update.message.reply_text("لطفاً اول در کانال جوین کن!")
        return

    users_collection.update_one({"user_id": user_id}, {"$set": {"support_mode": True。即

System: ### فایل: `requirements.txt`

```text
python-telegram-bot==20.7
pymongo==4.6.1
requests==2.31.0
