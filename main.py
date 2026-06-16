import sys
import os

os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2
import pyautogui
from mediapipe import Image, ImageFormat
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.core.base_options import BaseOptions
import config
from gesture_recognizer import GestureRecognizer, Gesture
from mouse_controller import MouseController

MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")


def _track_zone_bounds(w, h):
    """Return pixel (x1, y1, x2, y2) of the center tracking rectangle."""
    cx, cy = 0.5, 0.5
    hw, hh = config.TRACK_ZONE_W / 2, config.TRACK_ZONE_H / 2
    return (
        int((cx - hw) * w), int((cy - hh) * h),
        int((cx + hw) * w), int((cy + hh) * h),
    )


def _draw_ui(frame, gesture_results):
    h, w = frame.shape[:2]

    # Border zone — semi-transparent red overlay (outside track zone)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 60), -1)
    x1, y1, x2, y2 = _track_zone_bounds(w, h)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

    # Track zone — green rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Crosshair at center
    cx, cy = w // 2, h // 2
    cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 0), 1)
    cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 0), 1)

    # Labels
    if gesture_results:
        y_off = 30
        for gesture, extra, hand_label in gesture_results:
            text = f"{hand_label}: {gesture.name}"
            cv2.putText(frame, text, (10, y_off),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_off += 28
    else:
        cv2.putText(frame, "IDLE", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)


def main():
    if not os.path.exists(MODEL_PATH):
        print(f"[SuperGesture] Model not found: {MODEL_PATH}")
        print("  Download it from:")
        print("  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task")
        sys.exit(1)

    recognizer = GestureRecognizer()
    controller = MouseController()

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=config.MAX_NUM_HANDS,
        min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

    print("[SuperGesture] Starting virtual touchpad...")
    print("  Green rectangle = tracking zone (normal movement)")
    print("  Red border area  = edge-auto-move zone")
    print("  Right hand:")
    print("    Open palm + move   ->  cursor move")
    print("    Fist + move        ->  drag")
    print("    OK / pinch         ->  click (double-click if fast)")
    print("  Left hand:")
    print("    Fist + move up/down   ->  scroll wheel")
    print("    Fist + move left/right ->  zoom (Ctrl+scroll)")
    print("    OK gesture            ->  right click")
    print("  Press 'q' to quit.")
    print("  FAILSAFE: fling mouse to top-left corner to emergency-stop.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)

        result = detector.detect(mp_image)

        gesture_results = []
        if result.hand_landmarks:
            gesture_results = recognizer.recognize(
                result.hand_landmarks,
                result.handedness,
            )

        try:
            controller.handle_gestures(gesture_results)
        except pyautogui.FailSafeException:
            print("\n[SuperGesture] FAILSAFE triggered — exiting.")
            break

        if config.DRAW_LANDMARKS and result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    vision.HandLandmarksConnections.HAND_CONNECTIONS,
                )

        _draw_ui(frame, gesture_results)

        cv2.imshow("SuperGesture — Virtual Touchpad", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    print("[SuperGesture] Exited cleanly.")


if __name__ == "__main__":
    main()
