"""
Virtual Touchpad Gesture Control — Configuration
Tune all parameters here without touching logic files.
"""

# --- Camera ---
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# --- MediaPipe ---
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7
MAX_NUM_HANDS = 2

# --- Sensitivity (higher = faster cursor) ---
CURSOR_SENSITIVITY = 2.5
SCROLL_SENSITIVITY = 40
ZOOM_SENSITIVITY = 80

# --- Gesture distance thresholds (normalized 0..1 coords) ---
CLICK_THRESHOLD = 0.05

# --- Cooldowns (seconds) ---
CLICK_COOLDOWN = 0.35
DOUBLE_CLICK_WINDOW = 0.35
ZOOM_COOLDOWN = 0.5

# --- Trackpad edge-auto-move zone (normalized, centered in frame) ---
# Finger inside this rectangle = normal tracking
# Finger outside (between rectangle and camera border) = auto-move in that direction
TRACK_ZONE_W = 0.55            # width ratio of center tracking zone
TRACK_ZONE_H = 0.55            # height ratio of center tracking zone
AUTO_SPEED_BASE = 8            # base px/frame when just outside the tracking zone
AUTO_SPEED_MAX = 30            # max px/frame at the camera border

# --- Smoothing ---
EMA_ALPHA = 0.25
SCROLL_EMA_ALPHA = 0.4

# --- Hand preference ---
PRIMARY_HAND = "right"

# --- Debug ---
DRAW_LANDMARKS = True
DRAW_GESTURE_LABEL = True
