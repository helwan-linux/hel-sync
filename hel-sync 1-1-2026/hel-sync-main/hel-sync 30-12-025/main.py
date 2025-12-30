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

    # 4. زر البحث عن الموبايل (إشارة الرنين)
    def find_mobile():
        server.CLIP_HISTORY[token] = "___BUZZ_NOW___"
        ui.tray_icon.showMessage("Hel-Sync", "Buzzing Mobile...", 1)
        # نرجع الكليب بورد لوضعه بعد 5 ثواني عشان الرنين يوقف
        threading.Timer(5.0, sync_to_server).start()

    # افترضنا إن عندك زرار في الواجهة اسمه btn_find (لو مش موجود ضيفه أو اربطه بزرار تاني)
    if hasattr(ui, 'btn_find'): ui.btn_find.clicked.connect(find_mobile)

    # 5. زر بدء المشاركة
    def start_action_bridge():
        server.FILES_TO_SHARE = ui.pending_files
        server.ACCESS_TOKEN = token
        ui.start_sending_action()
        ui.tray_icon.showMessage("Hel-Sync", "Sharing Live!", 1)

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

    # 7. تشغيل السيرفر
    t = threading.Thread(
        target=server.start_network_service, 
        args=(ui.comm.file_received.emit, ui.comm.text_received.emit, token, perm_handler, None), 
        daemon=True
    )
    t.start()

    ui.launch()
    sys.exit(app.exec_())
