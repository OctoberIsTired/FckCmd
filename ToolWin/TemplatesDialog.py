# ------------------ Dialogs ------------------

from PySide6 import QtWidgets
from ToolWin.HelpFunction import save_config
from pathlib import Path

class TemplatesDialog(QtWidgets.QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Global Templates')
        self.cfg = cfg
        self.resize(500, 300)
        layout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['Name', 'Value'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btns = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton('Add')
        add.clicked.connect(self.add_row)
        remove = QtWidgets.QPushButton('Remove')
        remove.clicked.connect(self.remove_selected)
        browse = QtWidgets.QPushButton('Browse Value')
        browse_menu = QtWidgets.QMenu(browse)
        file_action = browse_menu.addAction('File...')
        folder_action = browse_menu.addAction('Folder...')
        browse.setMenu(browse_menu)
        file_action.triggered.connect(lambda: self.browse_value(kind='file'))
        folder_action.triggered.connect(lambda: self.browse_value(kind='folder'))

        save = QtWidgets.QPushButton('Save')
        save.clicked.connect(self.on_save)
        btns.addWidget(add)
        btns.addWidget(remove)
        btns.addWidget(browse)
        btns.addStretch()
        btns.addWidget(save)
        layout.addLayout(btns)

        for k, v in sorted(self.cfg.get('templates', {}).items()):
            self._append_row(k, v)

    def add_row(self):
        self._append_row('TEMPLATE_', '')

    def _append_row(self, name, value):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(name))
        self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(value))

    def remove_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def browse_value(self, kind='file'):
        sel = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not sel:
            if self.table.rowCount() == 0:
                QtWidgets.QMessageBox.information(self, 'Info', 'No template row exists. Add a row first.')
                return
            sel = [0]
        if kind == 'file':
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', str(Path.home()), 'All Files (*)')
            if not path:
                return
        else:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder', str(Path.home()))
            if not path:
                return
        for r in sel:
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(path))

    def on_save(self):
        templates = {}
        for r in range(self.table.rowCount()):
            name_item = self.table.item(r, 0)
            val_item = self.table.item(r, 1)
            if name_item:
                k = name_item.text().strip()
                v = val_item.text() if val_item else ''
                if k:
                    templates[k] = v
        bad = [k for k in templates.keys() if not k.startswith('TEMPLATE') or k != k.upper()]
        if bad:
            resp = QtWidgets.QMessageBox.question(self, 'Warning', 'Some template names are not uppercase or do not start with "TEMPLATE". Save anyway?')
            if resp != QtWidgets.QMessageBox.Yes:
                return
        self.cfg['templates'] = templates
        save_config(self.cfg)
        self.accept()
