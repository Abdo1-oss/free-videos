import streamlit as st
from pytube import YouTube
import tempfile
import requests
import random
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips
import os

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

st.title("أنشئ فيديو قرآن بخلفية طبيعية من يوتيوب (بدون FFmpeg)")

video_url = st.text_input("ألصق رابط فيديو يوتيوب للقرآن:")

if st.button("إنشاء الفيديو"):
    if not video_url:
        st.warning("يرجى وضع رابط فيديو أولاً")
        st.stop()

    with st.spinner("جاري تحميل الصوت من يوتيوب..."):
        try:
            yt = YouTube(video_url)
            audio_stream = yt.streams.filter(only_audio=True, file_extension='webm').first()
            if not audio_stream:
                audio_stream = yt.streams.filter(only_audio=True).first()
            if not audio_stream:
                st.error("لم يتم العثور على مسار صوتي مناسب.")
                st.stop()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as audio_file:
                audio_stream.download(filename=audio_file.name)
                audio_path = audio_file.name
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحميل الصوت: {e}")
            st.stop()

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

    # معالجة ودمج الصوت مع الخلفية
    try:
        st.info("جاري معالجة الصوت والفيديو...")
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
            st.download_button("تحميل الفيديو الجديد", f, file_name="quran_with_nature.mp4", mime="video/mp4")
        st.video(output_video_path)
    except Exception as e:
        st.error(f"حدث خطأ أثناء إنشاء الفيديو: {e}")
