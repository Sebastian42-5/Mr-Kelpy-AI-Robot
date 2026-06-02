import os
import pickle
import cv2
from skimage.metrics import structural_similarity as ssim
from deepface import DeepFace

FACE_DB_PATH = 'face_memory/face_db.pkl'
FACE_IMAGES_DIR = 'face_memory/face_images'

def load_db(db_path=FACE_DB_PATH):
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            return pickle.load(f)
    else:
        return {}

def get_similarity_score(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score