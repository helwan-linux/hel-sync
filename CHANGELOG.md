# Changelog

All notable changes to **Hel-Sync Pro** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-31

### 🚀 Added
- **Zero-App Connectivity**: Implementation of a web-based dashboard that allows mobile devices to connect via QR code without installing any APK/Apps.
- **Bi-Directional File Transfer**: Ability to send files from PC to Mobile and receive uploads from Mobile to PC.
- **Safe Permission Handler**: Added a mandatory desktop confirmation dialog for every incoming file request from mobile devices.
- **Live Clipboard Sync**: Real-time synchronization of text copied on mobile to the desktop dashboard.
- **Smart Buzz (Find My Mobile)**: Remote trigger for visual (flash) and audio (speech synthesis) alerts to locate misplaced mobile devices.
- **System Tray Integration**: Background execution support with a dedicated tray icon for quick access and status notifications.
- **Token-Based Security**: Secure access control using unique authentication tokens for every session.

### 🛠️ Changed
- **Performance Optimization**: Switched to a lightweight Flask-based backend to ensure minimal RAM usage compared to Electron-based solutions.
- **UI Refresh**: Applied the official Helwan Linux dark theme with an intuitive icon-based layout.
- **Network Discovery**: Improved local IP detection logic to support various network configurations and subnets.

### 🔒 Security
- **Privacy First**: All data transfers are strictly limited to the local area network (LAN); no data is uploaded to external servers.
- **Directory Isolation**: Isolated download path at `~/Downloads/HelSync` with automatic temporary file cleanup.

---
*Developed by Saeed Badredlden for the Helwan Linux Community.*
