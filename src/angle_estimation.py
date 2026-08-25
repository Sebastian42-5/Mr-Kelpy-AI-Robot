import cv2
import math 
import pickle


CALIBRATION_PATH = "calibration_data.pkl"

_camera_matrix = None
_dist_coeffs = None

def load_calibration(path: str = CALIBRATION_PATH):
    global _camera_matrix, _dist_coeffs

    with open(path, "rb") as f:
        data = pickle.load(f)

    _camera_matrix = data['camera_matrix']
    _dist_coeffs = data['dist_coeffs']

    fx = _camera_matrix[0, 0]
    fy = _camera_matrix[1, 1]
    cx = _camera_matrix[0, 2]
    cy = _camera_matrix[1, 2]

    print(f"Loaded calibration: fx={fx:.2f} fy={fy:.2f} cx={cx:.2f} cy={cy:.2f}")
    return _camera_matrix, _dist_coeffs

def get_camera_matrix():
    if _camera_matrix is None:
        raise RuntimeError("Calibration not loaded. Call load_calibration() first.")
    return _camera_matrix


def find_angle_from_pixel_center(pixel_x, pixel_y):

    if _camera_matrix is None:
        raise RuntimeError("Calibration not loaded")
    
    fx = _camera_matrix[0, 0]
    fy = _camera_matrix[1, 1]
    cx = _camera_matrix[0, 2]
    cy = _camera_matrix[1, 2]

    x_offset = pixel_x - cx
    y_offset = pixel_y - cy 

    angle_x = math.atan2(x_offset, fx)
    angle_y = math.atan2(y_offset, fy)

    return angle_x * 100, angle_y * 100
    

def find_angle_from_bbox(x1, y1, x2, y2):
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return center_x, center_y
    