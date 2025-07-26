import streamlit as st
import requests
import tempfile
import os
import random
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np

QURAA = [{"name": "الحصري مرتل", "id": "Husary_64kbps"}, {"name": "العفاسي", "id": "Alafasy_64kbps"}]
SURA_NAMES = ["الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة"]
SURA_AYAHS = [7, 286, 200, 176, 120]

PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"

def get_pexels_video(keywords):
    headers = {"Authorization": PEXELS_API_KEY}
    query = random.choice(keywords)
    params = {"query": query, "per_page": 15}
    resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    videos = []
    if resp.ok:
        for v in resp.json().get("videos", []):
            for vf in v.get("video_files", []):
                if vf.get("width", 0) < vf.get("height", 1) and vf.get("height", 1) >= 720:
                    videos.append(vf.get("link"))
    if videos:
        return random.choice(videos)
    return None

def get_best_video(keywords):
    link = get_pexels_video(keywords)
    if link:
        return link
    videos = [
        "https://assets.mixkit.co/videos/download/mixkit-clouds-in-the-sky-123.mp4",
        "https://assets.mixkit.co/videos/download/mixkit-mountain-landscape-1233.mp4",
        "https://assets.mixkit.co/videos/download/mixkit-sunrise-in-the-mountains-1176.mp4"
    ]
    return random.choice(videos)

def get_ayah_text(sura_idx, ayah_num):
    url = f"https://api.alquran.cloud/v1/ayah/{sura_idx}:{ayah_num}/ar"
    r = requests.get(url)
    return r.json()["data"]["text"] if r.ok else ""

def create_text_image(text, size, font_path="Amiri-Regular.ttf", fontsize=50):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    img = Image.new("RGBA", size, (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, fontsize)
    except:
        font = ImageFont.load_default()
    # استخدم textbbox إذا متاحة، وإلا getsize
    try:
        bbox = draw.textbbox((0, 0), bidi_text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        w, h = font.getsize(bidi_text)
    draw.text(((size[0]-w)//2, (size[1]-h)//2), bidi_text, font=font, fill="white")
    return np.array(img)

st.title("فيديو قرآن شورتس بسيط")

selected_qari = st.selectbox("اختر القارئ:", [q["name"] for q in QURAA])
qari_id = [q["id"] for q in QURAA][[q["name"] for q in QURAA].index(selected_qari)]
sura_idx = st.selectbox("اختر السورة:", range(1, len(SURA_NAMES)+1), format_func=lambda i: f"{i}. {SURA_NAMES[i-1]}")
ayah_count = SURA_AYAHS[sura_idx-1]

from_ayah = st.number_input("من الآية رقم:", 1, ayah_count, 1)
to_ayah = st.number_input("إلى الآية رقم:", from_ayah, ayah_count, from_ayah)

keywords_default = ["nature", "sky", "mountain", "river", "forest", "sunrise", "space", "stars", "moon", "clouds"]

if st.button("إنشاء الفيديو"):
    st.info("جاري تجهيز الصوت...")
    merged = None
    ayat_texts = []
    for ayah in range(int(from_ayah), int(to_ayah)+1):
        mp3_url = f"https://everyayah.com/data/{qari_id}/{sura_idx:03d}{ayah:03d}.mp3"
        r = requests.get(mp3_url)
        ayat_texts.append(get_ayah_text(sura_idx, ayah))
        if r.status_code != 200:
            segment = AudioSegment.silent(duration=2000)
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_ayah_file:
                temp_ayah_file.write(r.content)
                temp_ayah_file.flush()
                segment = AudioSegment.from_mp3(temp_ayah_file.name)
        merged = segment if merged is None else merged + segment

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as merged_file:
        merged.export(merged_file.name, format="mp3")
        audio_path = merged_file.name

    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration

    st.info("جاري تحميل فيديو الخلفية...")
    video_url = get_best_video(keywords_default)
    if not video_url:
        st.error("تعذر الحصول على فيديو مناسب من بيكسيلز أو Mixkit")
        st.stop()
    r = requests.get(video_url, stream=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vid_file:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                vid_file.write(chunk)
        vid_file.flush()
        if os.path.getsize(vid_file.name) < 10000:
            st.error("فشل تحميل الفيديو أو الملف غير صالح")
            st.stop()
        clip = VideoFileClip(vid_file.name)
        video_clip = clip.subclip(0, min(duration, clip.duration)).resize((1080,1920))

    st.info("جاري تجهيز النص...")
    ayat_text = " ".join(ayat_texts)
    text_img = create_text_image(ayat_text, (1080, 200), "Amiri-Regular.ttf", 60)
    text_clip = ImageClip(text_img, duration=duration).set_position(("center","bottom"))

    final = CompositeVideoClip([video_clip, text_clip.set_start(0)]).set_audio(audio_clip).set_duration(duration)

    output_path = "quran_shorts_simple.mp4"
    st.info("جاري تصدير الفيديو...")
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    st.success("تم الإنشاء!")
    st.video(output_path)
    with open(output_path, "rb") as f:
        st.download_button("تحميل الفيديو", f, file_name="quran_shorts_simple.mp4", mime="video/mp4")
