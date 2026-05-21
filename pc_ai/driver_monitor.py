import cv2, time, math
import mediapipe as mp
import paho.mqtt.client as mqtt

# ===== إعدادات MQTT =====
broker = "192.168.0.160"
port = 1883
topic_status = "car/driver/status"
topic_notification = "car/notification"
topic_motor = "lab6/motor"

client = mqtt.Client()
client.connect(broker, port, 60)

# ===== Mediapipe =====
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
mp_draw = mp.solutions.drawing_utils

# ===== إعدادات التتبع =====
EAR_THRESHOLD = 0.25
EAR_CONSEC_FRAMES = 15
COUNTER = 0
driver_sleeping = False
last_notification_time = 0
notification_interval = 5
response_timeout = 10
sleep_start_time = None

# ===== إضافة تأكيد زمني قبل الإرسال =====
SLEEP_CONFIRM_SECONDS = 3.0  # <-- تأكيد 3 ثواني قبل إرسال إشعار النعاس
potential_sleep_start = None  # وقت بداية الملاحظة كـ "محتمل نائم"

# دالة EAR
def euclidean_distance(p1, p2):
    return math.dist(p1, p2)

def eye_aspect_ratio(landmarks, eye_indices, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_indices]
    A = euclidean_distance(pts[1], pts[5])
    B = euclidean_distance(pts[2], pts[4])
    C = euclidean_distance(pts[0], pts[3])
    return (A + B) / (2.0 * C)

# فهرس نقاط العينين في Mediapipe
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

cap = cv2.VideoCapture(0)
print("Driver monitoring with Mediapipe...")

while True:
    ret, frame = cap.read()
    if not ret: break
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    current_time = time.time()
    ear = 0.0
    eyes_detected = False

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # EAR للعينين
            ear_left = eye_aspect_ratio(face_landmarks.landmark, LEFT_EYE, w, h)
            ear_right = eye_aspect_ratio(face_landmarks.landmark, RIGHT_EYE, w, h)
            ear = (ear_left + ear_right) / 2.0
            eyes_detected = True

            if ear < EAR_THRESHOLD:
                COUNTER += 1
            else:
                COUNTER = max(0, COUNTER - 2)

            # رسم العينين (اختياري)
            mp_draw.draw_landmarks(frame, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)

    # تحديد حالة السائق مع تأكيد 3 ثواني قبل إرسال إشعار النعاس
    if COUNTER >= EAR_CONSEC_FRAMES:
        # نلاحظ نعاساً "محتمل" — ابدأ المُؤقت إن لم يبدأ
        if not driver_sleeping:
            if potential_sleep_start is None:
                potential_sleep_start = current_time
            else:
                # إذا استمر الوضع "محتمل النعاس" لمدة SLEEP_CONFIRM_SECONDS، اعتبره نائماً فعلاً
                if (current_time - potential_sleep_start) >= SLEEP_CONFIRM_SECONDS:
                    driver_sleeping = True
                    sleep_start_time = current_time
                    client.publish(topic_status, "sleeping")
                    client.publish(topic_notification, "press_switch")
                    last_notification_time = current_time
                    print("Driver is sleeping! (confirmed after 3s)")
        # لو driver_sleeping بالفعل لا نحتاج لفعل شيء إضافي هنا
    else:
        # العينين مفتوحتين أو لا نعاس => إعادة تهيئة مؤقت التأكيد
        potential_sleep_start = None
        if driver_sleeping:
            driver_sleeping = False
            sleep_start_time = None
            client.publish(topic_status, "awake")
            print("Driver is awake!")

    # إذا كان نائم (مؤكد) فالتعامل مع التذكيرات و timeout كما كان
    if driver_sleeping and sleep_start_time:
        elapsed_time = current_time - sleep_start_time
        if current_time - last_notification_time > notification_interval:
            client.publish(topic_notification, "press_switch")
            last_notification_time = current_time
            print("Reminder sent.")
        if elapsed_time > response_timeout:
            client.publish(topic_motor, "OFF")
            print("Timeout! Motor OFF")
            driver_sleeping = False
            sleep_start_time = None

    # عرض
    cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
    cv2.putText(frame, "Status: " + ("Sleeping" if driver_sleeping else "Awake"),
                (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255) if driver_sleeping else (0,255,0), 2)
    cv2.imshow("Driver Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()