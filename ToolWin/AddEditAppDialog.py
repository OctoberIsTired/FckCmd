from PySide6 import QtWidgets
import uuid
import os
from ToolWin.ArgTable import *
from ToolWin.HelpFunction import save_config
from config import *
import re

class AddEditAppDialog(QtWidgets.QDialog):
    def __init__(self, cfg, app=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add / Edit App')
        self.cfg = cfg
        self.app = app.copy() if app else None
        self.resize(760, 560)

        main = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QGridLayout()

        form.addWidget(QtWidgets.QLabel('Name:'), 0, 0)
        self.name_edit = QtWidgets.QLineEdit(self.app.get('name', '') if self.app else '')
        form.addWidget(self.name_edit, 0, 1, 1, 3)

        form.addWidget(QtWidgets.QLabel('Path to executable:'), 1, 0)
        self.path_edit = QtWidgets.QLineEdit(self.app.get('path', '') if self.app else '')
        browse = QtWidgets.QPushButton('Browse')
        browse.clicked.connect(self.browse_exe)
        form.addWidget(self.path_edit, 1, 1, 1, 2)
        form.addWidget(browse, 1, 3)

        form.addWidget(QtWidgets.QLabel('Icon (optional):'), 2, 0)
        self.icon_edit = QtWidgets.QLineEdit(self.app.get('icon_path', '') if self.app else '')
        icon_browse = QtWidgets.QPushButton('Choose')
        icon_browse.clicked.connect(self.browse_icon)
        form.addWidget(self.icon_edit, 2, 1, 1, 2)
        form.addWidget(icon_browse, 2, 3)

        self.admin_cb = QtWidgets.QCheckBox('Run as administrator')
        self.admin_cb.setChecked(self.app.get('run_as_admin', False) if self.app else False)
        form.addWidget(self.admin_cb, 3, 0, 1, 2)

        self.quote_cb = QtWidgets.QCheckBox("Wrap substituted values in single quotes (')")
        self.quote_cb.setChecked(self.app.get('quote_values', False) if self.app else False)
        form.addWidget(self.quote_cb, 3, 2, 1, 2)

        main.addLayout(form)

        args_label = QtWidgets.QLabel('Arguments (top -> bottom order):')
        main.addWidget(args_label)

        self.args_table = ArgTable()
        main.addWidget(self.args_table, 1)

        ctrl_h = QtWidgets.QHBoxLayout()
        add_arg = QtWidgets.QPushButton('Add Arg')
        add_arg.clicked.connect(lambda: self.args_table.insertRow(self.args_table.rowCount()) or self.args_table.setItem(self.args_table.rowCount()-1,0,QtWidgets.QTableWidgetItem('')))
        remove_arg = QtWidgets.QPushButton('Remove')
        remove_arg.clicked.connect(self.remove_selected_args)
        up_btn = QtWidgets.QPushButton('Move Up')
        up_btn.clicked.connect(self.args_table.move_up)
        down_btn = QtWidgets.QPushButton('Move Down')
        down_btn.clicked.connect(self.args_table.move_down)

        ctrl_h.addWidget(add_arg)
        ctrl_h.addWidget(remove_arg)
        ctrl_h.addWidget(up_btn)
        ctrl_h.addWidget(down_btn)

        self.templates_combo = QtWidgets.QComboBox()
        self.templates_combo.addItem('--- Insert template into value ---')
        for k in sorted(self.cfg.get('templates', {}).keys()):
            self.templates_combo.addItem(k)
        self.templates_combo.activated.connect(self.insert_template)
        ctrl_h.addWidget(self.templates_combo)
        ctrl_h.addStretch()

        main.addLayout(ctrl_h)

        if self.app:
            for arg in self.app.get('args', []):
                row = self.args_table.rowCount()
                self.args_table.insertRow(row)
                self.args_table.setItem(row, 0, QtWidgets.QTableWidgetItem(arg.get('name', '')))
                self.args_table.setItem(row, 1, QtWidgets.QTableWidgetItem(arg.get('value', '')))

        main.addWidget(QtWidgets.QLabel('Assembled command (with tokens):'))
        self.preview_tokens = QtWidgets.QLineEdit()
        self.preview_tokens.setReadOnly(True)
        main.addWidget(self.preview_tokens)

        main.addWidget(QtWidgets.QLabel('Executed command (templates substituted):'))
        self.preview_executed = QtWidgets.QLineEdit()
        self.preview_executed.setReadOnly(True)
        main.addWidget(self.preview_executed)

        buttons = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton('Save')
        save_btn.clicked.connect(self.on_save)
        cancel_btn = QtWidgets.QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        main.addLayout(buttons)

        self.args_table.itemChanged.connect(self.update_preview)
        self.path_edit.textChanged.connect(self.update_preview)
        self.icon_edit.textChanged.connect(self.update_preview)
        self.name_edit.textChanged.connect(self.update_preview)
        self.quote_cb.stateChanged.connect(self.update_preview)
        self.update_preview()

    def browse_exe(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select executable', str(APP_DIR))
        if p:
            self.path_edit.setText(p)
            if not self.icon_edit.text():
                self.icon_edit.setText('')

    def browse_icon(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select icon', str(APP_DIR), 'Images (*.png *.ico *.jpg *.bmp)')
        if p:
            self.icon_edit.setText(p)

    def remove_selected_args(self):
        rows = sorted({idx.row() for idx in self.args_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.args_table.removeRow(r)
        self.update_preview()

    def insert_template(self, idx):
        if idx <= 0:
            return
        key = self.templates_combo.itemText(idx)
        sel = self.args_table.selectedIndexes()
        if sel:
            row = sel[0].row()
            cur = self.args_table.item(row, 1)
            if cur is None:
                cur = QtWidgets.QTableWidgetItem('')
                self.args_table.setItem(row, 1, cur)
            cur.setText((cur.text() or '') + key)
        else:
            row = self.args_table.rowCount()
            self.args_table.insertRow(row)
            self.args_table.setItem(row, 1, QtWidgets.QTableWidgetItem(key))
        self.update_preview()

    def _substitute_templates(self, assembled, templates, wrap_values=False):
        def repl(m):
            k = m.group(1)
            val = str(templates.get(k, k))
            if wrap_values:
                val_escaped = val.replace("'", "''")
                return f"'{val_escaped}'"
            return val
        return re.sub(r"(TEMPLATE_[A-Z0-9_]+)", repl, assembled)

    def update_preview(self):
        path = self.path_edit.text().strip()
        parts = [path] if path else []
        for r in range(self.args_table.rowCount()):
            name_item = self.args_table.item(r, 0)
            val_item = self.args_table.item(r, 1)
            name = name_item.text().strip() if name_item else ''
            val = val_item.text().strip() if val_item else ''
            if name:
                parts.append(name)
                if val:
                    parts.append(val)
            else:
                if val:
                    parts.append(val)
        assembled = ' '.join(parts)
        templates = self.cfg.get('templates', {})
        executed = self._substitute_templates(assembled, templates, wrap_values=self.quote_cb.isChecked())
        self.preview_tokens.setText(assembled)
        self.preview_executed.setText(executed)

    def on_save(self):
        path = self.path_edit.text().strip()
        if not path or not os.path.exists(path):
            QtWidgets.QMessageBox.warning(self, 'Validation', 'Please select a valid executable path.')
            return
        name = self.name_edit.text().strip() or os.path.basename(path)
        icon_path = self.icon_edit.text().strip() or ''
        run_as_admin = bool(self.admin_cb.isChecked())
        quote_values = bool(self.quote_cb.isChecked())
        args = []
        for r in range(self.args_table.rowCount()):
            name_item = self.args_table.item(r, 0)
            val_item = self.args_table.item(r, 1)
            args.append({'name': (name_item.text().strip() if name_item else ''), 'value': (val_item.text().strip() if val_item else '')})

        app_conf = {
            'id': self.app.get('id') if self.app else str(uuid.uuid4()),
            'name': name,
            'path': path,
            'icon_path': icon_path,
            'run_as_admin': run_as_admin,
            'quote_values': quote_values,
            'args': args
        }
        cfg_apps = self.cfg.get('apps', [])
        if self.app:
            for i, a in enumerate(cfg_apps):
                if a.get('id') == app_conf['id']:
                    cfg_apps[i] = app_conf
                    break
            else:
                cfg_apps.append(app_conf)
        else:
            cfg_apps.append(app_conf)
        self.cfg['apps'] = cfg_apps
        save_config(self.cfg)
        self.accept()
