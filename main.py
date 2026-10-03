import cv2
import mediapipe as mp
import pyautogui
import ctypes
import time


# =========================
# SETTINGS
# =========================

CAMERA_INDEX = 0

# Prevent repeated slide changes
SLIDE_COOLDOWN = 1.0

# Windows Media Play/Pause virtual key
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


# =========================
# MEDIAPIPE
# =========================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


last_slide_action = 0

# Used so one fist = one Play/Pause command
previous_fist = False


# =========================
# GLOBAL MEDIA PLAY / PAUSE
# =========================

def media_play_pause():
    """
    Sends the Windows global MEDIA_PLAY_PAUSE key.

    Works with applications such as:
    Spotify
    YouTube
    VLC
    Media Player
    Browser audio/video

    even when they are in the background.
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

    print("MEDIA PLAY / PAUSE")


# =========================
# FINGER DETECTION
# =========================

def finger_states(hand_landmarks, handedness):

    lm = hand_landmarks.landmark

    # Main fingers
    index = lm[8].y < lm[6].y
    middle = lm[12].y < lm[10].y
    ring = lm[16].y < lm[14].y
    pinky = lm[20].y < lm[18].y

    # Thumb
    if handedness == "Right":
        thumb = lm[4].x < lm[3].x
    else:
        thumb = lm[4].x > lm[3].x

    return [
        thumb,
        index,
        middle,
        ring,
        pinky
    ]


# =========================
# GESTURE DETECTION
# =========================

def detect_gesture(states):

    thumb, index, middle, ring, pinky = states

    # -------------------------
    # ONE FINGER
    # -------------------------
    # Index finger only
    if (
        index
        and not middle
        and not ring
        and not pinky
    ):
        return "NEXT"


    # -------------------------
    # TWO FINGERS
    # -------------------------
    # Index + middle
    if (
        index
        and middle
        and not ring
        and not pinky
    ):
        return "PREVIOUS"


    # -------------------------
    # FIST
    # -------------------------
    # All 5 fingers closed
    if not any(states):
        return "FIST"


    return "NONE"


# =========================
# SLIDE CONTROL
# =========================

def slide_action(action):

    global last_slide_action

    now = time.time()

    if now - last_slide_action < SLIDE_COOLDOWN:
        return False


    if action == "NEXT":

        pyautogui.press("right")

        print("NEXT SLIDE")

        last_slide_action = now

        return True


    elif action == "PREVIOUS":

        pyautogui.press("left")

        print("PREVIOUS SLIDE")

        last_slide_action = now

        return True


    return False


# =========================
# MAIN
# =========================

def main():

    global previous_fist


    cap = cv2.VideoCapture(CAMERA_INDEX)


    if not cap.isOpened():

        print("ERROR: Could not open webcam.")

        print(
            "Try changing CAMERA_INDEX "
            "from 0 to 1."
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
        print(" Gesture Controller Started")
        print("==============================")
        print("")
        print("1 finger = NEXT")
        print("2 fingers = PREVIOUS")
        print("Fist      = MEDIA PLAY/PAUSE")
        print("")
        print("Q = Quit")
        print("")


        while True:


            ok, frame = cap.read()


            if not ok:
                break


            # Mirror image
            frame = cv2.flip(frame, 1)


            # OpenCV BGR -> RGB
            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )


            results = hands.process(rgb)


            gesture = "NONE"


            # =========================
            # HAND FOUND
            # =========================

            if results.multi_hand_landmarks:


                hand_landmarks = (
                    results.multi_hand_landmarks[0]
                )


                handedness = (

                    results
                    .multi_handedness[0]
                    .classification[0]
                    .label

                )


                states = finger_states(
                    hand_landmarks,
                    handedness
                )


                gesture = detect_gesture(states)


                # =========================
                # NEXT
                # =========================

                if gesture == "NEXT":

                    slide_action("NEXT")


                # =========================
                # PREVIOUS
                # =========================

                elif gesture == "PREVIOUS":

                    slide_action("PREVIOUS")


                # =========================
                # GLOBAL MEDIA
                # =========================

                elif gesture == "FIST":

                    # Trigger only once when
                    # fist is first detected

                    if not previous_fist:

                        media_play_pause()


                    previous_fist = True


                # Hand isn't fist anymore
                if gesture != "FIST":

                    previous_fist = False


                # =========================
                # DRAW HAND
                # =========================

                mp_draw.draw_landmarks(

                    frame,

                    hand_landmarks,

                    mp_hands.HAND_CONNECTIONS

                )


            else:

                previous_fist = False


            # =========================
            # DISPLAY UI
            # =========================

            cv2.rectangle(

                frame,

                (10, 10),

                (520, 120),

                (0, 0, 0),

                -1

            )


            cv2.putText(

                frame,

                f"Gesture: {gesture}",

                (20, 45),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 255, 0),

                2

            )


            cv2.putText(

                frame,

                "1 Finger: NEXT | 2 Fingers: PREVIOUS",

                (20, 75),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                1

            )


            cv2.putText(

                frame,

                "Fist: Global Media Play/Pause | Q: Quit",

                (20, 100),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (255, 255, 255),

                1

            )


            cv2.imshow(

                "Gesture Controller",

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


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()