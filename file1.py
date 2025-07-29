import cv2
import mediapipe as mp
import serial
import time

# Setup serial with timeout
try:
    esp = serial.Serial('COM4', 115200, timeout=1)
    time.sleep(2)
except:
    print("Error: Could not connect to ESP32 on COM4.")
    exit()

# Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not access webcam.")
    exit()

last_sign = ""

def fingers_up(lm):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = []
    fingers.append(1 if lm.landmark[4].x < lm.landmark[3].x else 0)
    for i in range(1, 5):
        fingers.append(1 if lm.landmark[tip_ids[i]].y < lm.landmark[tip_ids[i]-2].y else 0)
    return fingers

def detect_sign(f):
    signs = {
        (1,1,1,1,1): "HELLO",
        (0,0,0,0,0): "I WANT FOOD",
        (0,1,0,0,0): "I WANT WATER",
        (0,1,1,0,0): "I WANT TO USE BATHROOM",
        (1,0,0,0,1): "MOVE FORWARD",
        (1,1,0,0,0): "TURN LEFT",
        (0,0,1,1,1): "TURN RIGHT",
        (0,1,1,1,1): "MOVE BACKWARD",
        (1,1,1,0,0): "I FEEL DIZZY",
        (1,0,1,0,1): "I NEED MEDICINE",
        (0,1,0,1,0): "HELP ME",
        (1,1,1,1,0): "I AM TIRED",
        (0,0,1,0,0): "I AM COLD",
        (1,0,0,1,1): "I AM IN PAIN",
        (1,1,0,1,0): "LET’S GO OUTSIDE"
    }
    return signs.get(tuple(f), None)

while True:
    success, img = cap.read()
    if not success:
        print("Frame not captured.")
        continue

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for lm in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, lm, mp_hands.HAND_CONNECTIONS)
            try:
                fingers = fingers_up(lm)
                sign = detect_sign(fingers)
                if sign and sign != last_sign:
                    print("Detected:", sign)
                    esp.write((sign + '\n').encode())
                    last_sign = sign
                if sign:
                    cv2.putText(img, f"Sign: {sign}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            except Exception as e:
                print("Detection error:", e)

    cv2.imshow("Smart Wheelchair Sign Detection", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

esp.close()
cap.release()
cv2.destroyAllWindows()
