import time
import pyautogui
import config
from utils import EMASmoother
from gesture_recognizer import Gesture

pyautogui.FAILSAFE = True


class MouseController:
    """Gesture → pyautogui actions with trackpad edge-auto-move and smoothing."""

    def __init__(self):
        # Cursor / drag state
        self._move_smoother = EMASmoother()
        self._last_click_time = 0.0
        self._last_action_time = 0.0
        self._prev_fingertip = None
        self._is_dragging = False

        # Scroll state
        self._scroll_smoother = EMASmoother(alpha=config.SCROLL_EMA_ALPHA)
        self._prev_scroll_fingertip = None

    # ------------------------------------------------------------------
    # Track-zone helpers
    # ------------------------------------------------------------------

    def _track_zone_bounds(self):
        """Return (x1, y1, x2, y2) normalized tracking rectangle (centered)."""
        cx, cy = 0.5, 0.5
        hw, hh = config.TRACK_ZONE_W / 2, config.TRACK_ZONE_H / 2
        return cx - hw, cy - hh, cx + hw, cy + hh

    def _get_auto_move(self, fingertip):
        """If fingertip is in the border zone, return (dx, dy) auto-move delta.
        Speed ramps from AUTO_SPEED_BASE at the track-zone edge
        to AUTO_SPEED_MAX at the camera border. Returns (0, 0) inside track zone."""
        x, y = fingertip
        x1, y1, x2, y2 = self._track_zone_bounds()

        dx, dy = 0.0, 0.0

        if x < x1:
            factor = (x1 - x) / x1 if x1 > 0 else 0
            dx = -(config.AUTO_SPEED_BASE + factor * (config.AUTO_SPEED_MAX - config.AUTO_SPEED_BASE))
        elif x > x2:
            denom = 1.0 - x2
            factor = (x - x2) / denom if denom > 0 else 0
            dx = config.AUTO_SPEED_BASE + factor * (config.AUTO_SPEED_MAX - config.AUTO_SPEED_BASE)

        if y < y1:
            factor = (y1 - y) / y1 if y1 > 0 else 0
            dy = -(config.AUTO_SPEED_BASE + factor * (config.AUTO_SPEED_MAX - config.AUTO_SPEED_BASE))
        elif y > y2:
            denom = 1.0 - y2
            factor = (y - y2) / denom if denom > 0 else 0
            dy = config.AUTO_SPEED_BASE + factor * (config.AUTO_SPEED_MAX - config.AUTO_SPEED_BASE)

        return dx, dy

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def handle_gestures(self, gesture_results):
        now = time.time()

        for gesture, extra_data, hand_label in gesture_results:
            if gesture == Gesture.CURSOR_MOVE:
                self._do_cursor_move(extra_data.get('fingertip'))

            elif gesture == Gesture.DRAG:
                self._do_drag(extra_data.get('fingertip'))

            elif gesture == Gesture.CLICK:
                self._do_click(now)

            elif gesture == Gesture.SCROLL:
                self._do_scroll(extra_data.get('fingertip'))

        has_move_or_drag = any(
            g in (Gesture.CURSOR_MOVE, Gesture.DRAG)
            for g, _, _ in gesture_results
        )
        if not has_move_or_drag:
            self._reset_move_state()

        has_scroll = any(g == Gesture.SCROLL for g, _, _ in gesture_results)
        if not has_scroll:
            self._reset_scroll_state()

    # ------------------------------------------------------------------
    # Cursor move
    # ------------------------------------------------------------------

    def _do_cursor_move(self, fingertip):
        if fingertip is None:
            self._prev_fingertip = None
            return

        auto_dx, auto_dy = self._get_auto_move(fingertip)
        if auto_dx != 0 or auto_dy != 0:
            # Finger is in border zone → auto-move, reset tracking delta
            self._prev_fingertip = None
            sx, sy = self._move_smoother.update(auto_dx, auto_dy)
            pyautogui.moveRel(int(sx), int(sy), _pause=False)
            return

        x, y = fingertip
        if self._prev_fingertip is not None:
            px, py = self._prev_fingertip
            dx = (x - px) * config.CAMERA_WIDTH * config.CURSOR_SENSITIVITY
            dy = (y - py) * config.CAMERA_HEIGHT * config.CURSOR_SENSITIVITY
            sx, sy = self._move_smoother.update(dx, dy)
            pyautogui.moveRel(int(sx), int(sy), _pause=False)

        self._prev_fingertip = (x, y)

    # ------------------------------------------------------------------
    # Drag
    # ------------------------------------------------------------------

    def _do_drag(self, fingertip):
        if fingertip is None:
            return

        auto_dx, auto_dy = self._get_auto_move(fingertip)
        if auto_dx != 0 or auto_dy != 0:
            self._prev_fingertip = None
            sx, sy = self._move_smoother.update(auto_dx, auto_dy)
            if not self._is_dragging:
                pyautogui.mouseDown(button='left', _pause=False)
                self._is_dragging = True
            pyautogui.moveRel(int(sx), int(sy), _pause=False)
            return

        x, y = fingertip
        if self._prev_fingertip is not None:
            px, py = self._prev_fingertip
            dx = (x - px) * config.CAMERA_WIDTH * config.CURSOR_SENSITIVITY
            dy = (y - py) * config.CAMERA_HEIGHT * config.CURSOR_SENSITIVITY
            sx, sy = self._move_smoother.update(dx, dy)

            if not self._is_dragging:
                pyautogui.mouseDown(button='left', _pause=False)
                self._is_dragging = True
            pyautogui.moveRel(int(sx), int(sy), _pause=False)

        self._prev_fingertip = (x, y)

    # ------------------------------------------------------------------
    # Click / Double-click
    # ------------------------------------------------------------------

    def _do_click(self, now):
        if now - self._last_action_time < config.CLICK_COOLDOWN:
            return

        if now - self._last_click_time < config.DOUBLE_CLICK_WINDOW:
            pyautogui.doubleClick(_pause=False)
            self._last_click_time = 0.0
        else:
            pyautogui.click(_pause=False)
            self._last_click_time = now

        self._last_action_time = now

    # ------------------------------------------------------------------
    # Scroll (secondary hand fist)
    # ------------------------------------------------------------------

    def _do_scroll(self, fingertip):
        if fingertip is None:
            return
        x, y = fingertip

        if self._prev_scroll_fingertip is not None:
            _, py = self._prev_scroll_fingertip
            dy = (py - y) * config.CAMERA_HEIGHT * config.CURSOR_SENSITIVITY
            _, sy = self._scroll_smoother.update(0, dy)
            scroll_amount = int(sy * config.SCROLL_SENSITIVITY / config.CURSOR_SENSITIVITY)
            if scroll_amount != 0:
                pyautogui.scroll(scroll_amount, _pause=False)

        self._prev_scroll_fingertip = (x, y)

    # ------------------------------------------------------------------
    # State reset
    # ------------------------------------------------------------------

    def _reset_move_state(self):
        if self._is_dragging:
            pyautogui.mouseUp(button='left', _pause=False)
            self._is_dragging = False
        self._prev_fingertip = None
        self._move_smoother.reset()

    def _reset_scroll_state(self):
        self._prev_scroll_fingertip = None
        self._scroll_smoother.reset()
