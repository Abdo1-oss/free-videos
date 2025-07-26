import streamlit as st
import requests
import tempfile
import os
import random
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from PIL import Image
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
import matplotlib.font_manager as fm

QURAA = [{"name": "الحصري مرتل", "id": "Husary_64kbps"}, {"name": "العفاسي", "id": "Alafasy_64kbps"}]
SURA_NAMES = ["الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة"]
SURA_AYAHS = [7, 286, 200, 176, 120]
PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"

def get_pexels_videos(keywords, min_height=720, needed_duration=30):
    headers = {"Authorization": PEXELS_API_KEY}
    all_links = []
    for query in random.sample(keywords, len(keywords)):
        params = {"query": query, "per_page": 20}
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
        if not resp.ok:
            continue
        for v in resp.json().get("videos", []):
            for vf in v.get("video_files", []):
                if vf.get("width", 0) < vf.get("height", 1) and vf.get("height", 1) >= min_height:
                    link = vf.get("link")
                    if link and link not in all_links:
                        all_links.append(link)
        if len(all_links) > 20:
            break
    video_clips = []
    total_dur = 0
    i = 0
    while total_dur < needed_duration and i < len(all_links):
        video_url = all_links[i]
        i += 1
        st.info(f"تحميل فيديو: {video_url}")
        try:
            r = requests.get(video_url, stream=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vid_file:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        vid_file.write(chunk)
                vid_file.flush()
                file_size = os.path.getsize(vid_file.name)
                if file_size < 10000:
                    continue
                clip = VideoFileClip(vid_file.name).resize((1080,1920))
                video_clips.append(clip)
                total_dur += clip.duration
        except Exception as e:
            st.warning(str(e))
            continue
    if total_dur < needed_duration:
        st.error("مدة الفيديوهات أقل من مدة الصوت. أضف آيات أقل أو استخدم كلمات مفتاحية أكثر ولا تكرر الفيديو.")
        return []
    return video_clips

def get_ayah_text(sura_idx, ayah_num):
    url = f"https://api.alquran.cloud/v1/ayah/{sura_idx}:{ayah_num}/ar"
    r = requests.get(url)
    return r.json()["data"]["text"] if r.ok else ""

def get_audio_segment(qari_id, sura_idx, ayah):
    mp3_url = f"https://everyayah.com/data/{qari_id}/{sura_idx:03d}{ayah:03d}.mp3"
    r = requests.get(mp3_url)
    if r.status_code != 200:
        return AudioSegment.silent(duration=2000)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_ayah_file:
        temp_ayah_file.write(r.content)
        temp_ayah_file.flush()
        segment = AudioSegment.from_mp3(temp_ayah_file.name)
    return segment

def create_text_image_noto_naskh(text, size=(1080, 200), fontsize=60, font_path="NotoNaskhArabic-Regular.ttf"):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    fig, ax = plt.subplots(figsize=(size[0]/100, size[1]/100), dpi=100)
    prop = fm.FontProperties(fname=font_path)
    ax.text(0.5, 0.5, bidi_text, fontsize=fontsize, fontproperties=prop,
            color="white", ha='center', va='center')
    ax.set_axis_off()
    fig.patch.set_alpha(0)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        plt.savefig(tmp.name, bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close(fig)
        img = Image.open(tmp.name).convert("RGBA")
        arr = np.array(img)
    os.unlink(tmp.name)
    return arr

def split_text_chunks(text, chunk_size=3):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
        i += chunk_size
    return chunks

st.title("فيديو قرآن شورتس من عدة فيديوهات بيكسيلز مع تقسيم النص")

selected_qari = st.selectbox("اختر القارئ:", [q["name"] for q in QURAA])
qari_id = [q["id"] for q in QURAA][[q["name"] for q in QURAA].index(selected_qari)]
sura_idx = st.selectbox("اختر السورة:", range(1, len(SURA_NAMES)+1), format_func=lambda i: f"{i}. {SURA_NAMES[i-1]}")
ayah_count = SURA_AYAHS[sura_idx-1]

from_ayah = st.number_input("من الآية رقم:", 1, ayah_count, 1)
to_ayah = st.number_input("إلى الآية رقم:", from_ayah, ayah_count, from_ayah)

keywords_default = ["nature", "sky", "mountain", "river", "forest", "sunrise", "space", "stars", "moon", "clouds"]

if st.button("إنشاء الفيديو"):
    st.info("جاري تجهيز الصوت...")
    audio_segments = []
    ayat_texts = []
    ayah_durations = []
    for ayah in range(int(from_ayah), int(to_ayah)+1):
        segment = get_audio_segment(qari_id, sura_idx, ayah)
        audio_segments.append(segment)
        ayat_texts.append(get_ayah_text(sura_idx, ayah))
        ayah_durations.append(len(segment)/1000)
    merged = sum(audio_segments[1:], audio_segments[0])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as merged_file:
        merged.export(merged_file.name, format="mp3")
        audio_path = merged_file.name
    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration

    st.info("جاري تحميل وتجميع فيديوهات الخلفية من بيكسيلز...")
    video_clips = get_pexels_videos(keywords_default, needed_duration=total_duration)
    if not video_clips:
        st.stop()
    concat_video = concatenate_videoclips(video_clips)
    if concat_video.duration > total_duration:
        concat_video = concat_video.subclip(0, total_duration)

    st.info("جاري تجهيز النص...")
    text_clips = []
    start = 0
    for text, ayah_dur in zip(ayat_texts, ayah_durations):
        chunks = split_text_chunks(text, chunk_size=3)
        chunk_dur = ayah_dur / max(1, len(chunks))
        for chunk in chunks:
            # استخدم خط Noto Naskh Arabic بالتشكيل وبكل شيء
            text_img = create_text_image_noto_naskh(chunk, size=(1080, 200), fontsize=60, font_path="NotoNaskhArabic-Regular.ttf")
            text_clip = ImageClip(text_img, duration=chunk_dur).set_start(start).set_position(("center","bottom"))
            text_clips.append(text_clip)
            start += chunk_dur

    final = CompositeVideoClip([concat_video] + text_clips).set_audio(audio_clip).set_duration(total_duration)

    output_path = "quran_shorts_pexels_final.mp4"
    st.info("جاري تصدير الفيديو...")
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    st.success("تم الإنشاء!")
    st.video(output_path)
    with open(output_path, "rb") as f:
        st.download_button("تحميل الفيديو", f, file_name="quran_shorts_pexels_final.mp4", mime="video/mp4")
