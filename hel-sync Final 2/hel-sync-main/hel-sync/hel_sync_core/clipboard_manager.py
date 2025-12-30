from PyQt5.QtWidgets import QApplication

class ClipboardManager:
    def __init__(self, callback):
        self.clipboard = QApplication.clipboard()
        self.callback = callback
        # ربط حدث تغير النص في الويندوز بالدالة بتاعتنا
        self.clipboard.dataChanged.connect(self.on_data_changed)

    def on_data_changed(self):
        text = self.clipboard.text()
        if text:
            self.callback(text)

    def set_text(self, text):
        # لمنع الحلقة المفرغة (Loop) بنوقف الإشارات مؤقتاً
        self.clipboard.blockSignals(True)
        self.clipboard.setText(text)
        self.clipboard.blockSignals(False)