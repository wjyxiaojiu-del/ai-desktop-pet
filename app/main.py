import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from app.ui.pet_window import PetWindow
except Exception as e:
    with open("run.log", "a", encoding="utf-8") as f:
        f.write(f"导入失败: {e}\n{traceback.format_exc()}\n")
    raise


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("AI桌面宠物")
        app.setApplicationDisplayName("AI 桌面宠物 - 小九")
        app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        window = PetWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        with open("run.log", "a", encoding="utf-8") as f:
            f.write(f"运行异常: {e}\n{traceback.format_exc()}\n")
        raise


if __name__ == "__main__":
    main()
