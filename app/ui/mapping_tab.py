from PySide6.QtWidgets import QVBoxLayout, QWidget


class MappingTab(QWidget):
    def __init__(self, content_widget: QWidget, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content_widget)
