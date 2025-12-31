import sys, threading, socket, time
from PyQt5.QtWidgets import QApplication
from hel_sync_gui.app_window import HelSyncGUI
from hel_sync_core import network_server as server

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except: ip = "127.0.0.1"
    finally: s.close()
    return ip

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    token = "auth_token_xyz" 
    ip_addr = get_ip()
    url = f"http://{ip_addr}:8080?token={token}"

    ui = HelSyncGUI(url)

    # 1. تحديث قائمة الاستلام
    ui.comm.file_received.connect(ui.add_received)

    # 2. تحديث الكليب بورد من الموبايل للكمبيوتر
    def update_clipboard_ui(text):
        ui.in_clip.setPlainText(text)
        ui.tray_icon.showMessage("Hel-Sync", "Text from Mobile Received", 1)
    ui.comm.text_received.connect(update_clipboard_ui)

    # 3. مزامنة النص من الكمبيوتر للموبايل (تلقائياً عند الكتابة)
    def sync_to_server():
        server.CLIP_HISTORY[token] = ui.out_clip.toPlainText()
    ui.out_clip.textChanged.connect(sync_to_server)

    # 4. زر البحث عن الموبايل (إشارة الرنين المطورة)
    def find_mobile():
        # تفعيل الرنين في صفحة الموبايل
        server.CLIP_HISTORY[token] = "___BUZZ_NOW___"
        ui.tray_icon.showMessage("Hel-Sync", "Buzzing Mobile... 🔔", 1)
        
        # تحسين شكل الزر لإظهار الحالة (Feedback)
        if hasattr(ui, 'btn_find'):
            ui.btn_find.setEnabled(False)
            ui.btn_find.setText("🔔 BUZZING...")

        # دالة داخلية لإيقاف الرنين وإعادة الحافظة لأصلها
        def stop_buzz_action():
            sync_to_server() # إعادة النص الأصلي الموجود في out_clip للسيرفر
            if hasattr(ui, 'btn_find'):
                ui.btn_find.setEnabled(True)
                ui.btn_find.setText("🔔 FIND MY MOBILE")
        
        # إيقاف التنبيه تلقائياً بعد 5 ثواني
        threading.Timer(5.0, stop_buzz_action).start()

    # ربط الزر الجديد (تم التأكد من وجوده في الواجهة)
    if hasattr(ui, 'btn_find'): 
        ui.btn_find.clicked.connect(find_mobile)

    # 5. زر بدء المشاركة (الجسر البرمجي)
    def start_action_bridge():
        server.FILES_TO_SHARE = ui.pending_files
        server.ACCESS_TOKEN = token
        ui.start_sending_action()
        ui.tray_icon.showMessage("Hel-Sync", "Sharing Live!", 1)

    # إعادة ربط زر الإرسال بالوظيفة الحقيقية للسيرفر
    ui.btn_send.clicked.disconnect()
    ui.btn_send.clicked.connect(start_action_bridge)

    # 6. معالج الصلاحيات الآمن
    def perm_handler(count, size):
        ui.comm.request_perm.emit(str(count), str(size))
        while not hasattr(ui, 'is_ok'):
            QApplication.processEvents()
            time.sleep(0.1)
        res = ui.is_ok
        del ui.is_ok 
        return res

    def secure_ask(c, s):
        ui.is_ok = ui.ask_perm(c, s)
    ui.comm.request_perm.connect(secure_ask)

    # 7. تشغيل السيرفر في خلفية البرنامج (Thread)
    t = threading.Thread(
        target=server.start_network_service, 
        args=(ui.comm.file_received.emit, ui.comm.text_received.emit, token, perm_handler, None), 
        daemon=True
    )
    t.start()

    # إطلاق الواجهة
    ui.launch()
    sys.exit(app.exec_())
