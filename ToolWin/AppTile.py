# ------------------ App tile widget ------------------
from PySide6 import QtCore, QtGui, QtWidgets
import ctypes
from ToolWin.HelpFunction import *
import re
import os

class AppTile(QtWidgets.QFrame):
    def __init__(self, app_conf, cfg, parent=None):
        super().__init__(parent)
        self.app = app_conf
        self.cfg = cfg
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.setMinimumSize(140, 100)

        v = QtWidgets.QVBoxLayout(self)
        h = QtWidgets.QHBoxLayout()

        self.icon_lbl = QtWidgets.QLabel()
        self.icon_lbl.setFixedSize(48, 48)
        self.icon_lbl.setScaledContents(True)
        self.load_icon()
        h.addWidget(self.icon_lbl)

        self.name_lbl = QtWidgets.QLabel(self.app.get('name') or os.path.basename(self.app.get('path', '')))
        self.name_lbl.setWordWrap(True)
        h.addWidget(self.name_lbl)

        self.gear_btn = QtWidgets.QPushButton()
        self.gear_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        self.gear_btn.setFixedSize(24, 24)
        h.addWidget(self.gear_btn)

        v.addLayout(h)
        btn_h = QtWidgets.QHBoxLayout()
        launch_btn = QtWidgets.QPushButton('Launch')
        launch_btn.clicked.connect(self.on_launch)
        btn_h.addWidget(launch_btn)

        copy_btn = QtWidgets.QPushButton('Copy')
        copy_btn.clicked.connect(self.on_copy)
        btn_h.addWidget(copy_btn)

        del_btn = QtWidgets.QPushButton('Delete')
        del_btn.clicked.connect(self.on_delete)
        btn_h.addWidget(del_btn)

        v.addLayout(btn_h)

    def load_icon(self):
        ip = self.app.get('icon_path', '')
        w = max(24, self.icon_lbl.width())
        h = max(24, self.icon_lbl.height())
        if ip and os.path.exists(ip):
            pix = QtGui.QIcon(ip).pixmap(w, h)
            self.icon_lbl.setPixmap(pix)
            return
        provider = QtWidgets.QFileIconProvider()
        fi = QtCore.QFileInfo(self.app.get('path', ''))
        if fi.exists():
            icon = provider.icon(fi)
            pix = icon.pixmap(w, h)
            self.icon_lbl.setPixmap(pix)
            return
        self.icon_lbl.setPixmap(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon).pixmap(w, h))

    def _build_args_and_command(self, reload_templates=True):
        templates = (load_config().get('templates', {}) if reload_templates else self.cfg.get('templates', {}))
        quote_values = bool(self.app.get('quote_values', False))
        parts = [self.app.get('path', '')]
        for a in self.app.get('args', []):
            val = a.get('value', '')
            def repl(m):
                k = m.group(1)
                v = str(templates.get(k, k))
                if quote_values:
                    v = v.replace("'", "''")
                    return f"'{v}'"
                return v
            val_sub = re.sub(r"(TEMPLATE_[A-Z0-9_]+)", repl, val)
            name = a.get('name', '')
            if name:
                parts.append(name)
                if val_sub:
                    parts.append(val_sub)
            else:
                if val_sub:
                    parts.append(val_sub)
        return parts, ' '.join(parts)

    def on_launch(self):
        parts, assembled = self._build_args_and_command(reload_templates=True)
        if is_windows():
            try:
                ps_cmd = assembled.replace('"', '\"')
                params = f'-NoExit -Command "{ps_cmd}"'
                ctypes.windll.shell32.ShellExecuteW(None, 'runas', 'powershell.exe', params, None, 1)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, 'Launch failed', f'Failed to launch elevated PowerShell: {e}')
        else:
            launch_process(self.app.get('path'), parts[1:], self.app.get('run_as_admin', False))

    def on_copy(self):
        parts, assembled = self._build_args_and_command(reload_templates=True)
        cb = QtWidgets.QApplication.clipboard()
        cb.setText(assembled)
        QtWidgets.QMessageBox.information(self, 'Copied', 'Assembled command copied to clipboard.')

    def on_delete(self):
        win = self.window()
        if hasattr(win, 'remove_app_by_id'):
            win.remove_app_by_id(self.app.get('id'))
