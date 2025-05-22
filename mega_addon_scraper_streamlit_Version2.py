import streamlit as st
import requests
import re

st.title("منصة جمع إضافات وأسواق 3D تلقائياً (Streamlit Cloud)")

platform = st.selectbox(
    "اختر المنصة/السوق:",
    [
        "Blender Market",
        "Orbolt (Houdini)",
        "Unreal Marketplace",
        "SketchUp Extension Warehouse"
    ]
)

max_pages = {
    "Blender Market": 100,
    "Orbolt (Houdini)": 50,
    "Unreal Marketplace": 100,
    "SketchUp Extension Warehouse": 50
}

default_pages = {
    "Blender Market": 10,
    "Orbolt (Houdini)": 5,
    "Unreal Marketplace": 5,
    "SketchUp Extension Warehouse": 5
}

pages = st.number_input(
    "عدد الصفحات (كل صفحة من 20 إلى 30 إضافة):",
    min_value=1,
    max_value=max_pages[platform],
    value=default_pages[platform]
)

run = st.button("ابدأ الجمع الآن")

def collect_blender_market(pages):
    all_addons = set()
    for page in range(1, pages+1):
        url = f'https://blendermarket.com/products?page={page}'
        resp = requests.get(url)
        if not resp.ok:
            break
        found = re.findall(r'/products/([^"/?]+)', resp.text)
        all_addons.update(found)
    return all_addons

def collect_orbolt(pages):
    all_addons = set()
    for page in range(1, pages+1):
        url = f'https://www.orbolt.com/store/home?page={page}'
        resp = requests.get(url)
        if not resp.ok:
            break
        found = re.findall(r'/asset/([^"/?]+)', resp.text)
        all_addons.update(found)
    return all_addons

def collect_unreal_marketplace(pages):
    all_addons = set()
    for page in range(1, pages+1):
        url = f'https://www.unrealengine.com/marketplace/en-US/store?page={page}'
        resp = requests.get(url)
        if not resp.ok:
            break
        found = re.findall(r'/marketplace/en-US/product/([^"/?]+)', resp.text)
        all_addons.update(found)
    return all_addons

def collect_sketchup_extensions(pages):
    all_addons = set()
    for page in range(1, pages+1):
        url = f'https://extensions.sketchup.com/search?page={page}'
        try:
            resp = requests.get(url)
            if not resp.ok:
                break
            found = re.findall(r'/extension/([^"/?]+)', resp.text)
            all_addons.update(found)
        except Exception:
            break
    return all_addons

if run:
    st.info("يجري الجمع ... يرجى الانتظار قليلاً حسب عدد الصفحات")
    if platform == "Blender Market":
        addons = collect_blender_market(int(pages))
    elif platform == "Orbolt (Houdini)":
        addons = collect_orbolt(int(pages))
    elif platform == "Unreal Marketplace":
        addons = collect_unreal_marketplace(int(pages))
    elif platform == "SketchUp Extension Warehouse":
        addons = collect_sketchup_extensions(int(pages))
    else:
        addons = set()

    st.success(f"تم جمع {len(addons)} عنصر/إضافة بنجاح!")
    st.download_button(
        label="تحميل القائمة كملف نصي",
        data="\n".join(sorted(addons)),
        file_name=f"{platform.replace(' ','_').lower()}_addons.txt",
        mime="text/plain"
    )
    if addons:
        st.write("أمثلة من النتائج:")
        st.write(list(sorted(addons))[:30])
