# ------------------ Main Window ------------------

from PySide6 import QtCore, QtGui, QtWidgets
from ToolWin.HelpFunction import *
from config import *
from ToolWin.AddEditAppDialog import AddEditAppDialog
from ToolWin.AppTile import *
from ToolWin.TemplatesDialog import TemplatesDialog

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Launcher')
        self.resize(900, 600)
        self.cfg = load_config()
        self.setup_ui()

    def setup_ui(self):
        w = QtWidgets.QWidget()
        self.setCentralWidget(w)
        h = QtWidgets.QHBoxLayout(w)

        left_v = QtWidgets.QVBoxLayout()
        self.templates_btn = QtWidgets.QPushButton('Add Global Template')
        self.templates_btn.clicked.connect(self.open_templates)
        left_v.addWidget(self.templates_btn)

        self.import_btn = QtWidgets.QPushButton('Import Config')
        self.import_btn.clicked.connect(self.import_config)
        left_v.addWidget(self.import_btn)

        self.export_btn = QtWidgets.QPushButton('Export Config')
        self.export_btn.clicked.connect(self.export_config)
        left_v.addWidget(self.export_btn)

        self.clear_btn = QtWidgets.QPushButton('Clear Config')
        self.clear_btn.clicked.connect(self.clear_config)
        left_v.addWidget(self.clear_btn)

        left_v.addStretch()
        h.addLayout(left_v, 0)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(container)
        self.grid.setSpacing(12)
        self.container = container
        self.scroll.setWidget(container)
        h.addWidget(self.scroll, 1)

        self.reload_grid()

    def reload_grid(self):
        # refresh config from disk
        self.cfg = load_config()
        # remove all
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)
        # compute number of columns based on available width of scroll viewport
        viewport_w = max(200, self.scroll.viewport().width())
        cols = max(1, viewport_w // DESIRED_TILE_WIDTH)
        # add '+' button as the first tile
        add_btn = QtWidgets.QPushButton('+')
        add_btn.setMinimumSize(160, 100)
        add_btn.clicked.connect(self.add_app)
        self.grid.addWidget(add_btn, 0, 0)

        apps = self.cfg.get('apps', [])
        for idx, app in enumerate(apps):
            # place starting from index 1 (0 reserved for add button)
            pos = idx + 1
            r = pos // cols
            c = pos % cols
            tile = AppTile(app, self.cfg)
            tile.gear_btn.clicked.connect(lambda checked=False, a=app: self.edit_app(a))
            self.grid.addWidget(tile, r, c)
        # schedule icon adjustment
        QtCore.QTimer.singleShot(50, self.adjust_tile_icons)

    def adjust_tile_icons(self):
        # iterate widgets in layout and adjust icon sizes proportionally to tile width
        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if not w or not isinstance(w, AppTile):
                continue
            tw = w.width() or w.sizeHint().width() or w.minimumWidth()
            iw = max(24, min(96, int(tw * 0.25)))
            w.icon_lbl.setFixedSize(iw, iw)
            w.load_icon()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # recalc grid (columns) + adjust icons after resize
        QtCore.QTimer.singleShot(50, self.reload_grid)

    def add_app(self):
        dlg = AddEditAppDialog(self.cfg, parent=self)
        if dlg.exec():
            self.cfg = load_config()
            self.reload_grid()

    def edit_app(self, app):
        dlg = AddEditAppDialog(self.cfg, app, parent=self)
        if dlg.exec():
            self.cfg = load_config()
            self.reload_grid()

    def remove_app(self, app):
        resp = QtWidgets.QMessageBox.question(self, 'Remove', f'Remove {app.get("name")}?')
        if resp == QtWidgets.QMessageBox.Yes:
            apps = [a for a in self.cfg.get('apps', []) if a.get('id') != app.get('id')]
            self.cfg['apps'] = apps
            save_config(self.cfg)
            self.reload_grid()

    def remove_app_by_id(self, app_id):
        apps = [a for a in self.cfg.get('apps', []) if a.get('id') != app_id]
        old = next((a for a in self.cfg.get('apps', []) if a.get('id') == app_id), None)
        if old:
            resp = QtWidgets.QMessageBox.question(self, 'Remove', f'Remove {old.get("name")} ?')
            if resp != QtWidgets.QMessageBox.Yes:
                return
        self.cfg['apps'] = apps
        save_config(self.cfg)
        self.reload_grid()

    def export_config(self):
        p, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export config to file', str(APP_DIR), 'JSON Files (*.json)')
        if not p:
            return
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
            QtWidgets.QMessageBox.information(self, 'Export', 'Config exported successfully.')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Export failed', f'Failed to export: {e}')

    def import_config(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Import config from file', str(APP_DIR), 'JSON Files (*.json)')
        if not p:
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            resp = QtWidgets.QMessageBox.question(self, 'Import', 'Replace current configuration with imported one? (No will merge)')
            if resp == QtWidgets.QMessageBox.Yes:
                self.cfg = data
            else:
                t = self.cfg.get('templates', {})
                t.update(data.get('templates', {}))
                a = self.cfg.get('apps', [])
                a.extend(data.get('apps', []))
                self.cfg['templates'] = t
                self.cfg['apps'] = a
            save_config(self.cfg)
            self.reload_grid()
            QtWidgets.QMessageBox.information(self, 'Import', 'Import completed.')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Import failed', f'Failed to import: {e}')

    def clear_config(self):
        resp = QtWidgets.QMessageBox.question(self, 'Clear', 'Clear current configuration file? This will remove all apps and templates.')
        if resp != QtWidgets.QMessageBox.Yes:
            return
        self.cfg = {'apps': [], 'templates': {}}
        save_config(self.cfg)
        self.reload_grid()

    def open_templates(self):
        dlg = TemplatesDialog(self.cfg, parent=self)
        if dlg.exec():
            self.cfg = load_config()
            self.reload_grid()