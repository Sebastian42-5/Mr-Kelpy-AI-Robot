import os
import pickle
import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np
from deepface import DeepFace

FACE_DB_PATH = 'face_memory/face_db.pkl'
FACE_IMAGES_DIR = 'face_memory/face_images'

CLUSTER_ASSOCIATION_THRESHOLD = 0.55
NAME_SIMILARITY_THRESHOLD = 0.60
MIN_CLUSTER_REQUIRED_TO_NAME = 3

only_named = True

""" 
Each cluster has an id, a centroid, embeddings and image paths

"""

def load_db(db_path=FACE_DB_PATH):
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            return pickle.load(f)
    else:
        return {'clusters': []}
    
def save_db(face_db):
    with open(FACE_DB_PATH, "f") as file:
        pickle.dump(face_db, file)

def get_face_embedding(face_bgr_cut):
    """
    Returns L2 normalized vector face embedding using deepface
    """
    try:
        result = DeepFace.represent(
        img_path=face_bgr_cut,
        model_name="Facenet512",
        detector_backend="skip",   
        enforce_detection=False,
    )
        vec = np.array(result[0]["embedding"], dtype=np.float32)

        norm = np.linalg.norm(vec)

        if norm == 0:
            return None
        else:
            return vec / norm
    except Exception as e:
        return None

def cosine_similarity(veca, vecb):
    return float(np.dot(veca, vecb))

def update_cluster_centroid(cluster):
    centroid = np.mean(cluster)
    norm = np.linalg.norm(centroid)
    if norm == 0:
        return centroid
    return centroid / norm

def find_most_accurate_cluster(db, current_embed, only_named):
    best_index = 0 
    best_similarity = 0 

    if only_named:
        threshold = NAME_SIMILARITY_THRESHOLD
    else:
        threshold = CLUSTER_ASSOCIATION_THRESHOLD

    for i, centroid in enumerate(db):
        if only_named and db["name"] is None:
            continue
        similarity = cosine_similarity(centroid, current_embed)
        if similarity > best_similarity:
            best_index = i 
            best_similarity = similarity 
    
    if best_index is not None and best_similarity >= threshold:
        return best_index, best_similarity
    else:
        return 0.0, None
               

def process_face(face_crop_bgr, frame_index):
    current_embed = get_face_embedding(face_crop_bgr)

    if current_embed is None:
        return None

    db = load_db(FACE_DB_PATH)
    best_index, best_similarity = find_most_accurate_cluster(db, current_embed, only_named)

    if best_index is not None:
        cluster_id = db["clusters"][best_index]["id"]
    # it's a new cluster
    else:
        cluster_id = len(db["clusters"])
    
    img_filename = f"face_memory/images/cluster{cluster_id}_frame{frame_index}.jpg"
    cv2.imwrite(img_filename, face_crop_bgr)

    if best_index is not None: # if the embedding is already on the db
        cluster = db["clusters"][cluster_id]
        cluster["embeddings"].append(current_embed)
        cluster["image_paths"].append(img_filename)
        update_cluster_centroid(cluster)
        print(f"the size of cluster {cluster_id} is now {len(cluster["embeddings"])}")
    else:
        new_cluster = {
            "id": cluster_id,  
            "name": None,
            "embeddings": [current_embed],
            "image_paths": [img_filename],
            "centroid": None,

        }
        db["clusters"].append(new_cluster)
    save_db(db)
    return cluster


def get_similarity_score(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    img1_gray = cv2.cvtColor(img1_path, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2_path, cv2.COLOR_BGR2GRAY)

    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def associate_name_with_face(current_embed, name):
    db = load_db(FACE_DB_PATH)

    best_index = -1
    best_similarity = 0

    if current_embed not in db["clusters"]:
        return False
    
    for i, cluster in enumerate(db["clusters"]):
        similarity_index = cosine_similarity(db["clusters"][i], cluster)

        if similarity_index > best_similarity:
            best_index = i 
            best_similarity = similarity_index
        
        if similarity_index > CLUSTER_ASSOCIATION_THRESHOLD:
            db["clusters"]["name"] = name
        
        save_db(db)




    pass

def recognize_face():
    pass

def get_most_recently_added_face_embedding():
    pass