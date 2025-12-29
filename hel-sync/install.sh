#!/bin/bash

# ألوان للتنسيق في الترمينال
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}--- Hel-Sync Auto Installer for Arch Linux ---${NC}"

# 1. تحديث النظام وتثبيت المكتبات الأساسية
echo -e "${GREEN}[1/4] Installing system dependencies...${NC}"
sudo pacman -S --needed --noconfirm \
    python-pyqt5 \
    python-flask \
    python-qrcode \
    python-pillow \
    python-setuptools \
    xclip \
    wl-clipboard \
    ufw

# 2. إعداد جدار الحماية
echo -e "${GREEN}[2/4] Setting up Firewall (Port 8080)...${NC}"
sudo systemctl enable --now ufw
sudo ufw allow 8080/tcp

# 3. إنشاء مجلد التحميلات الافتراضي
echo -e "${GREEN}[3/4] Creating Downloads folder...${NC}"
mkdir -p ~/Downloads/HelSync

# 4. جعل ملف تشغيل البرنامج قابل للتنفيذ
echo -e "${GREEN}[4/4] Setting permissions...${NC}"
chmod +x main.pyw

echo -e "${PURPLE}------------------------------------------${NC}"
echo -e "${GREEN}Done! You can now run the app using:${NC}"
echo -e "python main.pyw"
echo -e "${PURPLE}------------------------------------------${NC}"