import sys, threading, socket, time
from PyQt5.QtWidgets import QApplication
from hel_sync_gui.app_window import HelSyncGUI
from hel_sync_core import network_server as server

def get_ip():
    """هذه الدالة تجلب آي بي الجهاز المحلي لكي يظهر في الـ QR code"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    # 1. تشغيل التطبيق
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # لضمان استمرار البرنامج في الـ Tray
    
    # 2. إعداد بيانات الأمان والرابط
    token = "auth_token_xyz" # التوكن اللي بيمنع أي حد غريب يدخل على ملفاتك
    ip_addr = get_ip()
    url = f"http://{ip_addr}:8080?token={token}"

    # 3. تشغيل واجهتك الأصلية
    ui = HelSyncGUI(url)

    # 4. تفعيل "روح" البرنامج (ربط زر START SENDING)
    def start_sharing_action():
        # هنا بننقل الملفات اللي انت اخترتها في الواجهة للسيرفر عشان الموبايل يشوفها
        server.FILES_TO_SHARE = ui.pending_files
        server.ACCESS_TOKEN = token
        ui.db_title.setText("Status: Sharing Live")
        ui.btn_send.setEnabled(False)
        ui.tray_icon.showMessage("Hel-Sync", "Server is now sharing files!", 1)

    ui.btn_send.clicked.connect(start_sharing_action)

    # 5. معالج الصلاحيات (Permission Handler)
    # ده اللي بيخلي البرنامج يوقف الموبايل ويفتح لك رسالة Yes/No في الواجهة
    def perm_handler(count, size):
        ui.comm.request_perm.emit(str(count), str(size))
        # انتظار ردك من الواجهة (Yes أو No)
        while not hasattr(ui, 'is_ok'):
            QApplication.processEvents()
            time.sleep(0.1)
        res = ui.is_ok
        del ui.is_ok # مسح الحالة لبعدين
        return res

    # 6. تشغيل السيرفر في Thread منفصل عشان الواجهة ما تهنجش
    t = threading.Thread(
        target=server.start_network_service, 
        args=(ui.comm.file_received.emit, ui.comm.text_received.emit, token, perm_handler), 
        daemon=True
    )
    t.start()

    # 7. إطلاق الواجهة
    ui.launch()
    sys.exit(app.exec_())
