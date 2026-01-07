# Maintainer: Saeed Badredlden <helwanlinux@gmail.com>
pkgname=hel-sync
pkgver=1.1.0
pkgrel=2
pkgdesc="Official synchronization utility for Helwan Linux - Zero-App philosophy."
arch=('any')
url="https://github.com/helwan-linux/hel-sync"
license=('GPL3')
# الاعتماديات الحقيقية بناءً على الكود المصدري
depends=(
    'python' 
    'python-pyqt5' 
    'python-flask' 
    'python-qrcode' 
    'python-pillow' 
    'python-pyautogui'
    'python-cryptography' # المكتبة المطلوبة لحل هذا الخطأ
    'python-pyopenssl'     # لضمان استقرار تشفير SSL
    'libxtest' 
    'libnotify'
)
makedepends=('git')
source=("git+https://github.com/helwan-linux/hel-sync.git")
md5sums=('SKIP')

package() {
    cd "$srcdir/hel-sync/sync"

    # إنشاء المسارات
    install -dm755 "$pkgdir/usr/share/hel-sync"
    install -dm755 "$pkgdir/usr/bin"
    install -dm755 "$pkgdir/usr/share/applications"
    install -dm755 "$pkgdir/usr/share/icons/hicolor/48x48/apps"

    # نسخ التطبيق
    cp -r assets hel_sync_core hel_sync_gui integration main.py \
        "$pkgdir/usr/share/hel-sync/"

    # Desktop entry
    install -m644 hel-sync.desktop \
        "$pkgdir/usr/share/applications/"

    # Icon
    install -m644 assets/icon.png \
        "$pkgdir/usr/share/icons/hicolor/48x48/apps/hel-sync.png"

    # Launcher
    cat <<'EOF' > "$pkgdir/usr/bin/hel-sync"
#!/bin/bash
cd /usr/share/hel-sync || exit 1
exec python main.py "$@"
EOF

    chmod +x "$pkgdir/usr/bin/hel-sync"
}
