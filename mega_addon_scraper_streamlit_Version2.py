import streamlit as st
import yt_dlp
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import tempfile
import random
import os

# ضع مفتاح Pexels API الخاص بك هنا
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
st.title("أنشئ فيديو قرآن بخلفية طبيعية من رابط يوتيوب")

video_url = st.text_input("ألصق رابط فيديو يوتيوب للقرآن:")

if st.button("إنشاء الفيديو"):
    if not video_url:
        st.warning("يرجى وضع رابط فيديو أولاً")
        st.stop()

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. تحميل الفيديو من يوتيوب
        st.info("جاري تحميل الفيديو من يوتيوب...")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{tmpdir}/input.%(ext)s',
            'quiet': True,
            'merge_output_format': 'mp4',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحميل الفيديو من يوتيوب: {e}")
            st.stop()

        # ابحث عن ملف الفيديو الذي تم تحميله
        input_video_path = None
        for file in os.listdir(tmpdir):
            if file.endswith(".mp4"):
                input_video_path = os.path.join(tmpdir, file)
        if input_video_path is None:
            st.error("لم يتم العثور على ملف الفيديو!")
            st.stop()

        # 2. استخراج الصوت من الفيديو
        try:
            st.info("جاري استخراج الصوت من الفيديو...")
            video_clip = VideoFileClip(input_video_path)
            audio_clip = video_clip.audio
            duration = video_clip.duration
        except Exception as e:
            st.error(f"حدث خطأ أثناء استخراج الصوت: {e}")
            st.stop()

        # 3. تحميل فيديو خلفية الطبيعة
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

        # 4. دمج الصوت مع خلفية الطبيعة
        try:
            st.info("جاري تركيب الصوت على الخلفية الطبيعية...")
            bg_clip = VideoFileClip(bg_video_path)
            # كرر الخلفية إذا كانت أقصر من الصوت
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
