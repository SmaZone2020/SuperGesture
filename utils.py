import math
import config


def calculate_distance(p1, p2):
    """Euclidean distance between two MediaPipe NormalizedLandmark points."""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2)


def is_finger_extended(landmarks, tip_id, pip_id):
    """
    Returns True if the finger is extended (straight).
    In image coordinates Y grows downward, so an extended fingertip
    has a smaller Y than its PIP joint.
    landmarks is a list of NormalizedLandmark objects (MediaPipe Tasks API).
    """
    return landmarks[tip_id].y < landmarks[pip_id].y


def is_thumb_extended(landmarks):
    """
    Thumb extends sideways, so simple Y comparison doesn't work.
    We compare distances: tip-to-MCP vs IP-to-MCP.
    landmarks is a list of NormalizedLandmark objects.
    """
    tip = landmarks[4]
    ip = landmarks[3]
    mcp = landmarks[2]
    dist_tip_mcp = calculate_distance(landmarks[4], mcp)
    dist_ip_mcp = calculate_distance(ip, mcp)
    return dist_tip_mcp > dist_ip_mcp * 1.3


class EMASmoother:
    """Exponential Moving Average smoother for 2D coordinates."""

    def __init__(self, alpha=None):
        self.alpha = alpha if alpha is not None else config.EMA_ALPHA
        self.x = None
        self.y = None

    def update(self, x, y):
        if self.x is None:
            self.x, self.y = x, y
        else:
            self.x = self.alpha * x + (1 - self.alpha) * self.x
            self.y = self.alpha * y + (1 - self.alpha) * self.y
        return self.x, self.y

    def reset(self):
        self.x = None
        self.y = None


def get_hand_label(handedness):
    """Returns 'Left' or 'Right' string from MediaPipe Tasks handedness result."""
    return handedness[0].category_name


def get_fingertip_pos(landmarks, finger_id):
    """Return (x, y) normalized coordinates for a fingertip."""
    lm = landmarks[finger_id]
    return lm.x, lm.y
