import streamlit as st
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips
import tempfile
import requests
import random
import os

# ضع مفتاح Pexels API هنا
PEXELS_API_KEY = "pLcIoo3oNdhqna28AfdaBYhkE3SFps9oRGuOsxY3JTe92GcVDZpwZE9i"

def get_random_nature_video_url():
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": "nature", "per_page": 50}
    resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    resp.raise_for_status()
    videos = resp.json().get('videos', [])
    if not videos:
        raise Exception("لم يتم العثور على فيديوهات طبيعة!")
    video = random.choice(videos)
    # نختار جودة جيدة
    for f in video["video_files"]:
        if f["quality"] == "hd" and f["width"] <= 1280:
            return f["link"]
    return video["video_files"][0]["link"]

st.set_page_config(page_title="فيديو قرآن بخلفية طبيعية", layout="centered")
st.title("أنشئ فيديو قرآن بخلفية طبيعية متغيرة")

st.markdown("""
**الخطوات:**
1. الصق رابط فيديو يوتيوب للقرآن في الحقل أدناه.
2. اضغط على الزر لتحويل الفيديو إلى MP3 في موقع خارجي.
3. بعد التحويل، قم بتنزيل ملف MP3 وارفعه هنا لإكمال صناعة الفيديو بالخلفية الطبيعية.
""")

video_url = st.text_input("ألصق رابط فيديو يوتيوب للقرآن:")

if video_url:
    # رابط إلى ytmp3.cc مع توضيح للمستخدم
    st.markdown(
        f"[اضغط هنا لتحويل رابط يوتيوب إلى MP3 (يفتح في نافذة جديدة)](https://ytmp3.cc/youtube-to-mp3/{video_url})"
    )
    st.info("بعد التحويل، قم بتنزيل ملف MP3 الناتج وارفعه بالأسفل.")

uploaded_file = st.file_uploader("ارفع ملف MP3 الناتج هنا", type=["mp3"])

if uploaded_file:
    st.success("تم رفع الملف بنجاح! يمكنك الآن متابعة صناعة الفيديو بالخلفية الطبيعية.")
    if st.button("إنشاء الفيديو"):
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

        # حفظ ملف الصوت مؤقتًا
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
            audio_file.write(uploaded_file.read())
            audio_path = audio_file.name

        try:
            st.info("جاري معالجة الفيديو والصوت...")
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            bg_clip = VideoFileClip(bg_video_path)
            # إذا كانت الخلفية أقصر من الصوت، كرر الخلفية
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
                st.download_button("تحميل الفيديو الجديد", f, file_name="quran_with_nature.mp4", mime="video/mp4")
            st.video(output_video_path)
        except Exception as e:
            st.error(f"حدث خطأ أثناء إنشاء الفيديو: {e}")
