# Maintainer: Saeed Badredlden <helwanlinux@gmail.com>
pkgname=hel-sync
pkgver=1.1.0
pkgrel=4
pkgdesc="Official synchronization utility for Helwan Linux - Zero-App philosophy."
arch=('any')
url="https://github.com/helwan-linux/hel-sync"
license=('GPL3')

depends=(
    'python' 
    'python-pyqt5' 
    'python-flask' 
    'python-qrcode' 
    'python-pillow' 
    'python-pyautogui'
    'python-cryptography'
    'python-pyopenssl'
    'xdotool'
    'libxtst'
    'libnotify'
    'libcanberra'
    'sound-theme-freedesktop'
)
makedepends=('git')
source=("git+https://github.com/helwan-linux/hel-sync.git")
md5sums=('SKIP')

package() {
    cd "$srcdir/hel-sync/sync" 

    # 1. تثبيت ملفات البرنامج في /opt
    install -dm755 "$pkgdir/opt/hel-sync"
    cp -r * "$pkgdir/opt/hel-sync/"

    # 2. إنشاء المشغل (Launcher) في /usr/bin
    install -dm755 "$pkgdir/usr/bin"
    cat <<'EOF' > "$pkgdir/usr/bin/hel-sync"
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=$HOME/.Xauthority
cd /opt/hel-sync && python main.py "$@"
EOF
    chmod +x "$pkgdir/usr/bin/hel-sync"

    # 3. تثبيت الأيقونة في مسار النظام (هذا ما كان ينقصك)
    # نقوم بنسخها من مجلد assets إلى pixmaps ليراها النظام 
    install -Dm644 "assets/icon.png" "$pkgdir/usr/share/pixmaps/hel-sync.png"

    # 4. تثبيت ملف الـ Desktop Entry
    install -Dm644 "hel-sync.desktop" "$pkgdir/usr/share/applications/hel-sync.desktop"
}
