from enum import Enum, auto
import config
from utils import calculate_distance, is_finger_extended


class Gesture(Enum):
    NONE = auto()
    CURSOR_MOVE = auto()   # open palm → move cursor
    DRAG = auto()           # fist → drag
    CLICK = auto()          # OK gesture / thumb-index pinch → left click
    SCROLL = auto()         # left hand fist → scroll wheel


class GestureRecognizer:
    """Pure logic: takes MediaPipe landmark lists, returns per-hand gestures."""

    def recognize(self, multi_hand_landmarks, handedness_list):
        """
        Returns a list of (Gesture, extra_data, hand_label) tuples,
        one per detected hand that has an active gesture.
        """
        results = []

        for i, landmarks in enumerate(multi_hand_landmarks):
            label = handedness_list[i][0].category_name  # "Left" or "Right"
            gesture, extra = self._recognize_single_hand(landmarks, label)
            if gesture != Gesture.NONE:
                results.append((gesture, extra, label))

        return results

    # ------------------------------------------------------------------
    # Single-hand gesture tree
    # ------------------------------------------------------------------

    def _recognize_single_hand(self, landmarks, hand_label):
        fingers_up = [
            is_finger_extended(landmarks, 8, 6),   # index
            is_finger_extended(landmarks, 12, 10),  # middle
            is_finger_extended(landmarks, 16, 14),  # ring
            is_finger_extended(landmarks, 20, 18),  # pinky
        ]

        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        dist_thumb_index = calculate_distance(thumb_tip, index_tip)
        all_four_extended = all(fingers_up)
        all_four_closed = not any(fingers_up)

        # Camera is mirrored → MediaPipe labels are inverted.
        # User's primary hand (e.g. "right") is reported as the opposite ("Left").
        is_primary = hand_label.lower() != config.PRIMARY_HAND.lower()

        # --- Primary hand (cursor / drag / click) ---
        if is_primary:
            # 1. OK Gesture → click
            if dist_thumb_index < config.CLICK_THRESHOLD and fingers_up[1] and fingers_up[2] and fingers_up[3]:
                return Gesture.CLICK, {}

            # 2. Fist → drag
            if all_four_closed:
                return Gesture.DRAG, {'fingertip': (index_tip.x, index_tip.y)}

            # 3. Open palm → cursor move
            if all_four_extended:
                return Gesture.CURSOR_MOVE, {'fingertip': (index_tip.x, index_tip.y)}

            # 4. Thumb-index pinch → click
            if fingers_up[0] and dist_thumb_index < config.CLICK_THRESHOLD:
                return Gesture.CLICK, {}

        # --- Secondary hand (scroll) ---
        else:
            # Fist → scroll
            if all_four_closed:
                return Gesture.SCROLL, {'fingertip': (index_tip.x, index_tip.y)}

        return Gesture.NONE, {}
