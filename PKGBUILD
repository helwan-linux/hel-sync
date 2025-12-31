# Maintainer: Saeed Badredlden <helwanlinux@gmail.com>
pkgname=hel-sync
pkgver=1.0.0
pkgrel=1
pkgdesc="Official synchronization utility for Helwan Linux - Zero-App philosophy."
arch=('any')
url="https://github.com/helwan-linux/hel-sync"
license=('GPL3')
# الاعتماديات الحقيقية بناءً على الكود المصدري
depends=('python' 'python-pyqt5' 'python-flask' 'python-qrcode' 'python-pillow' 'python-pyautogui')
makedepends=('git')
source=("git+https://github.com/helwan-linux/hel-sync.git")
md5sums=('SKIP')

package() {
    cd "$srcdir/$pkgname/sync"

    # 1. إنشاء المسارات الهيكلية
    install -dm755 "$pkgdir/usr/share/hel-sync"
    install -dm755 "$pkgdir/usr/bin"
    install -dm755 "$pkgdir/usr/share/applications"
    install -dm755 "$pkgdir/usr/share/icons/hicolor/48x48/apps"

    # 2. نسخ كافة المجلدات البرمجية بناءً على الهيكلة الجديدة
    cp -r assets hel_sync_core hel_sync_gui integration main.py "$pkgdir/usr/share/hel-sync/"

    # 3. تثبيت ملف الديسك توب والأيقونة
    install -m644 hel-sync.desktop "$pkgdir/usr/share/applications/"
    install -m644 assets/icon.png "$pkgdir/usr/share/icons/hicolor/48x48/apps/hel-sync.png"

    # 4. سكريبت التشغيل مع معالجة الـ Working Directory
    cat <<EOF > "$pkgdir/usr/bin/hel-sync"
#!/bin/bash
# الانتقال للمسار لضمان عمل الـ imports والـ assets
cd /usr/share/hel-sync
python main.py "\$@"
EOF
    
    chmod +x "$pkgdir/usr/bin/hel-sync"
}
