#!/usr/bin/env python3
"""
App Launcher (PySide6)

Features implemented according to specification:
- Grid of app icons; first tile is a large "+" button to add an app.
- Clicking an app tile launches the app with arguments assembled from its arguments table (top->bottom).
- Each app tile has a gear button to edit configuration for that app.
- Add/Edit dialog supports:
  1) Path to executable
  2) Arguments table (name / value). Values may contain TEMPLATE_* tokens; tokens are replaced from global templates.
  3) Order of arguments: supports drag-and-drop reordering of table rows and Up/Down buttons.
  4) Live preview of the full command assembled from the table (bottom of dialog).
  5) Save — writes configuration to JSON file (launcher_config.json next to script).
  6) Dropdown of global templates (insert into value cell)
  7) Icon: loaded from provided icon file (png/ico) or from executable using QFileIconProvider
  8) Name field for the app
  9) Checkbox: run as administrator
 10) Checkbox: wrap substituted values in single quotes (per-app)
- Left side button "Add Global Template" opens template manager (add/edit/remove keys and values). Keys by convention: uppercase and start with TEMPLATE_.
- Configuration file stores JSON containing apps and templates.

Adaptive UI change:
- AppTile icons adapt to tile size. The grid is now responsive: number of columns is recalculated depending on available width so tiles wrap to next line when window is narrowed.

Requirements: pip install PySide6

"""

from ToolWin import MainWindow
from PySide6 import QtWidgets
import sys

# ------------------ Main ------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow.MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
