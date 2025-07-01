import streamlit as st
import requests
import tempfile
import random
import os
from pydub import AudioSegment, silence
from moviepy.editor import (
    VideoFileClip, AudioFileClip, concatenate_videoclips, vfx
)
import cv2

# ------------ إعدادات API KEYS ------------
PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"
PIXABAY_API_KEY = "50380897-76243eaec536038f687ff8e15"

# ------------ قائمة أفضل الشيوخ من everyayah.com ------------
QURAA = [
    {"name": "الحصري مرتل", "id": "Husary_64kbps"},
    {"name": "المنشاوي مرتل", "id": "Minshawy_Murattal_128kbps"},
    {"name": "عبد الباسط مرتل", "id": "Abdul_Basit_Murattal_64kbps"},
    {"name": "الغامدي", "id": "Ghamadi_40kbps"},
    {"name": "المعيقلي", "id": "MaherAlMuaiqly_64kbps"},
    {"name": "العفاسي", "id": "Alafasy_64kbps"},
    {"name": "الشريم", "id": "Shuraym_64kbps"},
    {"name": "فارس عباد", "id": "Fares_Abbad_64kbps"},
    {"name": "الشاطري", "id": "Shatri_64kbps"},
    {"name": "أبو بكر الشاطري", "id": "Abu_Bakr_Ash-Shaatree_128kbps"},
    {"name": "محمد أيوب", "id": "Muhammad_Ayyoub_128kbps"},
    {"name": "ياسر الدوسري", "id": "Yasser_Ad-Dussary_128kbps"},
    {"name": "أحمد العجمي", "id": "Ajamy_64kbps"},
    {"name": "إدريس أبكر", "id": "Idrees_Abkar_48kbps"},
    {"name": "خليفة الطنيجي", "id": "Tunaiji_64kbps"},
    {"name": "عبد الله بصفر", "id": "Basfar_48kbps"},
    {"name": "الحصري مجود", "id": "Husary_Mujawwad_128kbps"},
    {"name": "محمد جبريل", "id": "Jibreel_64kbps"},
    {"name": "علي جابر", "id": "Ali_Jaber_64kbps"},
    {"name": "المنشاوي مجود", "id": "Minshawy_Mujawwad_128kbps"},
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

def is_people_video(video_text):
    people_keywords = [
        "person","people","man","woman","boy","girl","child","men","women","kids","kid","human","face",
        "portrait","selfie","friends","couple","wedding","bride","groom","student","students","woman face"
    ]
    # كلمات تخالف الشريعة أو تشير لأشياء محرمة
    haram_keywords = [
        "cross","church","pork","alcohol","beer","wine","christ","statue","idol","jesus","dance","music","singer","band",
        "gambling","casino","nude","naked","bikini","swimsuit","sexy","kiss","romance","dating","halloween","zombie","devil","witch"
    ]
    return any(word in video_text for word in people_keywords + haram_keywords)

def is_shorts(width, height, duration, min_duration=7, max_duration=120):
    ratio = width / height if height > 0 else 1
    return (ratio < 0.7) and (min_duration <= duration <= max_duration)

# ------------------ اقتراح كلمات مفتاحية بناءً على الآيات ------------------
def suggest_keywords(sura_idx, from_ayah, to_ayah):
    # قائمة كلمات مفتاحية شائعة
    generic_keywords = [
        "nature", "mountain", "river", "sea", "forest", "lake", "desert", "sunset", "waterfall", "clouds",
        "meadow", "valley", "rain", "sky", "island", "garden", "trees", "ocean", "snow", "rocks",
        "moon", "stars", "sun", "night", "light", "storm", "planet", "space", "galaxy", "universe",
        "space", "planet", "nebula", "stars", "galaxy", "universe", "cosmos", "astronomy", "earth", "moon"
    ]
    # كلمات فضاء، كواكب، قبور
    space_keywords = ["space", "universe", "galaxy", "cosmos", "nebula", "planets", "planet", "stars", "astronomy", "moon", "earth", "solar system"]
    graves_keywords = ["grave", "graves", "tomb", "cemetery", "gravesite", "graveyard"]
    # كلمات لمشاهد يوم القيامة أو البعث أو الآخرة
    qiyamah_keywords = ["judgement day", "apocalypse", "resurrection", "afterlife", "hereafter", "heaven", "hell", "dark clouds", "storm", "lightning", "end times"]
    
    # تحليل سطحي للسورة/الآيات
    # (يمكنك إضافة المزيد من السور والتحليل حسب الحاجة)
    sura_name = SURA_NAMES[sura_idx-1]
    ayat_text = ""
    try:
        # جلب نص الآيات من api
        from_ = int(from_ayah)
        to_ = int(to_ayah)
        url = f"https://api.alquran.cloud/v1/ayah/{sura_idx}:{from_}/ar"
        r = requests.get(url)
        if r.ok:
            ayat_text = r.json().get("data", {}).get("text", "")
    except Exception:
        pass
    
    keywords = generic_keywords.copy()
    if sura_name in ["الأنبياء", "الرحمن", "القيامة", "الواقعة", "الحاقة", "المعارج", "النبأ", "الزلزلة", "القارعة", "التكوير", "الانفطار", "المطففين", "الانشقاق"]:
        keywords += qiyamah_keywords
    if sura_name in ["الشمس", "القمر", "النجم", "الكهف", "الإسراء", "الحديد", "يس", "الصافات"]:
        keywords += space_keywords
    if ("قبر" in ayat_text) or (sura_name in ["التكاثر", "الزلزلة", "القارعة"]):
        keywords += graves_keywords
    # تحليل كلمات الآية
    if any(word in ayat_text for word in ["نجوم", "كواكب", "شمس", "قمر", "سحاب", "فضاء", "سماء", "ليل", "نهار", "ظلام", "نور"]):
        keywords += space_keywords
    if any(word in ayat_text for word in ["قبر", "قبور", "موت", "عظام", "تراب"]):
        keywords += graves_keywords
    if any(word in ayat_text for word in ["بحر", "ماء", "أنهار"]):
        keywords += ["sea", "ocean", "river", "water", "waves", "rain"]
    # لا تكرر الكلمات
    keywords = list(set(keywords))
    return keywords

def get_pexels_shorts_videos(api_key, needed_duration, keywords):
    headers = {"Authorization": api_key}
    shorts = []
    for keyword in keywords:
        params = {"query": keyword, "per_page": 40}
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
        try:
            videos = resp.json().get('videos', [])
        except Exception:
            continue
        for v in videos:
            desc = (v.get("description") or "").lower()
            user_name = (v.get("user", {}).get("name") or "").lower()
            tags = [t.lower() for t in v.get("tags",[])]
            text = " ".join(tags) + " " + desc + " " + user_name
            if is_people_video(text):
                continue
            for file in v["video_files"]:
                if file["quality"]=="hd" and is_shorts(file["width"], file["height"], v["duration"]):
                    shorts.append({"link": file["link"], "duration": v["duration"], "title": v.get("description",'')})
                    break
    return shorts

def get_pixabay_shorts_videos(api_key, needed_duration, keywords):
    shorts = []
    for keyword in keywords:
        params = {
            "key": api_key,
            "q": keyword,
            "per_page": 40,
            "video_type": "film",
            "safesearch": "true"
        }
        resp = requests.get("https://pixabay.com/api/videos/", params=params)
        try:
            videos = resp.json().get("hits", [])
        except Exception:
            continue
        for v in videos:
            text = (v.get("tags") or "").lower() + " " + (v.get("user") or "").lower()
            if is_people_video(text):
                continue
            for vid in v["videos"].values():
                if is_shorts(vid["width"], vid["height"], v["duration"]):
                    shorts.append({"link": vid["url"], "duration": v["duration"], "title": v.get("tags",'')})
                    break
    return shorts

def download_and_get_clip(url, used_links, resize=(1080,1920)):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, stream=True, headers=headers)
    if resp.status_code != 200:
        return None, None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as file:
        for chunk in resp.iter_content(chunk_size=1024*1024):
            if chunk:
                file.write(chunk)
        file.flush()
        clip = VideoFileClip(file.name).resize(newsize=resize)
        if clip.duration < 2:
            return None, file.name
        if url in used_links:
            return None, file.name
        used_links.add(url)
        return clip, file.name

def trim_silence(audio_segment, silence_thresh=-40, chunk_size=10):
    start_trim = silence.detect_leading_silence(audio_segment, silence_thresh, chunk_size)
    end_trim = silence.detect_leading_silence(audio_segment.reverse(), silence_thresh, chunk_size)
    duration = len(audio_segment)
    return audio_segment[start_trim:duration-end_trim]

def add_echo(sound, delay=250, attenuation=0.6):
    echo = sound - 20
    for i in range(1, 5):
        echo = echo.overlay(sound - int(20 + i*10), position=i*delay)
    return sound.overlay(echo)

def blur_frame(img, ksize=15):
    return cv2.GaussianBlur(img, (ksize|1, ksize|1), 0)

# Ken Burns (Zoom & Pan) effect
def ken_burns_effect(clip, zoom=1.1, pan_direction='left'):
    w, h = clip.size
    if pan_direction == 'left':
        return clip.fx(vfx.crop, x1=0, y1=0, x2=int(w*(1-1/zoom)), y2=0).fx(vfx.resize, width=w)
    elif pan_direction == 'right':
        return clip.fx(vfx.crop, x1=int(w*(1-1/zoom)), y1=0, x2=0, y2=0).fx(vfx.resize, width=w)
    else:  # center zoom
        return clip.fx(vfx.resize, lambda t: 1 + (zoom-1)*t/clip.duration)

# Vignette (تدرج لوني عند الحواف)
def add_vignette(clip, strength=0.6):
    import numpy as np
    def vignette(image):
        rows, cols = image.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, 200)
        kernel_y = cv2.getGaussianKernel(rows, 200)
        kernel = kernel_y * kernel_x.T
        mask = 255 * kernel / np.linalg.norm(kernel)
        for i in range(3):
            image[:,:,i] = image[:,:,i] * (1-strength) + mask * strength
        return image
    return clip.fl_image(vignette)

def montage_effects(clip, effect_name="random"):
    # قائمة التأثيرات بدون أي تأثير لوني يسبب زرقة أو تشبع غير مرغوب
    effects = [
        lambda c: c.fx(vfx.fadein, 1),
        lambda c: c.fx(vfx.fadeout, 1),
        lambda c: c.fx(vfx.blackwhite),
        lambda c: c.fl_image(lambda img: blur_frame(img, ksize=15)),
        lambda c: ken_burns_effect(c, zoom=1.13, pan_direction=random.choice(['left','right','center'])),
        lambda c: add_vignette(c, strength=0.3),
    ]
    if effect_name == "random":
        return random.choice(effects)(clip)
    else:
        return effects[0](clip)

# ------------ واجهة المستخدم ------------
st.set_page_config(page_title="فيديو قرآن شورتس بتأثيرات", layout="centered")
st.title("أنشئ فيديو قرآن قصير (شورتس) بخلفية جميلة وتأثيرات مونتاج")

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
add_montage_fx = st.checkbox("تفعيل تأثيرات مونتاج الفيديو (لون/تباين/تكبير/تدرج حواف...)", value=True)

video_sources = st.multiselect(
    "اختر مصادر الفيديو (يمكنك تحديد أكثر من مصدر):",
    options=["Pexels", "Pixabay"],
    default=["Pexels", "Pixabay"]
)

if st.button("إنشاء الفيديو"):
    try:
        # --------- اقتراح الكلمات المفتاحية للبحث ----------
        st.info("جاري اقتراح المشاهد المناسبة لموضوع الآيات...")
        keywords = suggest_keywords(sura_idx, from_ayah, to_ayah)
        st.caption(f"الكلمات المفتاحية المستخدمة: {', '.join(keywords[:10])} ...")
        
        with st.spinner("جاري تحميل ودمج الصوت لجميع الآيات..."):
            merged = None
            missing_ayahs = []
            default_silence_ms = 3000
            for ayah in range(int(from_ayah), int(to_ayah)+1):
                mp3_url = f"https://everyayah.com/data/{selected_qari}/{sura_idx:03d}{ayah:03d}.mp3"
                r = requests.get(mp3_url)
                if r.status_code != 200:
                    missing_ayahs.append(ayah)
                    segment = AudioSegment.silent(duration=default_silence_ms)
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_ayah_file:
                        temp_ayah_file.write(r.content)
                        temp_ayah_file.flush()
                        segment = AudioSegment.from_mp3(temp_ayah_file.name)
                        segment = trim_silence(segment)
                merged = segment if merged is None else merged + segment

            if not merged:
                st.error("لم يتم العثور على أي آية صوتية متاحة لهذا القارئ في هذا المقطع.")
                st.stop()
            if add_echo_effect:
                merged = add_echo(merged)
            # تلاشي تدريجي في النهاية أطول (8 ثوان أو 40% من مدة الصوت)
            fade_in_duration_ms = 2000
            fade_out_duration_ms = min(8000, int(len(merged) * 0.4))
            merged = merged.fade_in(fade_in_duration_ms).fade_out(fade_out_duration_ms)
            if missing_ayahs:
                st.warning(f"بعض الآيات غير متوفرة للقارئ المختار وتم وضع صمت مكانها: {', '.join(str(a) for a in missing_ayahs)}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as merged_file:
                merged.export(merged_file.name, format="mp3")
                audio_path = merged_file.name

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        with st.spinner("جاري تحميل وتجهيز فيديوهات الخلفية..."):
            video_clips = []
            used_links = set()
            shorts = []
            if "Pexels" in video_sources:
                shorts += get_pexels_shorts_videos(PEXELS_API_KEY, duration, keywords)
            if "Pixabay" in video_sources:
                shorts += get_pixabay_shorts_videos(PIXABAY_API_KEY, duration, keywords)

            random.shuffle(shorts)
            downloaded_duration = 0.0
            shorts_index = 0
            while downloaded_duration < duration and shorts_index < len(shorts):
                video_obj = shorts[shorts_index]
                link = video_obj["link"]
                shorts_index += 1
                if link in used_links:
                    continue
                clip, fname = download_and_get_clip(link, used_links)
                if not clip:
                    continue
                if add_blur:
                    clip = clip.fl_image(lambda image: blur_frame(image, ksize=15))
                if add_montage_fx:
                    clip = montage_effects(clip, effect_name="random")
                if downloaded_duration + clip.duration > duration:
                    clip = clip.subclip(0, duration-downloaded_duration)
                video_clips.append(clip)
                downloaded_duration += clip.duration
            if not video_clips or downloaded_duration < duration:
                st.error("لم يتم العثور على فيديوهات كافية أو مناسبة لتغطية مدة الصوت. حاول مجددًا أو غيّر المصدر أو قلل المقطع الصوتي.")
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
