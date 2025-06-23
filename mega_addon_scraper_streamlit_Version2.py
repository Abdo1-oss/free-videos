import streamlit as st
import yt_dlp
import requests
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeVideoClip
import tempfile
import os
import random

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
    # نأخذ نسخة متوسطة الجودة
    for f in video["video_files"]:
        if f["quality"] == "hd" and f["width"] <= 1280:
            return f["link"]
    return video["video_files"][0]["link"]

st.set_page_config(page_title="إنشاء فيديو قرآن بخلفية طبيعية", layout="centered")
st.title("إنشاء فيديو قرآن بخلفية طبيعية متغيرة (من رابط يوتيوب)")

video_url = st.text_input("ألصق رابط فيديو القرآن من يوتيوب:")

if st.button("إنشاء الفيديو"):
    if not video_url:
        st.warning("يرجى وضع رابط فيديو أولاً")
        st.stop()

    with st.spinner("جاري تحميل فيديو الطبيعة..."):
        try:
            nature_video_url = get_random_nature_video_url()
            bg_resp = requests.get(nature_video_url, stream=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as bg_file:
                for chunk in bg_resp.iter_content(chunk_size=1024*1024):
                    if chunk:
                        bg_file.write(chunk)
                bg_video_path = bg_file.name
        except Exception as e:
            st.error(f"حدث خطأ أثناء جلب فيديو الطبيعة: {e}")
            st.stop()

    with st.spinner("جاري تحميل الصوت من يوتيوب..."):
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{tmpdir}/audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
            except Exception as e:
                st.error(f"حدث خطأ أثناء تحميل الصوت: {e}")
                st.stop()

            audio_path = None
            for file in os.listdir(tmpdir):
                if file.endswith(".mp3"):
                    audio_path = os.path.join(tmpdir, file)
            if audio_path is None:
                st.error("لم يتم العثور على ملف الصوت!")
                st.stop()

            st.info("جاري إنشاء الفيديو النهائي...")
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration

            # قص أو كرر فيديو الطبيعة ليطابق مدة الصوت
            bg_clip = VideoFileClip(bg_video_path)
            if bg_clip.duration >= duration:
                bg_clip = bg_clip.subclip(0, duration)
            else:
                # كرر الفيديو ليصل لنفس مدة الصوت
                loops = int(duration // bg_clip.duration) + 1
                bg_clip = concatenate_videoclips([bg_clip] * loops).subclip(0, duration)

            final_clip = bg_clip.set_audio(audio_clip)
            output_video_path = os.path.join(tmpdir, "output.mp4")
            final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=24)

            st.success("تم إنشاء الفيديو بنجاح!")
            with open(output_video_path, "rb") as f:
                st.download_button("تحميل الفيديو الجديد", f, file_name="quran_with_nature.mp4", mime="video/mp4")
            st.video(output_video_path)
