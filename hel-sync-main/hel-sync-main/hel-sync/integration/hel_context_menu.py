import sys
import os
import subprocess

def add_to_context_menu():
    """إضافة البرنامج لقائمة الزر الأيمن (كليك يمين) حسب نظام التشغيل"""
    
    # أولاً: نظام ويندوز (Registry)
    if sys.platform == "win32":
        try:
            import winreg
            exe_path = os.path.abspath("main.pyw")
            key_path = r"*\shell\Send via Hel-Sync\command"
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
            # استخدام pythonw لتشغيل البرنامج بدون ظهور نافذة CMD
            winreg.SetValue(key, "", winreg.REG_SZ, f'pythonw "{exe_path}" "%1"')
            return True
        except Exception as e:
            print(f"Windows Registry Error: {e}")
            return False

    # ثانياً: نظام لينكس (Arch Linux وبقية التوزيعات)
    # بنعتمد على نظام الـ .desktop files اللي بتفهمها معظم واجهات لينكس (KDE, GNOME, XFCE)
    elif sys.platform == "linux":
        try:
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Send via Hel-Sync
Exec=python {os.path.abspath("main.pyw")} %f
Icon={os.path.abspath("assets/icon.png")}
MimeType=application/octet-stream;
NoDisplay=true
Actions=SendToHelSync;

[Desktop Action SendToHelSync]
Name=Send via Hel-Sync
Exec=python {os.path.abspath("main.pyw")} %f
"""
            # إنشاء الملف في مسار الـ Actions الخاص بالمستخدم
            path = os.path.expanduser("~/.local/share/file-manager/actions")
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            
            with open(os.path.join(path, "hel-sync-action.desktop"), "w") as f:
                f.write(desktop_entry)
            return True
        except Exception as e:
            print(f"Linux Context Menu Error: {e}")
            return False

    return False