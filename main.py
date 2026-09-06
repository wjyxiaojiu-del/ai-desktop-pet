"""桌面宠物 — 轻量入口"""

import sys
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from pet import DesktopPet


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("桌面宠物")
        app.setQuitOnLastWindowClosed(False)
        pet = DesktopPet()
        sys.exit(app.exec())
    except Exception:
        with open("pet_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
