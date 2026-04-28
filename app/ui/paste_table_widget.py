from PySide6.QtWidgets import QTableWidget, QApplication, QTableWidgetItem
from PySide6.QtGui import QKeySequence, QShortcut


class PasteTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        self.paste_shortcut.activated.connect(self.paste_from_clipboard)

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text()
        if not text:
            return

        current_row = self.currentRow()
        current_col = self.currentColumn()

        if current_row < 0 or current_col < 0:
            return

        rows = text.splitlines()

        for r_idx, row_text in enumerate(rows):
            values = row_text.split("\t")

            for c_idx, value in enumerate(values):
                target_row = current_row + r_idx
                target_col = current_col + c_idx

                if target_row >= self.rowCount() or target_col >= self.columnCount():
                    continue

                item = self.item(target_row, target_col)
                if item is None:
                    item = QTableWidgetItem()
                    self.setItem(target_row, target_col, item)

                item.setText(value)