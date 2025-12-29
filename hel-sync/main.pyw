import sys, threading, socket
from PyQt5.QtWidgets import QApplication
from hel_sync_core import network_server as server
from hel_sync_gui.app_window import HelSyncGUI

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except: ip = "127.0.0.1"
    finally: s.close()
    return ip

if __name__ == "__main__":
    app = QApplication(sys.argv)
    token = "secure_token_123" # للتجربة، يفضل توليدها عشوائياً
    ui = HelSyncGUI(f"http://{get_ip()}:8080?token={token}")

    # استقبال الملفات من الكليك يمين (الكل وليس الأخير فقط)
    incoming_files = sys.argv[1:] 
    if incoming_files:
        server.FILES_TO_SHARE.extend(incoming_files)

    def file_received_handler(filename):
        ui.comm.file_received.emit(filename)

    # تشغيل السيرفر في خلفية منفصلة
    t = threading.Thread(target=server.start_network_service, 
                         args=(file_received_handler, None, token), daemon=True)
    t.start()

    ui.launch()
    sys.exit(app.exec_())