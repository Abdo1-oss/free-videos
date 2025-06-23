import streamlit as st
import threading
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import moviepy.editor as mp

# استخدم متغير البيئة لحماية التوكن
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7843765684:AAFd4rnJ1m2ryGXPgnJhO9hUfsSvs6z1ito")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي رابط فيديو قرآن الكريم (من يوتيوب أو ما شابه)، وسأرسل لك فيديو مناظر طبيعية بنفس الصوت."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    video_path = os.path.join(DOWNLOAD_DIR, "input.mp4")
    audio_path = os.path.join(DOWNLOAD_DIR, "audio.mp3")

    await update.message.reply_text("جاري تحميل الفيديو واستخراج الصوت...")

    # تحميل الفيديو
    try:
        ydl_opts = {"outtmpl": video_path, "format": "bestvideo+bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء تحميل الفيديو: {e}")
        return

    # استخراج الصوت
    try:
        video = mp.VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء استخراج الصوت: {e}")
        return

    await update.message.reply_text("تم استخراج الصوت بنجاح ✅\nجاري جلب فيديو خلفية من مناظر طبيعية...")

    # جلب فيديو مناظر طبيعية من Pexels
    bg_video_url = get_nature_video_url()
    if not bg_video_url:
        await update.message.reply_text("تعذر الحصول على فيديو خلفية من Pexels.")
        return

    # إرسال النتائج للمستخدم
    await update.message.reply_text(
        f"رابط فيديو الخلفية من Pexels:\n{bg_video_url}\n\n"
        f"تم استخراج الصوت من الفيديو الذي أرسلته ويمكنك تحميله من هنا:"
    )
    try:
        with open(audio_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file)
    except Exception:
        await update.message.reply_text("تعذر إرسال ملف الصوت، لكنه محفوظ على السيرفر.")

    await update.message.reply_text(
        "يمكنك دمج الصوت بالفيديو باستخدام خدمات أونلاين مثل [clideo.com/merge-video](https://clideo.com/merge-video) أو [online-convert.com](https://video.online-convert.com/convert-to-mp4) أو عبر أي محرر فيديو."
    )

def get_nature_video_url():
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': 'nature', 'per_page': 1}
    response = requests.get(
        'https://api.pexels.com/videos/search', headers=headers, params=params
    )
    if response.status_code == 200:
        data = response.json()
        if data['videos']:
            # نختار جودة HD إن توفرت
            for file in data['videos'][0]['video_files']:
                if file['quality'] == 'hd':
                    return file['link']
            return data['videos'][0]['video_files'][0]['link']
    return None

import threading

def start_bot():
    app.run_polling()

if 'bot_thread' not in st.session_state:
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    st.session_state['bot_thread'] = bot_thread

st.success("بوت تيليجرام يعمل في الخلفية ✅")
