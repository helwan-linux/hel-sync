import sys
import threading
import socket
import ctypes
import os
from PyQt5.QtWidgets import QApplication

# استيراد مكونات النظام الخاص بنا
from hel_sync_core.network_server import start_network_service
import hel_sync_core.network_server as server
from hel_sync_gui.app_window import HelSyncGUI
from hel_sync_core.security import SecurityManager
from integration.firewall_config import setup_firewall
from integration.hel_context_menu import add_to_context_menu

# إعدادات ويندوز للأيقونة (عشان تظهر بشكل صحيح في الـ Taskbar)
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('helwan.linux.helsync.v1')
except:
    pass

def get_ip():
    """جلب عنوان الـ IP الداخلي للجهاز للربط مع الموبايل"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # مش محتاج إنترنت فعلي، هو بس بيشوف الـ Interface اللي بيخرج منه البيانات
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    # 1. تفعيل ميزة الكليك يمين في النظام (مرة واحدة عند التشغيل)
    add_to_context_menu()

    # 2. فتح البورت في جدار الحماية (UFW في آرتش أو Firewall في ويندوز)
    setup_firewall()

    # 3. تشغيل محرك الواجهة الرسومية
    app = QApplication(sys.argv)
    
    # 4. توليد التوكن الأمني وإنشاء رابط الربط
    token = SecurityManager.generate_token()
    my_ip = get_ip()
    connection_url = f"http://{my_ip}:8080?token={token}"
    
    # 5. تشغيل واجهة البرنامج
    ui = HelSyncGUI(connection_url)
    
    # 6. إعداد "مراقب الكليب بورد" (Clipboard Listener)
    # أي حاجة تعملها Copy على الكمبيوتر، السيرفر بيحس بيها ويبعتها فوراً للموبايل
    def auto_clip_listener():
        text = app.clipboard().text()
        if text:
            # تحديث المتغير العالمي في السيرفر ليكون متاحاً للموبايل
            server.LATEST_CLIPBOARD = text

    # ربط حدث تغيير الكليب بورد بالدالة
    app.clipboard().dataChanged.connect(auto_clip_listener)

    # 7. دوال الـ Callback (اللي السيرفر بيناديها لما حاجة توصل من الموبايل)
    def on_file_received_callback(filename):
        # إرسال إشارة للواجهة لتحديث القائمة باسم الملف الجديد
        ui.comm.file_received.emit(filename)

    def on_text_received_callback(received_text):
        # وضع النص المستلم في كليب بورد الكمبيوتر فوراً
        app.clipboard().setText(received_text)
        # تحديث الواجهة لعرض النص المستلم
        ui.comm.text_received.emit(received_text)

    # 8. تشغيل سيرفر الشبكة في Thread منفصل (عشان الواجهة متهنجش)
    network_thread = threading.Thread(
        target=start_network_service, 
        args=(on_file_received_callback, on_text_received_callback, token), 
        daemon=True
    )
    network_thread.start()

    # 9. إطلاق نافذة البرنامج وبدء دورة الأحداث
    ui.launch()
    sys.exit(app.exec_())