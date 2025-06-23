import streamlit as st
import requests
import yt_dlp
import moviepy.editor as mp
import os
import uuid

# مفاتيح API
PEXELS_API_KEY = "YOUR_PEXELS_API_KEY"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="مولد فيديو القرآن بخلفية طبيعية", layout="centered")
st.title("🎬 مولد فيديو القرآن بخلفية مناظر طبيعية")

video_url = st.text_input("أدخل رابط فيديو القرآن (يوتيوب أو غيره):")

if st.button("ابدأ المعالجة") and video_url:
    st.info("جاري تحميل الفيديو...")
    random_id = str(uuid.uuid4())
    video_path = os.path.join(DOWNLOAD_DIR, f"input_{random_id}.mp4")
    audio_path = os.path.join(DOWNLOAD_DIR, f"audio_{random_id}.mp3")

    try:
        ydl_opts = {"outtmpl": video_path, "format": "bestvideo+bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        st.success("تم تحميل الفيديو!")

        # استخراج الصوت
        st.info("جاري استخراج الصوت...")
        video = mp.VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        st.audio(audio_path, format="audio/mp3")
        st.success("تم استخراج الصوت!")

        # جلب فيديو مناظر طبيعية من Pexels
        st.info("جاري جلب فيديو خلفية من Pexels...")
        headers = {'Authorization': PEXELS_API_KEY}
        params = {'query': 'nature', 'per_page': 1}
        response = requests.get('https://api.pexels.com/videos/search', headers=headers, params=params)
        if response.status_code == 200 and response.json()['videos']:
            bg_url = response.json()['videos'][0]['video_files'][0]['link']
            st.video(bg_url)
            st.success("تم جلب فيديو الخلفية!")
            st.markdown(f"[تحميل فيديو الخلفية من هنا]({bg_url})")
        else:
            st.error("تعذر جلب فيديو الخلفية من Pexels.")
        
        st.markdown("---")
        st.info("💡 يمكنك دمج الصوت مع الفيديو باستخدام مواقع مثل [Clideo](https://clideo.com/merge-video) أو [Online Convert](https://video.online-convert.com/convert-to-mp4) بسهولة.")

    except Exception as e:
        st.error(f"حدث خطأ: {str(e)}")
