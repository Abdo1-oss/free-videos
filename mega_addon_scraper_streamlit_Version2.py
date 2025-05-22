import streamlit as st
import requests
import re

st.title("جمع إضافات Unreal Marketplace تلقائياً (Streamlit Cloud)")

pages = st.number_input(
    "عدد الصفحات (كل صفحة فيها إضافات عديدة):",
    min_value=1,
    max_value=20,
    value=3
)

run = st.button("ابدأ الجمع الآن")

def collect_unreal_marketplace(pages):
    all_addons = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    for page in range(1, pages+1):
        url = f'https://www.unrealengine.com/marketplace/en-US/store?page={page}'
        resp = requests.get(url, headers=headers)
        if not resp.ok:
            st.error(f"لم يتم جلب الصفحة رقم {page} (status code: {resp.status_code})")
            continue
        found = re.findall(r'/marketplace/en-US/product/([^"/?]+)', resp.text)
        all_addons.update(found)
    return all_addons

if run:
    st.info("يجري الجمع ... يرجى الانتظار قليلاً حسب عدد الصفحات")
    addons = collect_unreal_marketplace(int(pages))
    st.success(f"تم جمع {len(addons)} عنصر/إضافة بنجاح!")
    if addons:
        st.write("أمثلة من النتائج:")
        st.write(list(sorted(addons))[:30])
        st.download_button(
            label="تحميل القائمة كملف نصي",
            data="\n".join(sorted(addons)),
            file_name="unreal_marketplace_addons.txt",
            mime="text/plain"
        )
