import cv2
import numpy as np
import pickle
import glob
import os

CHESSBOARD_SIZE = (9, 6)      # inner corners (columns, rows)
SQUARE_SIZE_MM = 25.0         # measure your actual printed square size
OUTPUT_PATH = "calibration_data.pkl"
CAMERA_INDEX = 0


def run_calibration():
    # Prepare object points like (0,0,0), (1,0,0), ..., scaled by square size
    objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE_MM

    obj_points = []   # 3d points in real world space
    img_points = []   # 2d points in image plane

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Could not open camera.")
        return

    frame_size = None
    captured_count = 0

    print("Press 'c' to capture a frame when the chessboard is detected (green corners).")
    print("Press 'q' to finish capturing and run calibration.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_size = frame.shape[:2][::-1]  # (width, height)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        found, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)

        display = frame.copy()
        if found:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            refined_corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            cv2.drawChessboardCorners(display, CHESSBOARD_SIZE, refined_corners, found)

        cv2.putText(display, f"Captured: {captured_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Calibration - press 'c' to capture, 'q' to finish", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c') and found:
            obj_points.append(objp)
            img_points.append(refined_corners)
            captured_count += 1
            print(f"Captured frame {captured_count}")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if captured_count < 10:
        print(f"Only {captured_count} captures — you want at least ~10-15 for a decent calibration. "
              "Re-run and capture more if the results look off.")

    if captured_count == 0:
        print("No captures recorded, aborting.")
        return

    print("Running calibration...")
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        obj_points, img_points, frame_size, None, None
    )

    if not ret:
        print("Calibration failed.")
        return

    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]

    print("\n--- Calibration Results ---")
    print(f"fx: {fx:.3f}  fy: {fy:.3f}")
    print(f"cx: {cx:.3f}  cy: {cy:.3f}")
    print(f"Distortion coeffs: {dist_coeffs.ravel()}")

    # Reprojection error - sanity check. Should be well under 1.0 (pixels).
    total_error = 0
    for i in range(len(obj_points)):
        projected, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
        error = cv2.norm(img_points[i], projected, cv2.NORM_L2) / len(projected)
        total_error += error
    mean_error = total_error / len(obj_points)
    print(f"Mean reprojection error: {mean_error:.4f} px (lower is better, aim for < 0.5)")

    calibration_data = {
        "camera_matrix": camera_matrix,
        "dist_coeffs": dist_coeffs,
        "image_size": frame_size,
        "reprojection_error": mean_error,
    }

    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(calibration_data, f)

    print(f"\nSaved calibration to {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    run_calibration()