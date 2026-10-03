import cv2
import mediapipe as mp
import pyautogui
import time

# ---------------- SETTINGS ----------------
CAMERA_INDEX = 0
COOLDOWN_SECONDS = 1.0

# Gesture:
# Index finger only  -> NEXT slide
# Index + middle     -> PREVIOUS slide
# Press Q in camera window to quit
# ------------------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

last_action_time = 0
last_gesture = "None"


def finger_states(hand_landmarks, handedness):
    """Return [thumb, index, middle, ring, pinky] as True/False."""
    lm = hand_landmarks.landmark

    # For index/middle/ring/pinky, fingertip above PIP joint = finger up.
    fingers = [
        lm[8].y < lm[6].y,    # index
        lm[12].y < lm[10].y,  # middle
        lm[16].y < lm[14].y,  # ring
        lm[20].y < lm[18].y,  # pinky
    ]

    # Thumb uses x direction and depends on detected hand.
    if handedness == "Right":
        thumb = lm[4].x < lm[3].x
    else:
        thumb = lm[4].x > lm[3].x

    return [thumb] + fingers


def detect_gesture(states):
    thumb, index, middle, ring, pinky = states

    # Ignore thumb in these two simple demo gestures.
    if index and not middle and not ring and not pinky:
        return "NEXT"

    if index and middle and not ring and not pinky:
        return "PREVIOUS"

    return "NONE"


def perform_action(gesture):
    global last_action_time

    now = time.time()
    if now - last_action_time < COOLDOWN_SECONDS:
        return

    if gesture == "NEXT":
        pyautogui.press("right")
        print("NEXT SLIDE")
        last_action_time = now

    elif gesture == "PREVIOUS":
        pyautogui.press("left")
        print("PREVIOUS SLIDE")
        last_action_time = now


def main():
    global last_gesture

    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        print("Try changing CAMERA_INDEX in main.py from 0 to 1.")
        return

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as hands:

        print("Gesture Slide Demo started.")
        print("Index finger only = NEXT")
        print("Index + middle = PREVIOUS")
        print("Press Q in the camera window to quit.")

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Mirror view so movement feels natural.
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            gesture = "NONE"

            if results.multi_hand_landmarks:
                for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    handedness = results.multi_handedness[i].classification[0].label
                    states = finger_states(hand_landmarks, handedness)
                    gesture = detect_gesture(states)

                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

                    cv2.putText(
                        frame,
                        f"Hand: {handedness}",
                        (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )

            perform_action(gesture)
            last_gesture = gesture

            cv2.rectangle(frame, (10, 10), (410, 115), (0, 0, 0), -1)
            cv2.putText(
                frame,
                f"Gesture: {gesture}",
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0) if gesture != "NONE" else (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "1 finger: NEXT | 2 fingers: PREVIOUS | Q: Quit",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 255, 255),
                1,
            )

            cv2.imshow("Gesture Slide Demo", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
