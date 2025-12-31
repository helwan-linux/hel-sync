# 🚀 Hel-Sync  
**Experience Seamless Connectivity Between Your PC and Mobile.**

Hel-Sync is the official synchronization utility for **Helwan Linux**, designed to bridge the gap between your desktop and mobile devices using a **Zero-App philosophy**.  
No mobile application is required — just scan, connect, and share.

![License](https://img.shields.io/badge/license-GPLv3-purple.svg)  
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-blue.svg)  
![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)

---

## ✨ Key Features

📱 **Zero-App Setup**  
Connect instantly via your mobile web browser by scanning a QR code.

📂 **Bi-Directional Transfer**  
Seamlessly send files to your mobile or receive uploads on your PC.

🔒 **Privacy First**  
All data transfers happen strictly within your Local Area Network (LAN).

🔔 **Smart Buzz (Find My Mobile)**  
Misplaced your phone? Trigger a visual and audio alert directly from your dashboard.

📋 **Live Clipboard**  
Copy text on your mobile and see it appear instantly on your desktop.

🛡️ **Permission Handler**  
Secure incoming transfers with a desktop confirmation dialog.

⚙️ **System Integration**  
Minimize to tray for background operation.

---

## 🛠️ Installation

### On Helwan Linux / Arch Linux

sudo pacman -S hel-sync  

OR using Helwan Package Manager:

hpm i hel-sync  

---

### From Source (Development)

Clone the repository:  
git clone https://github.com/your-repo/hel-sync.git  
cd hel-sync  

Install dependencies:  
pip install -r requirements.txt  

Run the application:  
python main.py  

---

## 📖 How to Use

**Launch Hel-Sync**  
Open the app from your application menu or terminal.

**Connect**  
Scan the generated QR code with your smartphone.

**Share Files**

• **To PC:**  
Use the *Upload* button on the mobile dashboard.

• **To Mobile:**  
Drag files into the PC app and click *Start Sending*.

**Clipboard Sync**  
Type or paste text in the mobile *Sync Clipboard* area to send it instantly to your PC.

---

## 🛡️ Security & Privacy

Hel-Sync is built with security in mind:

• **No Cloud**  
Your files never leave your home or office network.

• **Session Tokens**  
Every connection is protected by a unique authentication token.

• **Manual Approval**  
All incoming file transfers must be approved on the desktop.

---

## 🤝 Contributing

Contributions are welcome!  
If you have ideas for improvements or find any bugs, feel free to open an issue or submit a pull request.

---

## 👨‍💻 Author

**Saeed Badredlden**  
Lead Developer – Helwan Linux Community  

📧 helwanlinux@gmail.com  

---

Part of the **Helwan Linux Ecosystem**.  
Built with ❤️ for the Open Source Community.
