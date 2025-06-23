import streamlit as st
import requests
import tempfile
import random
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips

# بيانات السور
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

PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"

def get_timings(sura_number):
    url = f"https://verses.quran.com/Abdul_Basit_Murattal_64kbps/{sura_number:03d}.timings"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception("بيانات توقيت الآيات غير متوفرة لهذه السورة. جرب سورة أخرى.")
    timings = []
    for l in resp.text.strip().splitlines():
        parts = l.strip().split()
        if len(parts) == 3:
            timings.append((int(parts[0]), float(parts[1]), float(parts[2])))
    return timings

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

st.set_page_config(page_title="فيديو قرآن من آية إلى آية", layout="centered")
st.title("أنشئ فيديو قرآن بخلفية طبيعية (من آية إلى آية)")

sura_idx = st.selectbox("اختر السورة:", options=range(1, 115), format_func=lambda i: f"{i}. {SURA_NAMES[i-1]}")
try:
    timings = get_timings(sura_idx)
    ayah_count = len(timings)
except Exception as e:
    st.error(str(e))
    st.stop()

from_ayah = st.number_input("من الآية رقم:", min_value=1, max_value=ayah_count, value=1)
to_ayah = st.number_input("إلى الآية رقم:", min_value=from_ayah, max_value=ayah_count, value=ayah_count)

if st.button("إنشاء الفيديو"):
    audio_url = f"https://verses.quran.com/Abdul_Basit_Murattal_64kbps/{sura_idx:03d}.mp3"
    with st.spinner("جاري تحميل ملف السورة الصوتي..."):
        try:
            audio_resp = requests.get(audio_url, stream=True)
            if audio_resp.status_code != 200:
                st.error("تعذر تحميل ملف الصوت! جرب سورة أخرى.")
                st.stop()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                for chunk in audio_resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        audio_file.write(chunk)
                audio_path = audio_file.name
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحميل الصوت: {e}")
            st.stop()
    # استخراج المقطع
    try:
        st.info("جاري استخراج المقطع الصوتي للآيات المطلوبة...")
        audio_clip = AudioFileClip(audio_path)
        # timings: (ayah_number, start, end)
        start_sec = None
        end_sec = None
        for ayah, start, end in timings:
            if ayah == from_ayah:
                start_sec = start
            if ayah == to_ayah:
                end_sec = end
        if start_sec is None or end_sec is None:
            st.error("لم يتم العثور على توقيتات الآيات المطلوبة.")
            st.stop()
        ayat_clip = audio_clip.subclip(start_sec, end_sec)
    except Exception as e:
        st.error(f"حدث خطأ أثناء استخراج المقطع: {e}")
        st.stop()
    # تحميل فيديو الخلفية
    with st.spinner("جاري تحميل فيديو الخلفية الطبيعية..."):
        try:
            nature_video_url = get_random_nature_video_url()
            headers = {"User-Agent": "Mozilla/5.0"}
            bg_resp = requests.get(nature_video_url, stream=True, headers=headers)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as bg_file:
                for chunk in bg_resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        bg_file.write(chunk)
                bg_video_path = bg_file.name
        except Exception as e:
            st.error(f"حدث خطأ أثناء جلب فيديو الخلفية: {e}")
            st.stop()
    # دمج الصوت مع الخلفية
    try:
        st.info("جاري دمج الصوت مع الفيديو...")
        duration = ayat_clip.duration
        bg_clip = VideoFileClip(bg_video_path)
        if bg_clip.duration >= duration:
            bg_clip = bg_clip.subclip(0, duration)
        else:
            loops = int(duration // bg_clip.duration) + 1
            clips = [bg_clip] * loops
            bg_clip = concatenate_videoclips(clips).subclip(0, duration)
        final_clip = bg_clip.set_audio(ayat_clip)
        output_video_path = bg_video_path.replace(".mp4", "_output.mp4")
        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=24)
        st.success("تم إنشاء الفيديو بنجاح!")
        with open(output_video_path, "rb") as f:
            st.download_button("تحميل الفيديو الجديد", f, file_name="quran_ayat_with_nature.mp4", mime="video/mp4")
        st.video(output_video_path)
    except Exception as e:
        st.error(f"حدث خطأ أثناء إنشاء الفيديو: {e}")
