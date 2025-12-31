# Maintainer: Saeed Badredlden <helwanlinux@gmail.com>
pkgname=hel-sync
pkgver=1.0.0
pkgrel=1
pkgdesc="Official synchronization utility for Helwan Linux - Zero-App philosophy."
arch=('any')
url="https://github.com/helwan-linux/hel-sync"
license=('GPL3')
depends=('python' 'python-pyqt5' 'python-flask' 'python-qrcode' 'python-netifaces' 'python-pillow')
makedepends=('git')
source=("git+https://github.com/helwan-linux/hel-sync.git")
md5sums=('SKIP')

package() {
    # الدخول إلى مجلد المشروع ثم المجلد الفرعي sync
    cd "$srcdir/$pkgname/sync"

    # 1. إنشاء المجلدات اللازمة في جذور النظام (Root)
    install -dm755 "$pkgdir/usr/share/hel-sync"
    install -dm755 "$pkgdir/usr/bin"
    install -dm755 "$pkgdir/usr/share/applications"
    install -dm755 "$pkgdir/usr/share/icons/hicolor/48x48/apps"

    # 2. نسخ محتويات مجلد sync بالكامل إلى مسار البرنامج
    cp -r assets hel_sync_core hel_sync_gui integration main.py "$pkgdir/usr/share/hel-sync/"

    # 3. تثبيت ملف الـ Desktop والأيقونة
    install -m644 hel-sync.desktop "$pkgdir/usr/share/applications/"
    install -m644 assets/icon.png "$pkgdir/usr/share/icons/hicolor/48x48/apps/hel-sync.png"

    # 4. إنشاء سكريبت التشغيل الأساسي
    cat <<EOF > "$pkgdir/usr/bin/hel-sync"
#!/bin/bash
# الانتقال للمجلد لضمان عمل المسارات النسبية داخل كود بايثون
cd /usr/share/hel-sync
python main.py "\$@"
EOF
    
    # إعطاء صلاحية التنفيذ للسكريبت
    chmod +x "$pkgdir/usr/bin/hel-sync"
}
