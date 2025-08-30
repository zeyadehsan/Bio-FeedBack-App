# === breathing_gui_ver7.py ===
import sys
import math
import cv2
import numpy as np

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMainWindow, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt6.QtGui import QScreen, QPainter, QPen, QColor, QPainterPath, QPalette, QFont, QImage, QPixmap
from PyQt6.QtCore import Qt, QRectF, QTimer, QPropertyAnimation

#The main engine of the Emotion detection
from emotion_detector_module import EmotionDetector

#The main engine of the respiration rate algorthim (fetching from the firebase)
from algorithm_RR import RRAdaptation

#for fitching the 6Paramters
from firebase_fetch import fetch_latest_hrv


#Helper Funtion no.1 (Making the screen centered)
def center_window(window):
    screen = window.screen() or QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    x = screen_geometry.center().x() - window.width() // 2
    y = screen_geometry.center().y() - window.height() // 2
    window.move(x, y)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sine_widget = SineWaveWidget()
        self.setCentralWidget(self.sine_widget)
        self.setWindowTitle("Breathing Visualizer")
        self.showFullScreen()

    def closeEvent(self, event):
        widget = self.centralWidget()
        if isinstance(widget, SineWaveWidget):
            widget.cleanup()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F:
            if self.isFullScreen():
                self.showNormal()
                center_window(self) #Centering the screen using HF(1)
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()

class CountdownScreen(QWidget):
    def __init__(self, on_done_callback):
        super().__init__()
        self.count = 3
        self.on_done_callback = on_done_callback
        self.setStyleSheet("background-color: #f5f5dc;")
        self.setMinimumSize(1000, 600)
        self.label = QLabel(f"{self.count}", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #333; font-weight: bold;")
        self.label.setFont(QFont("Arial", 96, QFont.Weight.Bold))
        self.opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.opacity_effect)
        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_countdown)
        self.timer.start(1000)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(800)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animate_countdown()

    def animate_countdown(self):
        if self.count > 0:
            self.label.setText(str(self.count))
            self.opacity_effect.setOpacity(0)
            self.animation.start()
            self.play_beep()
            self.count -= 1
        else:
            self.timer.stop()
            self.on_done_callback()
            self.close()

    def play_beep(self):
        try:
            if sys.platform == 'win32':
                import winsound
                winsound.Beep(1000, 200)
            else:
                import os
                os.system('printf "\a"')
        except:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        rounded_rect = QRectF(self.rect().adjusted(5, 5, -5, -5))
        path.addRoundedRect(rounded_rect, 30, 30)
        painter.fillPath(path, QColor(245, 245, 220))

class SineWaveWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1000, 600)
        self.phase = 0
        self.elapsed_time_ms = 0
        self.dot_x_ratio = 0.0

        self.rr_adapt = RRAdaptation(initial_rr=20)
        self.rr_startingPoint = RRAdaptation(initial_rr=20)
        self.rr_bpm = self.rr_adapt.current_rr
        self.breath_cycle_sec = 60 / self.rr_bpm
        self.breath_cycle_ms = self.breath_cycle_sec * 1000

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(33)

        self.phase_label = QLabel(self)
        self.phase_label.setText("Inhale")
        self.phase_label.setStyleSheet("font-size: 36px; font-weight: bold; color: green;")
        self.phase_label.setGeometry(20, 20, 200, 40)

        self.timer_label = QLabel(self)
        self.timer_label.setText("Time: 0s")
        self.timer_label.setStyleSheet("font-size: 22px; color: gray;")
        self.timer_label.setGeometry(20, 70, 200, 30)

        self.rr_label = QLabel(self)
        self.rr_label.setText(f"RR: {self.rr_bpm} bpm")
        self.rr_label.setStyleSheet("font-size: 22px; color: black;")
        self.rr_label.setGeometry(20, 150, 200, 30)

        # ==inializing the reset button attributes
        self.reset_button = QPushButton("Reset RR", self)
        self.reset_button.setGeometry(20, 190, 120, 40)
        self.reset_button.setStyleSheet(""
            "QPushButton {"
            "  font-size: 16px;"
            "  color: #2e2e2e;"
            "  background-color: #d8b65b;"
            "  border: none;"
            "  border-radius: 10px;"
            "  padding: 3px 4px;"
            "}"
            "QPushButton:hover {"
            "  background-color:  #c8a74f;"
            "}"
        )
        shadow_button = QGraphicsDropShadowEffect(self)
        shadow_button.setBlurRadius(20)
        shadow_button.setOffset(2, 2)
        shadow_button.setColor(QColor(0, 0, 0, 120))
        self.reset_button.setGraphicsEffect(shadow_button)
        self.reset_button.clicked.connect(self.reset_rr)
        
        # == breathing label ==
        self.breaths = 0
        self.breath_label = QLabel(self)
        self.breath_label.setText("Breaths: 0")
        self.breath_label.setStyleSheet("font-size: 20px; color: #d8b65b;")
        self.breath_label.setGeometry(20, 110, 200, 30)

        # == 6Paramters label ==
        start_y = 500  # move lower
        spacing = 35    # vertical spacing

        self.hfPower_label = QLabel("HF Power: 0", self)
        self.hfPower_label.setGeometry(20, start_y, 250, 25)

        self.lfPower_label = QLabel("LF Power: 0", self)
        self.lfPower_label.setGeometry(20, start_y + spacing, 250, 25)

        self.lfHfRatio_label = QLabel("LF/HF Ratio: 0", self)
        self.lfHfRatio_label.setGeometry(20, start_y + 2*spacing, 250, 25)

        self.pnn50_label = QLabel("pNN50: 0", self)
        self.pnn50_label.setGeometry(20, start_y + 3*spacing, 250, 25)

        self.rmssd_label = QLabel("RMSSD: 0", self)
        self.rmssd_label.setGeometry(20, start_y + 4*spacing, 250, 25)

        self.sdnn_label = QLabel("SDNN: 0", self)
        self.sdnn_label.setGeometry(20, start_y + 5*spacing, 250, 25)

        # Style (apply to all at once)
        for lbl in [self.hfPower_label, self.lfPower_label, self.lfHfRatio_label,
                    self.pnn50_label, self.rmssd_label, self.sdnn_label]:
            lbl.setStyleSheet("font-size: 18px; color: #0CB9C1;")

        # this for the updating
        self.hrv_timer = QTimer()
        #self.hrv_timer.timeout.connect(self.refresh_hrv_data)
        self.hrv_timer.start(5000)  # fetch every 5 seconds




        # == webcam label ==
        self.webcam_label = QLabel(self)
        self.webcam_label.setScaledContents(True)
        self.webcam_label.setStyleSheet("QLabel { border: 5px solid #4A6E78; border-radius: 10px; background-color: white; }")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(4, 4)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.webcam_label.setGraphicsEffect(shadow)

        self.webcam_opacity = QGraphicsOpacityEffect()
        self.webcam_label.setGraphicsEffect(self.webcam_opacity)
        self.webcam_opacity.setOpacity(0.0)
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.fade_in_webcam)
        self.fade_timer.start(50)
        self.opacity_value = 0.0

        # == inializing the emotion module
        self.emotion_detector = EmotionDetector()
        self.emotion_detector.frame_ready.connect(self.display_emotion_frame)
        self.emotion_detector.emotion_ready.connect(self.display_emotion_text)
        self.emotion_detector.start()

        self.emotion_line_label = QLabel(self)
        self.emotion_line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emotion_line_label.setStyleSheet("font-size: 18px; color: gray;")

    # resting the RR using the button
    def reset_rr(self):
        self.rr_adapt.reset()
        self.rr_bpm = self.rr_adapt.current_rr
        self.breath_cycle_sec = 60 / self.rr_bpm
        self.breath_cycle_ms = self.breath_cycle_sec * 1000
        self.rr_label.setText(f"RR: {self.rr_bpm:.1f} bpm")

        # Animation effect for RR label
        self.rr_opacity_effect = QGraphicsOpacityEffect(self.rr_label)
        self.rr_label.setGraphicsEffect(self.rr_opacity_effect)
        self.rr_anim = QPropertyAnimation(self.rr_opacity_effect, b"opacity")
        self.rr_anim.setDuration(600)
        self.rr_anim.setStartValue(0.3)
        self.rr_anim.setEndValue(1.0)
        self.rr_anim.start()
        self.update_animation()

    # cleaning up the emotion detecor 
    def cleanup(self):
        self.emotion_detector.stop()
    
    # for the fadeing in of the web cam
    def fade_in_webcam(self):
        if self.opacity_value < 1.0:
            self.opacity_value += 0.05
            self.webcam_opacity.setOpacity(self.opacity_value)
        else:
            self.fade_timer.stop()

    def display_emotion_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.webcam_label.setPixmap(QPixmap.fromImage(img))

    def display_emotion_text(self, emotion):
        self.emotion_detector.current_emotion = emotion
        color_map = {
            "calm": "#4CAF50",
            "happy": "#FFD700",
            "angry": "#E53935",
            "stressed": "#FF8C00",
            "default": "#999999",
            "Face Not Detected": "#999999"
        }
        color = color_map.get(emotion, color_map["default"])
        if emotion == "Face Not Detected":
            self.emotion_line_label.setText("<span style='color:#999999; font-size:18px;'>Face Not Detected</span>")
        else:
            self.update_emotion_line_display(emotion)
    # an updater function for the 6Parameters:
    def update_hrv_labels(self, hrv_data):
        self.hfPower_label.setText(f"HF Power: {hrv_data['hfPower']}")
        self.lfPower_label.setText(f"LF Power: {hrv_data['lfPower']}")
        self.lfHfRatio_label.setText(f"LF/HF Ratio: {hrv_data['lfHfRatio']}")
        self.pnn50_label.setText(f"pNN50: {hrv_data['pnn50']}")
        self.rmssd_label.setText(f"RMSSD: {hrv_data['rmssd']}")
        self.sdnn_label.setText(f"SDNN: {hrv_data['sdnn']}")

    # to diplay emotions in calm | angry | happy | stressed format
    def update_emotion_line_display(self, current_emotion):
        emotions = ["calm", "happy", "angry", "stressed"]
        color_map = {
            "calm": "#4CAF50",
            "happy": "#FFD700",
            "angry": "#E53935",
            "stressed": "#FF8C00"
        }
        dull_color = "#BBBBBB"
        html_parts = []
        for emo in emotions:
            color = color_map.get(emo, dull_color) if emo == current_emotion else dull_color
            html_parts.append(f'<span style="color:{color}; font-weight:bold; font-size:18px;">{emo.capitalize()}</span>')
        combined_html = ' &nbsp;|&nbsp; '.join(html_parts)
        self.emotion_line_label.setText(combined_html)
    
    #The refresher function
    # def refresh_hrv_data(self):
    #     try:
    #         hrv_data = fetch_latest_hrv()
    #         if hrv_data:
    #             self.update_hrv_labels(hrv_data)
    #     except Exception as e:
    #         print(f"Error fetching HRV: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        margin = 10
        cam_width, cam_height = (320, 240) if self.window().isFullScreen() else (200, 150)
        cam_x = self.width() - cam_width - margin
        cam_y = margin
        self.webcam_label.setGeometry(cam_x, cam_y, cam_width, cam_height)
        self.emotion_line_label.setGeometry(cam_x, cam_y + cam_height + 5, cam_width, 30)
        font_size = max(12, self.width() // 60)
        self.emotion_line_label.setStyleSheet(f"font-size: {font_size}px; color: gray;")

    def update_animation(self):
        self.elapsed_time_ms += self.timer.interval()
        seconds = self.elapsed_time_ms // 1000
        self.timer_label.setText(f"Time: {seconds}s")
        delta = self.timer.interval() / self.breath_cycle_ms
        self.dot_x_ratio += delta
        if self.dot_x_ratio >= 1.0:
            self.dot_x_ratio = 0.0
            self.breaths += 1
            self.breath_label.setText(f"Breaths: {self.breaths}")

            emotion = getattr(self.emotion_detector, 'current_emotion', None)
            new_rr = self.rr_adapt.update(emotion)
            self.rr_bpm = new_rr
            self.breath_cycle_sec = 60 / self.rr_bpm
            self.breath_cycle_ms = self.breath_cycle_sec * 1000
            self.rr_label.setText(f"RR: {self.rr_bpm:.1f} bpm")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rounded_rect = self.rect().adjusted(5, 5, -5, -5)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rounded_rect), 15, 15)
        painter.fillPath(path, QColor(245, 245, 220))
        width = self.width()
        height = self.height()
        baseline_y = height // 2
        amplitude = height // 3
        pen_axis = QPen(QColor(200, 200, 200))
        pen_axis.setWidth(2)
        painter.setPen(pen_axis)
        painter.drawLine(0, baseline_y, width, baseline_y)
        pen_wave = QPen(QColor(0, 128, 128))
        pen_wave.setWidth(3)
        painter.setPen(pen_wave)
        prev_x = 0
        prev_y = baseline_y - math.sin(0) * amplitude
        for x in range(1, width):
            angle = (x / width) * 2 * math.pi
            y = baseline_y - math.sin(angle) * amplitude
            painter.drawLine(prev_x, int(prev_y), x, int(y))
            prev_x = x
            prev_y = y
        moving_x = self.dot_x_ratio * width
        angle = self.dot_x_ratio * 2 * math.pi
        moving_y = baseline_y - math.sin(angle) * amplitude
        if math.sin(angle) >= 0:
            self.phase_label.setText("Inhale")
            self.phase_label.setStyleSheet("font-size: 36px; font-weight: bold; color: green;")
            painter.setBrush(QColor(0, 200, 0))
        else:
            self.phase_label.setText("Exhale")
            self.phase_label.setStyleSheet("font-size: 36px; font-weight: bold; color: darkred;")
            painter.setBrush(QColor(200, 0, 0))
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(int(moving_x) - 6, int(moving_y) - 6, 12, 12)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    def start_main_window():
        global main_window
        main_window = MainWindow()
        center_window(main_window)
        main_window.show()
    countdown = CountdownScreen(on_done_callback=start_main_window)
    center_window(countdown)
    countdown.show()
    sys.exit(app.exec())
