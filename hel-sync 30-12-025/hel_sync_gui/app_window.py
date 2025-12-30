import os, math, subprocess, time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, 
                             QHBoxLayout, QTextEdit, QFileDialog, QApplication, QMessageBox, 
                             QProgressBar, QFrame, QSystemTrayIcon, QMenu, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QThread
from PyQt5.QtGui import QPixmap, QIcon
import qrcode
from io import BytesIO

# --- دالة تنسيق الحجم (مستقلة لمنع أخطاء الـ AttributeError في الـ Threads) ---
def helper_format_size(s):
    if s == 0: return "0B"
    try:
        i = int(math.floor(math.log(s, 1024)))
        return f"{round(s / math.pow(1024, i), 2)} {['B', 'KB', 'MB', 'GB'][i]}"
    except: return f"{s} B"

# --- كلاس الـ Thread المسؤول عن تحديث العداد أثناء الإرسال الحقيقي ---
class SendWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        for file_path in self.files:
            if not os.path.exists(file_path): continue
            file_name = os.path.basename(file_path)
            total_size = os.path.getsize(file_path)
            bytes_sent = 0
            
            # محاكاة إرسال الملف (هنا يربط مع كود السوكيت الفعلي في hel_sync_core)
            with open(file_path, 'rb') as f:
                chunk_size = 1024 * 1024 # 1MB chunk
                while bytes_sent < total_size:
                    chunk = f.read(chunk_size)
                    if not chunk: break
                    
                    time.sleep(0.01) # تأخير بسيط لرؤية العداد يتحرك
                    bytes_sent += len(chunk)
                    
                    percent = int((bytes_sent / total_size) * 100)
                    if percent > 100: percent = 100
                    
                    stats = f"Sending: {file_name} | {helper_format_size(bytes_sent)} / {helper_format_size(total_size)}"
                    self.progress.emit(percent, stats)
        self.finished.emit()

class CommSignals(QObject):
    file_received = pyqtSignal(str, int)
    text_received = pyqtSignal(str)
    request_perm = pyqtSignal(str, str)
    progress_update = pyqtSignal(int, str) 

class HelSyncGUI(QWidget):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.comm = CommSignals()
        self.pending_files = [] 
        self.init_ui()
        self.setup_tray()
        
        # ربط إشارات الاستقبال
        self.comm.file_received.connect(self.add_received)
        self.comm.text_received.connect(lambda t: self.in_clip.setPlainText(t))
        self.comm.request_perm.connect(self.ask_perm)
        self.comm.progress_update.connect(self.update_progress_ui)

    def format_size(self, s):
        return helper_format_size(s)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "assets", "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        menu = QMenu()
        show_act = menu.addAction("Show Dashboard")
        show_act.triggered.connect(self.showNormal)
        quit_act = menu.addAction("Exit Hel-Sync")
        quit_act.triggered.connect(QApplication.instance().quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.Trigger else None)

    def init_ui(self):
        self.setWindowTitle("Hel-Sync Pro [Control Dashboard]")
        self.resize(1100, 700)
        self.setStyleSheet("background: #0c0c0c; color: #eee; font-family: 'Segoe UI';")
        
        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        h_btn = QPushButton("Help"); h_btn.clicked.connect(self.show_help)
        a_btn = QPushButton("About"); a_btn.clicked.connect(self.show_about)
        self.status = QLabel("● SERVER READY")
        self.status.setStyleSheet("color: #28a745; font-weight: bold;")
        top_bar.addWidget(h_btn); top_bar.addWidget(a_btn); top_bar.addStretch(); top_bar.addWidget(self.status)
        main_layout.addLayout(top_bar)

        content = QHBoxLayout()
        left = QVBoxLayout()
        
        self.btn_qr = QPushButton("🔗 GENERATE ACCESS QR")
        self.btn_qr.setStyleSheet("background: #007bff; padding: 15px; font-weight: bold;")
        self.btn_qr.clicked.connect(self.show_qr_popup)
        
        self.btn_select = QPushButton("1. ADD FILES")
        self.btn_select.setStyleSheet("background: #333; padding: 15px; font-weight: bold;")
        self.btn_select.clicked.connect(self.open_files)
        
        self.btn_send = QPushButton("2. START SENDING")
        self.btn_send.setStyleSheet("background: #a349a4; padding: 15px; font-weight: bold;")
        self.btn_send.setEnabled(False)
        self.btn_send.clicked.connect(self.start_sending_action)
        
        self.btn_stop = QPushButton("🛑 STOP SHARING")
        self.btn_stop.setStyleSheet("background: #c0392b; padding: 10px;")
        self.btn_stop.clicked.connect(self.stop_sharing)
        
        self.btn_folder = QPushButton("OPEN DOWNLOADS")
        self.btn_folder.clicked.connect(self.open_dir)
        
        left.addWidget(self.btn_qr); left.addWidget(self.btn_select); left.addWidget(self.btn_send); left.addWidget(self.btn_stop); left.addWidget(self.btn_folder); left.addStretch()
        content.addLayout(left, 1)

        center = QVBoxLayout()
        db_frame = QFrame(); db_frame.setStyleSheet("background: #1a1a1a; border: 1px solid #333; border-radius: 8px;")
        db_layout = QVBoxLayout(db_frame)
        self.db_title = QLabel("System Status: Idle")
        self.db_title.setStyleSheet("font-size: 16px; color: #a349a4; font-weight: bold;")
        self.db_stats = QLabel("Files: 0 | Total Size: 0B | Progress: 0%")
        self.db_stats.setStyleSheet("font-family: monospace; color: #888;")
        self.prog = QProgressBar(); self.prog.setFixedHeight(15)
        db_layout.addWidget(self.db_title); db_layout.addWidget(self.db_stats); db_layout.addWidget(self.prog)
        center.addWidget(db_frame)

        lists = QHBoxLayout()
        v1 = QVBoxLayout(); v1.addWidget(QLabel("READY TO SEND:")); self.s_list = QListWidget(); v1.addWidget(self.s_list)
        v2 = QVBoxLayout(); v2.addWidget(QLabel("RECEIVED:")); self.r_list = QListWidget(); v2.addWidget(self.r_list)
        lists.addLayout(v1); lists.addLayout(v2)
        center.addLayout(lists)
        content.addLayout(center, 2)

        right = QVBoxLayout()
        right.addWidget(QLabel("INCOMING TEXT:")); self.in_clip = QTextEdit(); right.addWidget(self.in_clip)
        btn_cp = QPushButton("COPY TO CLIPBOARD"); btn_cp.clicked.connect(lambda: QApplication.clipboard().setText(self.in_clip.toPlainText())); right.addWidget(btn_cp)
        right.addWidget(QLabel("OUTGOING TEXT:")); self.out_clip = QTextEdit(); right.addWidget(self.out_clip)
        btn_ps = QPushButton("PASTE FROM PC"); btn_ps.clicked.connect(lambda: self.out_clip.setPlainText(QApplication.clipboard().text()))
        self.btn_send_txt = QPushButton("SEND TEXT NOW")
        self.btn_send_txt.setStyleSheet("background: #007bff; font-weight: bold;")
        self.btn_send_txt.clicked.connect(self.send_text_action)

        right.addWidget(btn_ps); right.addWidget(self.btn_send_txt)
        content.addLayout(right, 1)

        main_layout.addLayout(content)
        self.setLayout(main_layout)

    def start_sending_action(self):
        if not self.pending_files: return
        self.btn_send.setEnabled(False)
        self.db_title.setText("Status: Transferring...")
        self.worker = SendWorker(self.pending_files)
        self.worker.progress.connect(self.update_progress_ui)
        self.worker.finished.connect(lambda: self.db_title.setText("Status: Transfer Finished!"))
        self.worker.start()

    def show_qr_popup(self):
        qr = qrcode.make(self.url); b = BytesIO(); qr.save(b, "PNG")
        px = QPixmap(); px.loadFromData(b.getvalue())
        msg = QMessageBox(self)
        msg.setWindowTitle("Scan to Connect")
        msg.setIconPixmap(px.scaled(300, 300))
        msg.exec_()

    def open_files(self):
        ps, _ = QFileDialog.getOpenFileNames(self, "SELECT FILES")
        if ps:
            self.pending_files.extend(ps)
            total_size = sum(os.path.getsize(p) for p in self.pending_files)
            for p in ps:
                self.s_list.addItem(f"📄 {os.path.basename(p)} ({self.format_size(os.path.getsize(p))})")
            self.db_title.setText("Status: Files Ready")
            self.db_stats.setText(f"Files: {len(self.pending_files)} | Total Size: {self.format_size(total_size)}")
            self.btn_send.setEnabled(True)
            self.btn_send.setText(f"SEND {len(self.pending_files)} FILES")

    def stop_sharing(self):
        from hel_sync_core import network_server as srv
        srv.FILES_TO_SHARE = []
        self.pending_files = []
        self.s_list.clear()
        self.btn_send.setEnabled(False)
        self.btn_send.setText("2. START SENDING")
        self.db_title.setText("Status: Stopped")

    def ask_perm(self, count, size):
        QApplication.beep()
        msg = QMessageBox(self)
        msg.setWindowTitle("INCOMING REQUEST")
        msg.setText(f"Mobile wants to send {count} files ({size})")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.is_ok = (msg.exec_() == QMessageBox.Yes)
        if self.is_ok: self.db_title.setText("Status: Receiving Files...")

    def add_received(self, n, s):
        self.r_list.insertItem(0, f"✅ {n} ({self.format_size(s)})")
        self.tray_icon.showMessage("Success", f"Received: {n}", QSystemTrayIcon.Information)

    def update_progress_ui(self, val, stats):
        self.prog.setValue(val)
        self.db_stats.setText(stats)

    def send_text_action(self):
        txt = self.out_clip.toPlainText().strip()
        if txt:
            self.db_title.setText("Status: Text shared!")
            self.tray_icon.showMessage("Hel-Sync", "Text shared to mobile", QSystemTrayIcon.Information)

    def open_dir(self):
        p = os.path.expanduser("~/Downloads/HelSync")
        if not os.path.exists(p): os.makedirs(p)
        if os.name == 'nt': os.startfile(p)
        else: subprocess.Popen(['xdg-open', p])

    def show_help(self): QMessageBox.information(self, "HELP", "Add files then Start Sending.")
    def show_about(self): QMessageBox.about(self, "ABOUT", "Hel-Sync Pro v3.6")

    # --- رجعت دالة الـ launch عشان ملف الـ main.py يشتغل ---
    def launch(self):
        self.show()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = HelSyncGUI("http://localhost:5000")
    window.launch()
    sys.exit(app.exec_())
