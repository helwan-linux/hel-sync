import os, subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QListWidget, QHBoxLayout, QTextEdit, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPixmap
import qrcode
from io import BytesIO
from hel_sync_core import network_server as server

class CommSignals(QObject):
    file_received = pyqtSignal(str)
    text_received = pyqtSignal(str)

class HelSyncGUI(QWidget):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.comm = CommSignals()
        self.init_ui()
        self.comm.file_received.connect(self.add_to_list)
        self.comm.text_received.connect(lambda t: self.clip_display.setPlainText(t))

    def init_ui(self):
        self.setWindowTitle("Hel-Sync Pro Control")
        self.setFixedSize(500, 750)
        self.setStyleSheet("background: #0c0c0c; color: #eee;")
        layout = QVBoxLayout()

        # 1. QR Code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.gen_qr()
        layout.addWidget(self.qr_label)

        # 2. إرسال ملفات من الكمبيوتر
        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("📁 Select & Send Files")
        self.send_btn.setStyleSheet("background: #a349a4; padding: 10px; font-weight: bold;")
        self.send_btn.clicked.connect(self.open_file_dialog)
        
        self.open_folder_btn = QPushButton("📂 Open Downloads")
        self.open_folder_btn.setStyleSheet("background: #333; padding: 10px;")
        self.open_folder_btn.clicked.connect(self.open_download_folder)
        
        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.open_folder_btn)
        layout.addLayout(btn_layout)

        # 3. قسم النصوص
        layout.addWidget(QLabel("📋 Clipboard Sync:"))
        self.clip_display = QTextEdit()
        self.clip_display.setMaximumHeight(80)
        self.clip_display.setStyleSheet("background: #161616; border: 1px solid #a349a4;")
        layout.addWidget(self.clip_display)
        
        clip_btns = QHBoxLayout()
        self.send_clip_btn = QPushButton("📤 Send Text to Mobile")
        self.send_clip_btn.clicked.connect(self.send_text_to_mobile)
        
        self.copy_clip_btn = QPushButton("✂️ Copy Received Text")
        self.copy_clip_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.clip_display.toPlainText()))
        
        clip_btns.addWidget(self.send_clip_btn)
        clip_btns.addWidget(self.copy_clip_btn)
        layout.addLayout(clip_btns)

        # 4. قائمة الملفات المستلمة
        layout.addWidget(QLabel("✅ Recently Received Files:"))
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("background: #1a1a1a; border-radius: 5px;")
        layout.addWidget(self.file_list)

        self.setLayout(layout)

    def gen_qr(self):
        qr = qrcode.make(self.url)
        buf = BytesIO(); qr.save(buf, "PNG")
        pix = QPixmap(); pix.loadFromData(buf.getvalue())
        self.qr_label.setPixmap(pix.scaled(200, 200))

    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files to Share")
        if paths:
            server.FILES_TO_SHARE.extend(paths)
            self.add_to_list(f"Shared {len(paths)} files to mobile")

    def open_download_folder(self):
        path = os.path.expanduser("~/Downloads/HelSync")
        # دعم فتح المجلد في آرتش (Linux) وويندوز
        if os.name == 'nt': os.startfile(path)
        else: subprocess.Popen(['xdg-open', path])

    def send_text_to_mobile(self):
        text = self.clip_display.toPlainText()
        if text:
            server.LATEST_CLIPBOARD = text
            self.add_to_list("Text sent to mobile")

    def add_to_list(self, text):
        self.file_list.insertItem(0, f"• {text}")

    def launch(self):
        self.show()