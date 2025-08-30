
# import cv2
# import numpy as np
# from keras.models import load_model
# import time
# from collections import deque, Counter
# import threading

# class EmotionDetector(threading.Thread):
#     def __init__(self, model_path="emotion_model.h5", confidence_threshold=0.5, cooldown_ms=2000):
#         super().__init__()
#         self.model = load_model(model_path, compile=False)
#         self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
#         self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
#         self.cap = cv2.VideoCapture(0)

#         self.confidence_threshold = confidence_threshold
#         self.cooldown_ms = cooldown_ms
#         self.rolling_window = deque(maxlen=15)

#         self.last_emotion = "loading..."
#         self.last_switch_time = int(time.time() * 1000)
#         self.latest_emotion = "loading..."

#         self.running = True
#         self.lock = threading.Lock()

#     def map_emotion(self, emotion):
#         if emotion in ['Happy', 'Neutral']:
#             return "calm"
#         elif emotion == 'Angry':
#             return "angry"
#         elif emotion == 'Sad':
#             return "sad"
#         else:
#             return "stressed"

#     def run(self):
#         while self.running:
#             ret, frame = self.cap.read()
#             if not ret:
#                 continue

#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

#             for (x, y, w, h) in faces:
#                 roi_gray = gray[y:y + h, x:x + w]
#                 try:
#                     face = cv2.resize(roi_gray, (64, 64))
#                     face = face.astype("float32") / 255.0
#                     face = np.expand_dims(face, axis=0)
#                     face = np.expand_dims(face, axis=-1)

#                     preds = self.model.predict(face, verbose=0)[0]
#                     confidence = np.max(preds)
#                     raw_emotion = self.emotion_labels[np.argmax(preds)]

#                     if confidence >= self.confidence_threshold:
#                         mapped = self.map_emotion(raw_emotion)
#                         self.rolling_window.append(mapped)

#                     if len(self.rolling_window) == self.rolling_window.maxlen:
#                         most_common = Counter(self.rolling_window).most_common(1)[0][0]
#                         now = int(time.time() * 1000)

#                         if most_common != self.last_emotion and (now - self.last_switch_time) > self.cooldown_ms:
#                             with self.lock:
#                                 self.last_emotion = most_common
#                                 self.latest_emotion = most_common
#                             self.last_switch_time = now

#                 except Exception as e:
#                     continue

#             time.sleep(0.05)  # slight delay to ease CPU

#     def get_emotion(self):
#         with self.lock:
#             return self.latest_emotion

#     def stop(self):
#         self.running = False
#         self.cap.release()

# == ver2==
# === emotion_detector_module.py ===

# import cv2
# import numpy as np
# from keras.models import load_model
# from PyQt6.QtCore import QThread, pyqtSignal
# from collections import deque, Counter
# import time

# class EmotionDetector(QThread):
#     frame_ready = pyqtSignal(np.ndarray)
#     emotion_ready = pyqtSignal(str)

#     def __init__(self, model_path="emotion_model.h5", confidence_threshold=0., cooldown_ms=2000):
#         super().__init__()
#         self.model = load_model(model_path, compile=False)
#         self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
#         self.cap = cv2.VideoCapture(0)

#         self.confidence_threshold = confidence_threshold
#         self.cooldown_ms = cooldown_ms
#         self.recent_emotions = deque(maxlen=15)

#         self.last_emotion = "loading..."
#         self.last_switch_time = int(time.time() * 1000)
#         self.latest_emotion = "loading..."

#         self.running = True

#     def run(self):
#         while self.running:
#             ret, frame = self.cap.read()
#             if not ret:
#                 continue

#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

#             dominant_emotion = None
#             for (x, y, w, h) in faces:
#                 roi_gray = gray[y:y + h, x:x + w]
#                 try:
#                     face = cv2.resize(roi_gray, (64, 64))
#                     face = face.astype("float32") / 255.0
#                     face = np.expand_dims(face, axis=0)
#                     face = np.expand_dims(face, axis=-1)

#                     preds = self.model.predict(face, verbose=0)[0]
#                     confidence = np.max(preds)
#                     raw_emotion = self.decode_emotion(preds)

#                     if confidence >= self.confidence_threshold:
#                         mapped = self.map_emotion(raw_emotion)
#                         self.recent_emotions.append(mapped)

#                     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#                     cv2.putText(frame, raw_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
#                     break

#                 except Exception as e:
#                     continue

#             if len(self.recent_emotions) > 0:
#                 most_common = Counter(self.recent_emotions).most_common(1)[0][0]
#                 self.latest_emotion = most_common  # Always update
#                 self.emotion_ready.emit(self.latest_emotion)

#             self.frame_ready.emit(frame)
#             time.sleep(0.05)

#     def decode_emotion(self, preds):
#         emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
#         return emotions[np.argmax(preds)]

#     def map_emotion(self, emotion):
#         if emotion in ['Happy', 'Neutral']:
#             return "calm"
#         elif emotion == 'Angry':
#             return "angry"
#         elif emotion == 'Sad':
#             return "sad"
#         else:
#             return "stressed"

#     def stop(self):
#         self.running = False
#         self.quit()
#         self.wait()
#         self.cap.release()

# # == ver3==
# # === emotion_detector_module.py (enhanced filtering version) ===
# import cv2
# import numpy as np
# from keras.models import load_model
# from PyQt6.QtCore import QThread, pyqtSignal
# from collections import deque, Counter
# import time

# class EmotionDetector(QThread):
#     frame_ready = pyqtSignal(np.ndarray)
#     emotion_ready = pyqtSignal(str)

#     def __init__(self, model_path="emotion_model.h5", confidence_threshold=0.5, cooldown_ms=1000):
#         super().__init__()
#         self.model = load_model(model_path, compile=False)
#         self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
#         self.cap = cv2.VideoCapture(0)

#         self.confidence_threshold = confidence_threshold
#         self.cooldown_ms = cooldown_ms
#         self.recent_emotions = deque(maxlen=10)

#         self.last_emotion = "loading..."
#         self.latest_emotion = "loading..."
#         self.last_switch_time = int(time.time() * 1000)
#         self.last_eval_time = time.time()
#         self.last_face_detected_time = time.time()

#         self.running = True

#     def run(self):
#         while self.running:
#             ret, frame = self.cap.read()
#             if not ret:
#                 continue

#             frame = cv2.flip(frame, 1)
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

#             detected = False
#             for (x, y, w, h) in faces:
#                 detected = True
#                 self.last_face_detected_time = time.time()

#                 try:
#                     face = cv2.resize(gray[y:y + h, x:x + w], (64, 64)).astype("float32") / 255.0
#                     face = np.expand_dims(face, axis=(0, -1))

#                     preds = self.model.predict(face, verbose=0)[0]
#                     confidence = np.max(preds)
#                     margin = confidence - sorted(preds, reverse=True)[1]
#                     raw_emotion = self.decode_emotion(preds)

#                     if confidence >= self.confidence_threshold and margin > 0.2:
#                         mapped = self.map_emotion(raw_emotion)
#                         self.recent_emotions.append(mapped)

#                     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
#                     cv2.putText(frame, raw_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                                 0.9, (0, 255, 0), 2)
#                     break
#                 except:
#                     continue

#             current_time = time.time()

#             # Emotion update every 1.5s
#             if current_time - self.last_eval_time >= 1.5:
#                 if len(self.recent_emotions) >= 3:
#                     top_emotion = Counter(self.recent_emotions).most_common(1)[0][0]
#                     now_ms = int(current_time * 1000)
#                     if top_emotion != self.last_emotion and (now_ms - self.last_switch_time) > self.cooldown_ms:
#                         self.latest_emotion = top_emotion
#                         self.last_emotion = top_emotion
#                         self.last_switch_time = now_ms
#                         self.emotion_ready.emit(top_emotion)
#                     else:
#                         self.emotion_ready.emit(top_emotion)
#                 self.recent_emotions.clear()
#                 self.last_eval_time = current_time

#             # No face fallback
#             if time.time() - self.last_face_detected_time > 2.5:
#                 if self.latest_emotion != "Face Not Detected":
#                     self.latest_emotion = "Face Not Detected"
#                     self.emotion_ready.emit("Face Not Detected")

#             self.frame_ready.emit(frame)
#             time.sleep(0.05)

#     def decode_emotion(self, preds):
#         emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
#         return emotions[np.argmax(preds)]

#     def map_emotion(self, emotion):
#         if emotion in ['Happy', 'Neutral']:
#             return "calm"
#         elif emotion == 'Angry':
#             return "angry"
#         elif emotion == 'Sad':
#             return "sad"
#         else:
#             return "stressed"

#     def stop(self):
#         self.running = False
#         self.quit()
#         self.wait()
#         self.cap.release()

# # == ver3==
import cv2
import numpy as np
from keras.models import load_model
from PyQt6.QtCore import QThread, pyqtSignal
from collections import deque, Counter
import time

class EmotionDetector(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    emotion_ready = pyqtSignal(str)

    def __init__(self, model_path="emotion_model.h5", confidence_threshold=0.4, cooldown_ms=500):
        super().__init__()
        self.model = load_model(model_path, compile=False)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.cap = cv2.VideoCapture(0)

        self.confidence_threshold = confidence_threshold
        self.cooldown_ms = cooldown_ms
        self.recent_emotions = deque(maxlen=7)  # Smaller window for faster change

        self.last_emotion = "loading..."
        self.latest_emotion = "loading..."
        self.last_switch_time = int(time.time() * 1000)
        self.last_eval_time = time.time()
        self.last_face_detected_time = time.time()

        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            detected = False
            for (x, y, w, h) in faces:
                detected = True
                self.last_face_detected_time = time.time()

                try:
                    roi = gray[y:y + h, x:x + w]
                    face = cv2.resize(roi, (64, 64)).astype("float32") / 255.0
                    face = np.expand_dims(face, axis=(0, -1))

                    preds = self.model.predict(face, verbose=0)[0]
                    confidence = np.max(preds)
                    second_best = sorted(preds, reverse=True)[1]
                    margin = confidence - second_best
                    raw_emotion = self.decode_emotion(preds)

                    if confidence >= self.confidence_threshold and margin > 0.15:
                        mapped = self.map_emotion(raw_emotion)
                        self.recent_emotions.append(mapped)

                    # Green bounding box + label
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, raw_emotion, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    break
                except:
                    continue

            # Evaluate emotion more frequently
            current_time = time.time()
            if current_time - self.last_eval_time >= 1.0:
                if self.recent_emotions:
                    top_emotion = Counter(self.recent_emotions).most_common(1)[0][0]
                    now_ms = int(current_time * 1000)
                    if (top_emotion != self.last_emotion and 
                        (now_ms - self.last_switch_time) > self.cooldown_ms):
                        self.latest_emotion = top_emotion
                        self.last_emotion = top_emotion
                        self.last_switch_time = now_ms
                        self.emotion_ready.emit(top_emotion)
                    else:
                        self.emotion_ready.emit(top_emotion)

                self.recent_emotions.clear()
                self.last_eval_time = current_time

            # Face not detected recently
            if time.time() - self.last_face_detected_time > 1.5:
                if self.latest_emotion != "Face Not Detected":
                    self.latest_emotion = "Face Not Detected"
                    self.emotion_ready.emit("Face Not Detected")

            self.frame_ready.emit(frame)
            time.sleep(0.05)

    def decode_emotion(self, preds):
        emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        return emotions[np.argmax(preds)]

    def map_emotion(self, emotion):
        if emotion in 'Neutral':
            return "calm"
        elif emotion == 'Happy':
            return "happy"
        elif emotion == 'Angry':
            return "angry"
        elif emotion == 'Sad':
            return "sad"
        elif emotion in ['Fear', 'Disgust', 'Surprise']:
            return "stressed"
        else:
            return "stressed"  # fallback if unexpected


    def stop(self):
        self.running = False
        self.quit()
        self.wait()
        self.cap.release()
