import streamlit as st
import requests
import tempfile
import random
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, concatenate_videoclips

# قائمة مبسطة لبعض القراء (يمكنك توسيعها)
QURAA = [
    {"name": "الحصري مرتل", "id": "Husary_64kbps"},
    {"name": "عبد الباسط مرتل", "id": "Abdul_Basit_Murattal_64kbps"},
    {"name": "المعيقلي", "id": "MaherAlMuaiqly_64kbps"},
    {"name": "المنشاوي مرتل", "id": "Minshawy_Murattal_128kbps"},
    {"name": "الغامدي", "id": "Ghamadi_40kbps"}
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

PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"
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

st.title("أنشئ فيديو قرآن من آية إلى آية بخلفية طبيعية (everyayah.com)")

qari_names = [q["name"] for q in QURAA]
selected_qari_idx = st.selectbox("اختر القارئ:", options=range(len(qari_names)), format_func=lambda i: qari_names[i])
selected_qari = QURAA[selected_qari_idx]["id"]

sura_idx = st.selectbox("اختر السورة:", options=range(1, 115), format_func=lambda i: f"{i}. {SURA_NAMES[i-1]}")
ayah_count = 286 if sura_idx == 2 else (7 if sura_idx == 1 else 30) if sura_idx == 78 else 7  # يفضل جلب العدد الصحيح من كل سورة من جدول خارجي، هنا وضعنا قيم تقريبية لبعض السور
from_ayah = st.number_input("من الآية رقم:", min_value=1, max_value=ayah_count, value=1)
to_ayah = st.number_input("إلى الآية رقم:", min_value=from_ayah, max_value=ayah_count, value=from_ayah)

if st.button("إنشاء الفيديو"):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as merged_file:
            combined = None
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
                    combined = segment if combined is None else combined + segment
            combined.export(merged_file.name, format="mp3")
            audio_path = merged_file.name

        with st.spinner("جاري تحميل فيديو الخلفية الطبيعية..."):
            nature_video_url = get_random_nature_video_url()
            headers = {"User-Agent": "Mozilla/5.0"}
            bg_resp = requests.get(nature_video_url, stream=True, headers=headers)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as bg_file:
                for chunk in bg_resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        bg_file.write(chunk)
                bg_video_path = bg_file.name

        # دمج الصوت مع الفيديو
        from moviepy.editor import AudioFileClip
        st.info("جاري دمج الصوت مع الفيديو...")
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        bg_clip = VideoFileClip(bg_video_path)
        if bg_clip.duration >= duration:
            bg_clip = bg_clip.subclip(0, duration)
        else:
            loops = int(duration // bg_clip.duration) + 1
            clips = [bg_clip] * loops
            bg_clip = concatenate_videoclips(clips).subclip(0, duration)
        final_clip = bg_clip.set_audio(audio_clip)
        output_video_path = bg_video_path.replace(".mp4", "_output.mp4")
        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=24)
        st.success("تم إنشاء الفيديو بنجاح!")
        with open(output_video_path, "rb") as f:
            st.download_button("تحميل الفيديو الجديد", f, file_name="quran_ayat_with_nature.mp4", mime="video/mp4")
        st.video(output_video_path)
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
