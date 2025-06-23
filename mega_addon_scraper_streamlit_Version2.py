import PIL
from PIL import Image

# دعم Pillow 10+
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import streamlit as st
import requests
import tempfile
import random
import os
from pydub import AudioSegment, silence
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
)

QURAA = [
    {"name": "الحصري مرتل", "id": "Husary_64kbps"},
    {"name": "عبد الباسط مرتل", "id": "Abdul_Basit_Murattal_64kbps"},
    {"name": "المنشاوي مرتل", "id": "Minshawy_Murattal_128kbps"},
    {"name": "المعيقلي", "id": "MaherAlMuaiqly_64kbps"},
    {"name": "الغامدي", "id": "Ghamadi_40kbps"},
]

SURA_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس", "هود", "يوسف", "الرعد",
    "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء",
    "النمل", "القصص", "العنكبوت", "الروم", "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم",
    "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة", "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق",
    "التحريم", "الملك", "القلم", "الحاقة", "المعارج", "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ",
    "النازعات", "عبس", "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات", "القارعة", "التكاثر", "العصر",
    "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص", "الفلق", "الناس"
]

SURA_AYAHS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6
]

PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"

def trim_silence(audio_segment, silence_thresh=-40, chunk_size=10):
    start_trim = silence.detect_leading_silence(audio_segment, silence_thresh, chunk_size)
    end_trim = silence.detect_leading_silence(audio_segment.reverse(), silence_thresh, chunk_size)
    duration = len(audio_segment)
    return audio_segment[start_trim:duration-end_trim]

def get_ayah_texts(sura, from_ayah, to_ayah):
    url = f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={sura}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return [""] * (to_ayah - from_ayah + 1)
    verses = resp.json().get('verses', [])
    ayah_dict = {}
    for v in verses:
        try:
            sura_num, ayah_num = map(int, v['verse_key'].split(':'))
            ayah_dict[ayah_num] = v['text_uthmani']
        except Exception:
            continue
    texts = []
    for ayah in range(from_ayah, to_ayah+1):
        texts.append(ayah_dict.get(ayah, ""))
    return texts

def get_random_nature_video_url():
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": "nature", "per_page": 30}
    resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    resp.raise_for_status()
    videos = resp.json().get('videos', [])
    if not videos:
        raise Exception("لم يتم العثور على فيديوهات طبيعة!")
    video = random.choice(videos)
    for f in video["video_files"]:
        if f["quality"] == "hd" and f["width"] <= 1280:
            return f["link"]
    return video["video_files"][0]["link"]

st.set_page_config(page_title="فيديو قرآن شورتس مع نص الآيات", layout="centered")
st.title("أنشئ فيديو قرآن قصير (شورتس) بخلفية طبيعية ونص الآيات")

qari_names = [q["name"] for q in QURAA]
selected_qari_idx = st.selectbox("اختر القارئ:", options=range(len(qari_names)), format_func=lambda i: qari_names[i])
selected_qari = QURAA[selected_qari_idx]["id"]

sura_idx = st.selectbox("اختر السورة:", options=range(1, 115), format_func=lambda i: f"{i}. {SURA_NAMES[i-1]}")
ayah_count = SURA_AYAHS[sura_idx-1]

col1, col2 = st.columns(2)
with col1:
    from_ayah = st.number_input("من الآية رقم:", min_value=1, max_value=ayah_count, value=1)
with col2:
    to_ayah = st.number_input("إلى الآية رقم:", min_value=from_ayah, max_value=ayah_count, value=from_ayah)

uploaded_font = st.file_uploader("ارفع ملف الخط (TTF أو OTF) لعرض نص الآية بخطك المفضل (اختياري)", type=["ttf", "otf"])
if uploaded_font:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ttf") as tmp_font:
        tmp_font.write(uploaded_font.read())
        font_path = tmp_font.name
else:
    font_path = "Arial" # أو أي خط افتراضي متوفر

if st.button("إنشاء الفيديو"):
    try:
        with st.spinner("جاري تحميل ودمج الصوت بدون فواصل..."):
            merged = None
            for ayah in range(int(from_ayah), int(to_ayah)+1):
                mp3_url = f"https://everyayah.com/data/{selected_qari}/{sura_idx:03d}{ayah:03d}.mp3"
                r = requests.get(mp3_url)
                if r.status_code != 200:
                    st.error(f"تعذر تحميل الآية رقم {ayah}.")
                    st.stop()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_ayah_file:
                    temp_ayah_file.write(r.content)
                    temp_ayah_file.flush()
                    segment = AudioSegment.from_mp3(temp_ayah_file.name)
                    segment = trim_silence(segment)
                    merged = segment if merged is None else merged + segment
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as merged_file:
                merged.export(merged_file.name, format="mp3")
                audio_path = merged_file.name

        with st.spinner("جلب نصوص الآيات..."):
            ayah_texts = get_ayah_texts(sura_idx, from_ayah, to_ayah)

        with st.spinner("تحميل فيديو الخلفية وتحويله لحجم شورتس..."):
            nature_video_url = get_random_nature_video_url()
            headers = {"User-Agent": "Mozilla/5.0"}
            bg_resp = requests.get(nature_video_url, stream=True, headers=headers)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as bg_file:
                for chunk in bg_resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        bg_file.write(chunk)
                bg_video_path = bg_file.name

        st.info("جاري إنتاج الفيديو النهائي وكتابة نصوص الآيات...")
        video_clip = VideoFileClip(bg_video_path).resize(newsize=(1080, 1920))
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        if video_clip.duration < duration:
            loops = int(duration // video_clip.duration) + 1
            video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, duration)
        else:
            video_clip = video_clip.subclip(0, duration)

        ayah_duration = duration / len(ayah_texts)
        clips = [video_clip.set_audio(audio_clip)]
        for i, text in enumerate(ayah_texts):
            start = i * ayah_duration
            end = (i+1) * ayah_duration
            try:
                txt_clip = (TextClip(text, fontsize=60, color='white', size=(1000, 200),
                            font=font_path,
                            bg_color='black', method='text')
                            .set_position(('center', 'bottom')).set_start(start).set_end(end))
            except Exception as txt_err:
                txt_clip = (TextClip(text, fontsize=60, color='white', size=(1000, 200),
                            bg_color='black', method='text')
                            .set_position(('center', 'bottom')).set_start(start).set_end(end))
            clips.append(txt_clip)
        final = CompositeVideoClip(clips, size=(1080,1920)).set_duration(duration)
        output_path = "quran_shorts.mp4"
        final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        st.success("تم إنشاء الفيديو بنجاح!")
        st.video(output_path)
        with open(output_path, "rb") as f:
            st.download_button("تحميل الفيديو", f, file_name="quran_shorts.mp4", mime="video/mp4")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
