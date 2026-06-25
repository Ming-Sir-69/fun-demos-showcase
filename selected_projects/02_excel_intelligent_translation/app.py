import sys
import os

# 将 src 目录添加到模块搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()
