import streamlit as st
import requests
import tempfile
import random
import os
from pydub import AudioSegment, silence
from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips
)
import cv2

# ------------ إعدادات API KEYS ------------
PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"
PIXABAY_API_KEY = "50380897-76243eaec536038f687ff8e15"
# Unsplash لا يدعم فيديو فعلي، فقط صور

# ------------ إعدادات القراء ------------
QURAA = [
    {"name": "الحصري مرتل", "id": "Husary_64kbps"},
    {"name": "عبد الباسط مرتل", "id": "Abdul_Basit_Murattal_64kbps"},
    {"name": "المنشاوي مرتل", "id": "Minshawy_Murattal_128kbps"},
    {"name": "المعيقلي", "id": "MaherAlMuaiqly_64kbps"},
    {"name": "الغامدي", "id": "Ghamadi_40kbps"},
    {"name": "مشاري العفاسي", "id": "Alafasy_64kbps"},
    {"name": "سعود الشريم", "id": "Shuraym_64kbps"},
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

# ------------ فلترة الفيديوهات ------------
def is_people_video(video_text):
    people_keywords = [
        "person","people","man","woman","boy","girl","child","men","women","kids","kid","human","face",
        "portrait","selfie","friends","couple","wedding","bride","groom","student","students","woman face"
    ]
    return any(word in video_text for word in people_keywords)

def is_shorts(width, height, duration, min_duration=7, max_duration=120):
    ratio = width / height if height > 0 else 1
    return (ratio < 0.7) and (min_duration <= duration <= max_duration)

# ------------ جلب فيديوهات شورتس ------------

def get_pexels_shorts_videos(api_key, needed_duration):
    headers = {"Authorization": api_key}
    params = {"query": "nature", "per_page": 50}
    resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    videos = resp.json().get('videos', [])
    shorts = []
    for v in videos:
        desc = (v.get("description") or "").lower()
        user_name = (v.get("user", {}).get("name") or "").lower()
        tags = [t.lower() for t in v.get("tags",[])]
        text = " ".join(tags) + " " + desc + " " + user_name
        if is_people_video(text):
            continue
        for file in v["video_files"]:
            if file["quality"]=="hd" and is_shorts(file["width"], file["height"], v["duration"]):
                shorts.append((file["link"], v["duration"]))  # (الرابط, المدة)
                break
    return shorts

def get_pixabay_shorts_videos(api_key, needed_duration):
    params = {
        "key": api_key,
        "q": "nature",
        "per_page": 50,
        "video_type": "film",
        "safesearch": "true"
    }
    resp = requests.get("https://pixabay.com/api/videos/", params=params)
    videos = resp.json().get("hits", [])
    shorts = []
    for v in videos:
        text = (v.get("tags") or "").lower() + " " + (v.get("user") or "").lower()
        if is_people_video(text):
            continue
        for vid in v["videos"].values():
            if is_shorts(vid["width"], vid["height"], v["duration"]):
                shorts.append((vid["url"], v["duration"]))
                break
    return shorts

# Unsplash صور فقط، يمكن تحويل صورة واحدة لفيديو طويل أو عدة صور لمقطع متحرك
def get_unsplash_nature_images():
    st.warning("Unsplash لا يدعم فيديوهات حقيقية، سيتم استخدام صور متحركة.")
    url = f"https://api.unsplash.com/search/photos?query=nature&per_page=30&orientation=portrait&client_id=ضع_مفتاح_unsplash_هنا"
    resp = requests.get(url)
    data = resp.json()
    images = [img["urls"]["regular"] for img in data.get("results",[])]
    return images

def download_and_get_clip(url, resize=(1080,1920)):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, stream=True, headers=headers)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as file:
        for chunk in resp.iter_content(chunk_size=1024*1024):
            if chunk:
                file.write(chunk)
        file.flush()
        return VideoFileClip(file.name).resize(newsize=resize), file.name

def make_slideshow_from_images(images, duration, resize=(1080,1920)):
    from moviepy.editor import ImageClip
    clips = []
    img_duration = duration / len(images)
    for img_url in images:
        resp = requests.get(img_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as imgfile:
            imgfile.write(resp.content)
            imgfile.flush()
            clips.append(ImageClip(imgfile.name).set_duration(img_duration).resize(newsize=resize))
    return concatenate_videoclips(clips)

# ------------ فلترة الصمت في الصوت ------------
def trim_silence(audio_segment, silence_thresh=-40, chunk_size=10):
    start_trim = silence.detect_leading_silence(audio_segment, silence_thresh, chunk_size)
    end_trim = silence.detect_leading_silence(audio_segment.reverse(), silence_thresh, chunk_size)
    duration = len(audio_segment)
    return audio_segment[start_trim:duration-end_trim]

# ------------ صدى الصوت ------------
def add_echo(sound, delay=250, attenuation=0.6):
    echo = sound - 20
    for i in range(1, 5):
        echo = echo.overlay(sound - int(20 + i*10), position=i*delay)
    return sound.overlay(echo)

# ------------ ضباب الفيديو ------------
def blur_frame(img, ksize=15):
    return cv2.GaussianBlur(img, (ksize|1, ksize|1), 0)

# ------------ واجهة المستخدم ------------
st.set_page_config(page_title="فيديو قرآن شورتس بتأثيرات", layout="centered")
st.title("أنشئ فيديو قرآن قصير (شورتس) بخلفية طبيعية وصوت القارئ وتأثيرات")

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

add_blur = st.checkbox("تفعيل الضباب (Blur) على الفيديو؟", value=True)
add_echo_effect = st.checkbox("تفعيل الصدى (Echo) على الصوت؟", value=True)
video_source = st.selectbox("اختر مصدر الفيديو:", ["Pexels", "Pixabay", "Unsplash (صور فقط)"])

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

            if add_echo_effect:
                merged = add_echo(merged)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as merged_file:
                merged.export(merged_file.name, format="mp3")
                audio_path = merged_file.name

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        with st.spinner("جاري تحميل وتجهيز فيديوهات الخلفية..."):
            video_clips = []
            used_links = set()
            if video_source == "Pexels":
                shorts = get_pexels_shorts_videos(PEXELS_API_KEY, duration)
            elif video_source == "Pixabay":
                shorts = get_pixabay_shorts_videos(PIXABAY_API_KEY, duration)
            elif video_source.startswith("Unsplash"):
                images = get_unsplash_nature_images()
                final_video = make_slideshow_from_images(images, duration)
                if add_blur:
                    final_video = final_video.fl_image(lambda image: blur_frame(image, ksize=15))
                final = final_video.set_audio(audio_clip).set_duration(duration)
                output_path = "quran_shorts.mp4"
                final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
                st.success("تم إنشاء الفيديو بنجاح!")
                st.video(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("تحميل الفيديو", f, file_name="quran_shorts.mp4", mime="video/mp4")
                st.stop()
            else:
                shorts = []

            downloaded_duration = 0.0
            while downloaded_duration < duration and shorts:
                link, vid_dur = random.choice(shorts)
                if link in used_links:
                    shorts = [s for s in shorts if s[0] != link]
                    continue
                clip, fname = download_and_get_clip(link)
                if add_blur:
                    clip = clip.fl_image(lambda image: blur_frame(image, ksize=15))
                video_clips.append(clip)
                downloaded_duration += clip.duration
                used_links.add(link)
            if not video_clips or downloaded_duration < duration:
                st.error("لم يتم العثور على فيديوهات كافية لتغطية مدة الصوت. حاول مجددًا أو غيّر المصدر.")
                st.stop()
            final_video = concatenate_videoclips(video_clips).subclip(0, duration)

        final = final_video.set_audio(audio_clip).set_duration(duration)
        output_path = "quran_shorts.mp4"
        final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        st.success("تم إنشاء الفيديو بنجاح!")
        st.video(output_path)
        with open(output_path, "rb") as f:
            st.download_button("تحميل الفيديو", f, file_name="quran_shorts.mp4", mime="video/mp4")
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
