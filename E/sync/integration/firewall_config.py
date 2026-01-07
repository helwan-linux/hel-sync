import subprocess
import sys

def setup_firewall():
    try:
        if sys.platform == "win32":
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', 'name=HelSync', 'dir=in', 'action=allow', 'protocol=TCP', 'localport=8080'], capture_output=True)
        else:
            # لمستخدمي آرتش ولينكس
            # البرنامج هيحاول يفتح البورت، لو ufw مش متطب مش هيعمل Error
            subprocess.run(['sudo', 'ufw', 'allow', '8080/tcp'], capture_output=True)
    except: pass