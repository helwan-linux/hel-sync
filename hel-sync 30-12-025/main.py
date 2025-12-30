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
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    
    token = "auth_token_xyz" 
    ip_addr = get_ip()
    url = f"http://{ip_addr}:8080?token={token}"

    ui = HelSyncGUI(url)

    # --- [تعديل 1: ربط الاستلام بالأسماء الصحيحة في كود الـ 230 سطر] ---
    def update_received_list_ui(filename, size):
        # بننادي على الدالة اللي إنت كاتبها جوه الـ GUI أصلاً (add_received)
        # لأنها بتحدث r_list اللي موجود فعلاً
        ui.add_received(filename, size)

    # ربط إشارة السيرفر بالدالة
    ui.comm.file_received.connect(update_received_list_ui)
    
    # ربط إشارة النص المستلم (للكليب بورد) - الاسم عندك هو in_clip
    def update_clipboard_ui(text):
        ui.in_clip.setPlainText(text)
        ui.tray_icon.showMessage("Hel-Sync", "New text received from mobile!", 1)
            
    ui.comm.text_received.connect(update_clipboard_ui)

    # 4. تفعيل زر START SENDING
    # 4. تفعيل زر START SENDING
    def start_sharing_action_bridge():
        server.FILES_TO_SHARE = ui.pending_files
        server.ACCESS_TOKEN = token
        
        # --- السطر اللي كان ناقص عشان الموبايل يستلم ---
        # ربط الـ out_clip بتاع الواجهة بـ CLIP_HISTORY بتاع السيرفر
        def sync_to_server():
            server.CLIP_HISTORY[token] = ui.out_clip.toPlainText()
            
        # جعل السيرفر يقرأ من الـ out_clip كل ما يتغير النص
        ui.out_clip.textChanged.connect(sync_to_server)
        # -----------------------------------------------
        
        ui.start_sending_action()
        ui.tray_icon.showMessage("Hel-Sync", "Server is now sharing files & text!", 1)

    ui.btn_send.clicked.disconnect()
    ui.btn_send.clicked.connect(start_sharing_action_bridge)

    # فك أي ربط قديم وربط الزر بالدالة الجديدة
    ui.btn_send.clicked.disconnect()
    ui.btn_send.clicked.connect(start_sharing_action_bridge)

    # 5. معالج الصلاحيات (Thread-Safe)
    def perm_handler(count, size):
        # بننادي إشارة تفتح الـ MessageBox من الـ Main Thread
        ui.comm.request_perm.emit(str(count), str(size))
        while not hasattr(ui, 'is_ok'):
            QApplication.processEvents()
            time.sleep(0.1)
        res = ui.is_ok
        del ui.is_ok 
        return res

    # ربط طلب الإذن بالدالة اللي بتحفظ الرد
    def secure_ask(c, s):
        ui.is_ok = ui.ask_perm(c, s)
    ui.comm.request_perm.connect(secure_ask)

    # 6. معالج العداد (الاسم عندك هو prog)
    def progress_handler(percent, filename, current, total):
        ui.prog.setValue(int(percent))
        ui.db_stats.setText(f"Receiving: {filename} ({int(percent)}%)")

    # 7. تشغيل السيرفر
    t = threading.Thread(
        target=server.start_network_service, 
        args=(ui.comm.file_received.emit, ui.comm.text_received.emit, token, perm_handler, progress_handler), 
        daemon=True
    )
    t.start()

    ui.launch()
    sys.exit(app.exec_())
