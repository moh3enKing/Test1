from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# توکن ربات تلگرام خود را جایگزین کنید
BOT_TOKEN = "TOKEN_BOT"

# مشخصات سازنده
OWNER_USERNAME = "@KIING_ZOG"
OWNER_ID = 5637609683

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"سلام! 👋\nمن سازنده ربات هستم.\nUsername: {OWNER_USERNAME}\nID: {OWNER_ID}"
    )

# نمونه تابع برای پاسخ به پیام های متنی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if "سلام" in text:
        await update.message.reply_text("سلام! حال شما چطوره؟")
    elif "وقت" in text:
        await update.message.reply_text("وقت بخیر! 🌸")
    else:
        await update.message.reply_text("متوجه نشدم! 😅")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
