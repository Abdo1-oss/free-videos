import streamlit as st
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from gtts import gTTS
import os

st.title("🎬 أداة دبلجة الفيديو بالذكاء الاصطناعي")

uploaded_file = st.file_uploader("📤 ارفع الفيديو", type=["mp4", "mov", "avi"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    st.video("input_video.mp4")

    st.info("⏳ جاري استخراج الصوت وتحويله لنص...")
    model = whisper.load_model("base")
    result = model.transcribe("input_video.mp4")
    original_text = result["text"]
    st.success("✅ تم نسخ الكلام!")

    st.text_area("🗣️ النص الأصلي:", original_text)

    # ترجمة بسيطة
    from googletrans import Translator
    translator = Translator()
    translated = translator.translate(original_text, dest='ar')
    arabic_text = translated.text
    st.text_area("🌍 الترجمة العربية:", arabic_text)

    # تحويل إلى صوت
    tts = gTTS(arabic_text, lang='ar')
    tts.save("arabic_audio.mp3")

    # تركيب الصوت الجديد على الفيديو
    st.info("🎛️ جاري دمج الصوت الجديد...")
    video = VideoFileClip("input_video.mp4")
    audio = AudioFileClip("arabic_audio.mp3")
    final_video = video.set_audio(audio)
    final_video.write_videofile("output_video.mp4", codec="libx264", audio_codec="aac")

    st.success("🎉 فيديوك المدبلج جاهز!")
    st.video("output_video.mp4")
    with open("output_video.mp4", "rb") as f:
        st.download_button("⬇️ تحميل الفيديو المدبلج", f, file_name="dubbed_video.mp4")
