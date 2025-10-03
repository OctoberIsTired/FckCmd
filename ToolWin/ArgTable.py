from PySide6 import QtWidgets, QtCore

class ArgTable(QtWidgets.QTableWidget):
    """Table widget with support for row drag & drop (move) and Up/Down buttons."""
    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(['Argument / Flag', 'Value'])
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

    def dropEvent(self, event):
        source = event.source()
        if source is not self:
            super().dropEvent(event)
            return
        drop_row = self.rowAt(event.position().toPoint().y())
        if drop_row == -1:
            drop_row = self.rowCount()
        selected_rows = sorted(set(idx.row() for idx in self.selectedIndexes()))
        if not selected_rows:
            super().dropEvent(event)
            return
        rows_data = []
        for r in selected_rows:
            name_item = self.item(r, 0)
            val_item = self.item(r, 1)
            rows_data.append((name_item.text() if name_item else '', val_item.text() if val_item else ''))
        for r in reversed(selected_rows):
            self.removeRow(r)
            if r < drop_row:
                drop_row -= 1
        for i, (n, v) in enumerate(rows_data):
            self.insertRow(drop_row + i)
            self.setItem(drop_row + i, 0, QtWidgets.QTableWidgetItem(n))
            self.setItem(drop_row + i, 1, QtWidgets.QTableWidgetItem(v))
        event.accept()

    def move_up(self):
        rows = sorted(set(idx.row() for idx in self.selectedIndexes()))
        if not rows:
            return
        for r in rows:
            if r <= 0:
                continue
            self._swap_rows(r, r - 1)
        self.clearSelection()
        for r in [max(0, x - 1) for x in rows]:
            self.selectRow(r)

    def move_down(self):
        rows = sorted(set(idx.row() for idx in self.selectedIndexes()), reverse=True)
        if not rows:
            return
        last = self.rowCount() - 1
        for r in rows:
            if r >= last:
                continue
            self._swap_rows(r, r + 1)
        self.clearSelection()
        for r in [min(last, x + 1) for x in rows]:
            self.selectRow(r)

    def _swap_rows(self, r1, r2):
        for c in range(self.columnCount()):
            it1 = self.takeItem(r1, c)
            it2 = self.takeItem(r2, c)
            self.setItem(r1, c, it2)
            self.setItem(r2, c, it1)
