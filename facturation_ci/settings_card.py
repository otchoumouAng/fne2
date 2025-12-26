from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtCore import Qt, pyqtSignal
from page._settings_card import Ui_SettingsCard
from core.theme import BG_CARD, TEXT_MAIN, TEXT_SEC, PRIMARY, BORDER

class SettingsCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, description, icon_path=None, parent=None):
        super().__init__(parent)
        self.ui = Ui_SettingsCard()
        self.ui.setupUi(self)

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Style logic matches previous implementation but applies to UI elements
        self.setStyleSheet(f"""
            QFrame#SettingsCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame#SettingsCard:hover {{
                border: 1px solid {PRIMARY};
                background-color: rgba(255, 158, 29, 0.05);
            }}
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # Set Content
        self.ui.title_label.setText(title)
        self.ui.title_label.setStyleSheet(f"color: {TEXT_MAIN}; font-weight: bold; font-size: 16px; border: none; background: transparent;")

        if description:
            self.ui.desc_label.setText(description)
            self.ui.desc_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; border: none; background: transparent;")
        else:
            self.ui.desc_label.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
