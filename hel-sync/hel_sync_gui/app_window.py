import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, 
                             QProgressBar, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon, QPixmap
import qrcode
from io import BytesIO

class CommSignals(QObject):
    """إشارات الربط بين السيرفر والواجهة"""
    file_received = pyqtSignal(str) # تستقبل اسم الملف
    text_received = pyqtSignal(str)

class HelSyncGUI(QWidget):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.comm = CommSignals()
        self.total_files = 0
        self.init_ui()
        
        # ربط الإشارات بالدوال
        self.comm.file_received.connect(self.update_file_list)
        self.comm.text_received.connect(self.show_new_text)

    def init_ui(self):
        self.setWindowTitle("Hel-Sync Pro - Arch Linux")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #0c0c0c; color: white;")

        layout = QVBoxLayout()

        # 1. قسم الـ QR Code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.generate_qr()
        layout.addWidget(self.qr_label)

        # 2. معلومات الاتصال
        info_label = QLabel("Scan to Sync (Mobile + PC)")
        info_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #a349a4;")
        layout.addWidget(info_label)

        # 3. عداد البيانات (Stats Frame)
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #161616; border-radius: 10px; border: 1px solid #333;")
        stats_layout = QHBoxLayout(stats_frame)
        
        self.file_count_label = QLabel("Files: 0")
        self.file_count_label.setFont(QFont("Consolas", 11))
        
        status_dot = QLabel("● Online")
        status_dot.setStyleSheet("color: #28a745; border: none;")
        
        stats_layout.addWidget(self.file_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(status_dot)
        layout.addWidget(stats_frame)

        # 4. قائمة الملفات المستلمة
        layout.addWidget(QLabel("Recently Received Files:"))
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #222;
            }
        """)
        layout.addWidget(self.file_list)

        # 5. آخر نص مستلم
        layout.addWidget(QLabel("Last Clipboard Sync:"))
        self.clip_label = QLabel("Waiting for text...")
        self.clip_label.setWordWrap(True)
        self.clip_label.setStyleSheet("background: #000; padding: 10px; border-left: 3px solid #007bff;")
        layout.addWidget(self.clip_label)

        self.setLayout(layout)

    def generate_qr(self):
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(self.url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#a349a4", back_color="black")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        self.qr_label.setPixmap(pixmap)

    def update_file_list(self, filename):
        self.total_files += 1
        self.file_count_label.setText(f"Files: {self.total_files}")
        self.file_list.insertItem(0, f"✓ {filename}") # إضافة الملف في أول القائمة
        
    def show_new_text(self, text):
        self.clip_label.setText(text)

    def launch(self):
        self.show()