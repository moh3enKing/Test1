import telebot
from telebot import types
from flask import Flask, request
import requests
from pymongo import MongoClient
import time
import ssl

### اطلاعات مهم ربات:
BOT_TOKEN = "8089258024:AAFx2ieX_ii_TrI60wNRRY7VaLHEdD3-BP0"
CHANNEL_USERNAME = "@netgoris"
ADMIN_ID = 5637609683
MONGO_URL = "mongodb+srv://mohsenfeizi1386:RIHPhDJPhd9aNJvC@cluster0.ounkvru.mongodb.net/?retryWrites=true&w=majority&tls=true"
WEBHOOK_URL = "https://tellgpt-bot.onrender.com/webhook"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)
client = MongoClient(MONGO_URL, tls=True, tlsAllowInvalidCertificates=True)
db = client["tellgpt"]
users = db["users"]
bans = db["bans"]
spam = {}

### دکمه های ثابت:
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛟 پشتیبانی", "📜 راهنما")
    return kb

### ضد اسپم:
def is_spamming(user_id):
    now = time.time()
    if user_id not in spam:
        spam[user_id] = []
    spam[user_id] = [t for t in spam[user_id] if now - t < 120]
    spam[user_id].append(now)
    return len(spam[user_id]) > 4

### چک عضویت:
def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

### جین اجباری:
def send_join_message(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton("✅ عضویت زدم", callback_data="check_join"))
    bot.send_message(chat_id, f"لطفا ابتدا در کانال {CHANNEL_USERNAME} عضو شوید تا بتوانید از ربات استفاده کنید.", reply_markup=kb)

### پیام راهنما:
def help_text():
    return ("📋 راهنمای استفاده:\n\n"
            "🔹 ارسال پیام برای دریافت پاسخ هوش مصنوعی\n"
            "🔹 ارسال لینک‌های اینستاگرام، پینترست یا اسپاتیفای برای دانلود\n"
            "🔹 ارسال متن برای ساخت تصویر\n\n"
            "⚠️ قوانین:\n"
            "❌ ارسال اسپم ممنوع\n"
            "❌ رعایت ادب الزامیست\n"
            "✅ با عضویت در کانال از خدمات بهره‌مند شوید")

### وب سرویس چت:
def ai_chat(text):
    urls = [
        f"https://starsshoptl.ir/Ai/index.php?text={text}",
        f"https://starsshoptl.ir/Ai/index.php?model=gpt&text={text}",
        f"https://starsshoptl.ir/Ai/index.php?model=deepseek&text={text}"
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            if res.ok:
                return res.text
        except:
            continue
    return "❌ خطا در دریافت پاسخ!"

### وب سرویس‌های دانلود:
def insta_download(url):
    try:
        res = requests.get(f"https://pouriam.top/eyephp/instagram?url={url}").json()
        return res["links"]
    except:
        return []

def spotify_download(url):
    try:
        res = requests.get(f"http://api.cactus-dev.ir/spotify.php?url={url}").json()
        return res["data"]["download_url"]
    except:
        return None

def pinterest_download(url):
    try:
        res = requests.get(f"https://haji.s2025h.space/pin/?url={url}&client_key=keyvip").json()
        return res["download_url"] if res["status"] else None
    except:
        return None

def image_generator(text):
    try:
        res = requests.get(f"https://v3.api-free.ir/image/?text={text}").json()
        return res["result"] if res["ok"] else None
    except:
        return None

### پیام استارت:
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    if bans.find_one({"user_id": uid}):
        bot.send_message(uid, "🚫 شما مسدود هستید.")
        return
    if not is_joined(uid):
        send_join_message(uid)
        return
    if not users.find_one({"user_id": uid}):
        users.insert_one({"user_id": uid})
        bot.send_message(ADMIN_ID, f"کاربر جدید: {uid}")
    bot.send_message(uid, "سلام! خوش آمدید 🎉", reply_markup=main_menu())

### دکمه‌های کیبورد:
@bot.message_handler(func=lambda m: m.text == "📜 راهنما")
def help_handler(msg):
    bot.send_message(msg.chat.id, help_text(), reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🛟 پشتیبانی")
def support(msg):
    if msg.chat.type != "private":
        return
    bot.send_message(msg.chat.id, "پیام خود را بنویسید. برای لغو، 'لغو' را ارسال کنید.", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_support)

def process_support(msg):
    if msg.text.lower() == "لغو":
        bot.send_message(msg.chat.id, "پشتیبانی لغو شد.", reply_markup=main_menu())
        return
    bot.send_message(ADMIN_ID, f"پیام پشتیبانی از {msg.from_user.id}:\n{msg.text}")
    bot.send_message(msg.chat.id, "پیام شما ارسال شد.", reply_markup=main_menu())

### چک عضویت:
@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def check_join(c):
    if is_joined(c.from_user.id):
        bot.delete_message(c.message.chat.id, c.message.message_id)
        bot.send_message(c.message.chat.id, "✅ تایید شد! خوش آمدید.", reply_markup=main_menu())
    else:
        bot.answer_callback_query(c.id, "لطفا ابتدا عضو شوید.")

### مدیریت پیام‌های عادی:
@bot.message_handler(func=lambda m: True)
def main(msg):
    uid = msg.from_user.id
    if msg.chat.type != "private":
        return
    if bans.find_one({"user_id": uid}):
        return
    if is_spamming(uid):
        bot.send_message(uid, "⏳ لطفا کمی صبر کنید، در حال محدودیت ضد اسپم هستید.")
        return
    text = msg.text
    if text.startswith("http"):
        if "instagram.com" in text:
            links = insta_download(text)
            if links:
                for l in links:
                    bot.send_message(uid, l)
            else:
                bot.send_message(uid, "❌ خطا در دریافت لینک اینستاگرام.")
        elif "spotify.com" in text:
            link = spotify_download(text)
            if link:
                bot.send_audio(uid, link)
            else:
                bot.send_message(uid, "❌ خطا در دریافت آهنگ اسپاتیفای.")
        elif "pin.it" in text or "pinterest.com" in text:
            link = pinterest_download(text)
            if link:
                bot.send_photo(uid, link)
            else:
                bot.send_message(uid, "❌ خطا در دریافت عکس پینترست.")
        else:
            bot.send_message(uid, "⚠️ لینک معتبر نیست.")
    elif text.lower().startswith("عکس "):
        pic = image_generator(text[5:])
        if pic:
            bot.send_photo(uid, pic)
        else:
            bot.send_message(uid, "❌ خطا در ساخت تصویر.")
    else:
        answer = ai_chat(text)
        bot.send_message(uid, answer)

### دریافت وب‌هوک:
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

### ست کردن وب‌هوک:
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    res = requests.get(url, params={"url": WEBHOOK_URL})
    print(res.text)

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=5000)
