# Changelog

All notable changes to **Hel-Sync** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-31

### 🚀 Added
- **Zero-App Connectivity**: A web-based dashboard system allowing mobile devices to connect via QR code scan—no mobile app installation required.
- **Bi-Directional File Transfer**: Full support for sending files from PC to Mobile and receiving uploads from Mobile to PC.
- **Safe Permission Handler**: Mandatory desktop confirmation dialog for all incoming file requests to ensure user security.
- **Live Clipboard Sync**: Instant synchronization of text sent from mobile devices to the desktop dashboard.
- **Smart Buzz (Find My Mobile)**: Remote utility to locate misplaced phones by triggering visual (screen flash) and audio (speech synthesis) alerts.
- **System Tray Integration**: Background operation support with a tray icon for persistent connectivity and quick status updates.
- **Token-Based Security**: Unique access tokens generated for each session to prevent unauthorized network access.

### 🛠️ Changed
- **Performance Optimization**: Developed using a lightweight Flask backend and PyQt5 to ensure minimal resource consumption on Helwan Linux.
- **UI Design**: Implemented the official Helwan Linux dark aesthetic with a clean, user-friendly interface.
- **Network Logic**: Advanced local IP detection to ensure seamless operation across various LAN environments.

### 🔒 Security
- **Privacy First**: All communications and data transfers are kept strictly within the local network (LAN).
- **Safe Directory**: Dedicated download management at `~/Downloads/HelSync` with secure temporary file handling.

---
*Developed by Saeed Badredlden for the Helwan Linux Community.*
