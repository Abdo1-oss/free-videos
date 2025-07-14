import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO

def detect_faces_from_thumbnail(image_url):
    try:
        resp = requests.get(image_url, stream=True, timeout=5)
        if resp.status_code != 200:
            return False

        img = Image.open(BytesIO(resp.content)).convert('RGB')
        img_np = np.array(img)
        img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        face_cascade = cv2.CascadeClassifier("models/haarcascade_frontalface_default.xml")
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        return len(faces) > 0

    except Exception as e:
        print("Thumbnail analysis error:", e)
        return False
