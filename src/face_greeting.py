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
    os.makedirs(os.path.dirname(FACE_DB_PATH), exist_ok=True)
    with open(FACE_DB_PATH, "wb") as file:
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

def update_cluster_centroid(embeddings):
    centroid = np.mean(embeddings, axis=0)
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

    for i, cluster in enumerate(db["clusters"]):
        if only_named and cluster["name"] is None:
            continue
        similarity = cosine_similarity(cluster["centroid"], current_embed)
        if similarity > best_similarity:
            best_index = i 
            best_similarity = similarity 
    
    if best_index is not None and best_similarity >= threshold:
        return best_index, best_similarity
    else:
        return None, 0.0
               

def process_face(face_crop_bgr, frame_count):
    current_embed = get_face_embedding(face_crop_bgr)

    if current_embed is None:
        return None

    db = load_db(FACE_DB_PATH)
    best_index, best_similarity = find_most_accurate_cluster(db, current_embed, only_named=False)

    if best_index is not None:
        cluster = db["clusters"][best_index]
    # it's a new cluster
    else:
        cluster = {
            "id": len(db["clusters"]),
            "name": None,
            "embeddings": [],
            "image_paths": [],
            "centroid": None,
        }
        db["clusters"].append(cluster)
 
        os.makedirs(FACE_IMAGES_DIR, exist_ok=True)
        img_filename = f"{FACE_IMAGES_DIR}/cluster{cluster['id']}_frame{frame_count}.jpg"
        cv2.imwrite(img_filename, face_crop_bgr)
    
        cluster["embeddings"].append(current_embed)
        cluster["image_paths"].append(img_filename)
        cluster["centroid"] = update_cluster_centroid(cluster["embeddings"]) 
    
        print(f"the size of cluster {cluster['id']} is now {len(cluster['embeddings'])}")
    
        save_db(db)
        return cluster


def get_similarity_score(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score


def associate_name_with_face(current_embed, name):
    db = load_db(FACE_DB_PATH)
    
    best_index, best_similarity = find_most_accurate_cluster(db, current_embed, only_named=False)

    if best_index is None or best_similarity < CLUSTER_ASSOCIATION_THRESHOLD:
        print("No name matches with this cluster")
        return False
    
    db["clusters"][best_index]["name"] = name
    
    save_db(db)
    return True



def recognize_face(current_embed):
    db = load_db(FACE_DB_PATH)

    best_index, best_similarity = find_most_accurate_cluster(db, current_embed, only_named=True)
    
    if best_index is not None:
        name = db["clusters"][best_index]["name"]
        print(f"The name associated to that face is {name} with a similarity of {best_similarity:.3f}")
        return name
    return None


def get_most_recently_added_face_embedding(db_snapshot):
    db = db_snapshot or load_db(FACE_DB_PATH)
    recently_grown_cluster = None 

    for cluster in db["clusters"]:
        if recently_grown_cluster is None:
            recently_grown_cluster = cluster 
        elif len(cluster["embeddings"]) >= len(recently_grown_cluster["embeddings"]):
            recently_grown_cluster = cluster
    
    if recently_grown_cluster:
        return recently_grown_cluster["embeddings"][-1]
    return None