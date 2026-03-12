"""
程序入口
启动窗口文字监控自动回复工具
"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(__file__))

from gui.main_window import MainWindow


def main():
    """主函数，启动 GUI 应用"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
