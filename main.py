import cv2
import mediapipe as mp
import pyautogui
import ctypes
import math


# =========================================================
# SETTINGS
# =========================================================

CAMERA_INDEX = 0

# Mouse movement
FRAME_MARGIN = 100
SMOOTHING = 0.25

# Pinch distance
PINCH_THRESHOLD = 0.055

# Windows global media key
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


# =========================================================
# INITIAL SETUP
# =========================================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()

# Previous mouse position for smoothing
smooth_x = screen_width / 2
smooth_y = screen_height / 2

# Used to prevent repeated actions
last_discrete_gesture = "NONE"


# =========================================================
# HELPERS
# =========================================================

def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def media_play_pause():
    """
    Global Windows Media Play/Pause.
    Works even when browser/media player is in background.
    """

    user32 = ctypes.windll.user32

    # Key down
    user32.keybd_event(
        VK_MEDIA_PLAY_PAUSE,
        0,
        0,
        0
    )

    # Key up
    user32.keybd_event(
        VK_MEDIA_PLAY_PAUSE,
        0,
        KEYEVENTF_KEYUP,
        0
    )

    print("PLAY / PAUSE")


# =========================================================
# FINGER STATES
# =========================================================

def finger_states(hand_landmarks):
    """
    Returns states for:
    index, middle, ring, pinky

    True = open
    False = closed

    Thumb is handled separately because thumb direction
    is used for slide control.
    """

    lm = hand_landmarks.landmark

    index = lm[8].y < lm[6].y
    middle = lm[12].y < lm[10].y
    ring = lm[16].y < lm[14].y
    pinky = lm[20].y < lm[18].y

    return index, middle, ring, pinky


# =========================================================
# GESTURE DETECTION
# =========================================================

def detect_gesture(hand_landmarks):

    lm = hand_landmarks.landmark

    index, middle, ring, pinky = finger_states(
        hand_landmarks
    )

    # Thumb-index distance
    pinch_distance = distance(
        lm[4],
        lm[8]
    )


    # =====================================================
    # OK SIGN
    #
    # Thumb + Index touching
    # Middle, Ring, Pinky open
    # =====================================================

    if (
        pinch_distance < PINCH_THRESHOLD
        and middle
        and ring
        and pinky
    ):
        return "PLAY_PAUSE"


    # =====================================================
    # CLICK
    #
    # Thumb + Index touching
    # Middle, Ring, Pinky closed
    # =====================================================

    if (
        pinch_distance < PINCH_THRESHOLD
        and not middle
        and not ring
        and not pinky
    ):
        return "CLICK"


    # =====================================================
    # THUMB UP / DOWN
    #
    # Other fingers must be closed
    # =====================================================

    other_fingers_closed = (
        not index
        and not middle
        and not ring
        and not pinky
    )

    if other_fingers_closed:

        thumb_tip = lm[4]
        thumb_mcp = lm[2]

        vertical_difference = (
            thumb_tip.y - thumb_mcp.y
        )

        horizontal_difference = abs(
            thumb_tip.x - thumb_mcp.x
        )

        # Thumb must be mainly vertical
        if abs(vertical_difference) > horizontal_difference:

            # Smaller Y = higher in image
            if vertical_difference < -0.08:
                return "NEXT"

            # Larger Y = lower in image
            if vertical_difference > 0.08:
                return "PREVIOUS"


    # =====================================================
    # MOUSE CONTROL
    #
    # Index finger only
    # =====================================================

    if (
        index
        and not middle
        and not ring
        and not pinky
    ):
        return "MOUSE"


    return "NONE"


# =========================================================
# MOUSE MOVEMENT
# =========================================================

def move_mouse(
    hand_landmarks,
    frame_width,
    frame_height
):

    global smooth_x
    global smooth_y

    lm = hand_landmarks.landmark

    # Index fingertip
    index_tip = lm[8]

    camera_x = int(
        index_tip.x * frame_width
    )

    camera_y = int(
        index_tip.y * frame_height
    )


    # =====================================================
    # ACTIVE CAMERA AREA
    # =====================================================

    min_x = FRAME_MARGIN
    max_x = frame_width - FRAME_MARGIN

    min_y = FRAME_MARGIN
    max_y = frame_height - FRAME_MARGIN


    # Clamp
    camera_x = max(
        min_x,
        min(camera_x, max_x)
    )

    camera_y = max(
        min_y,
        min(camera_y, max_y)
    )


    # =====================================================
    # CAMERA -> SCREEN
    # =====================================================

    target_x = (
        (camera_x - min_x)
        / (max_x - min_x)
        * screen_width
    )

    target_y = (
        (camera_y - min_y)
        / (max_y - min_y)
        * screen_height
    )


    # =====================================================
    # SMOOTHING
    # =====================================================

    smooth_x = (
        smooth_x
        + (target_x - smooth_x)
        * SMOOTHING
    )

    smooth_y = (
        smooth_y
        + (target_y - smooth_y)
        * SMOOTHING
    )


    pyautogui.moveTo(
        int(smooth_x),
        int(smooth_y),
        duration=0
    )


# =========================================================
# DISCRETE ACTIONS
# =========================================================

def execute_discrete_action(gesture):

    if gesture == "CLICK":

        pyautogui.click()

        print("LEFT CLICK")


    elif gesture == "NEXT":

        pyautogui.press("right")

        print("NEXT SLIDE")


    elif gesture == "PREVIOUS":

        pyautogui.press("left")

        print("PREVIOUS SLIDE")


    elif gesture == "PLAY_PAUSE":

        media_play_pause()


# =========================================================
# MAIN
# =========================================================

def main():

    global last_discrete_gesture


    cap = cv2.VideoCapture(
        CAMERA_INDEX
    )


    if not cap.isOpened():

        print(
            "ERROR: Could not open camera."
        )

        return


    with mp_hands.Hands(

        static_image_mode=False,

        max_num_hands=1,

        min_detection_confidence=0.65,

        min_tracking_confidence=0.65

    ) as hands:


        print("")
        print("==============================")
        print(" Gesture Computer Controller")
        print("==============================")
        print("")
        print("Index Finger = Move Mouse")
        print("Pinch        = Left Click")
        print("Thumb Up     = Next Slide")
        print("Thumb Down   = Previous Slide")
        print("OK Sign      = Play/Pause")
        print("")
        print("Q = Quit")
        print("")


        while True:


            ok, frame = cap.read()

            if not ok:
                break


            # Mirror camera
            frame = cv2.flip(
                frame,
                1
            )


            frame_height, frame_width, _ = (
                frame.shape
            )


            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )


            results = hands.process(rgb)


            gesture = "NONE"


            # =================================================
            # HAND FOUND
            # =================================================

            if results.multi_hand_landmarks:


                hand_landmarks = (
                    results.multi_hand_landmarks[0]
                )


                gesture = detect_gesture(
                    hand_landmarks
                )


                # =============================================
                # CONTINUOUS MOUSE
                # =============================================

                if gesture == "MOUSE":

                    move_mouse(
                        hand_landmarks,
                        frame_width,
                        frame_height
                    )

                    # Mouse movement allows future actions
                    last_discrete_gesture = "NONE"


                # =============================================
                # DISCRETE ACTIONS
                # =============================================

                elif gesture in [

                    "CLICK",
                    "NEXT",
                    "PREVIOUS",
                    "PLAY_PAUSE"

                ]:

                    # Only execute once when gesture appears
                    if (
                        gesture
                        != last_discrete_gesture
                    ):

                        execute_discrete_action(
                            gesture
                        )

                        last_discrete_gesture = (
                            gesture
                        )


                # =============================================
                # NOTHING
                # =============================================

                else:

                    last_discrete_gesture = "NONE"


                # =============================================
                # DRAW HAND
                # =============================================

                mp_draw.draw_landmarks(

                    frame,

                    hand_landmarks,

                    mp_hands.HAND_CONNECTIONS

                )


            else:

                last_discrete_gesture = "NONE"


            # =================================================
            # ACTIVE MOUSE AREA
            # =================================================

            cv2.rectangle(

                frame,

                (
                    FRAME_MARGIN,
                    FRAME_MARGIN
                ),

                (
                    frame_width
                    - FRAME_MARGIN,

                    frame_height
                    - FRAME_MARGIN
                ),

                (255, 255, 255),

                1

            )


            # =================================================
            # UI
            # =================================================

            cv2.rectangle(

                frame,

                (10, 10),

                (620, 135),

                (0, 0, 0),

                -1

            )


            cv2.putText(

                frame,

                f"Gesture: {gesture}",

                (20, 42),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.75,

                (0, 255, 0),

                2

            )


            cv2.putText(

                frame,

                "Index: Mouse | Pinch: Click",

                (20, 70),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                1

            )


            cv2.putText(

                frame,

                "Thumb Up: Next | Thumb Down: Previous",

                (20, 95),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                1

            )


            cv2.putText(

                frame,

                "OK Sign: Global Play/Pause",

                (20, 120),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                1

            )


            cv2.imshow(

                "Gesture Computer Controller",

                frame

            )


            # Quit
            if (
                cv2.waitKey(1) & 0xFF
                == ord("q")
            ):
                break


    cap.release()

    cv2.destroyAllWindows()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()