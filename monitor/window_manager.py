"""
窗口管理模块
负责列举系统中的所有可见窗口，激活指定窗口，并对窗口进行截图
"""

import logging
from typing import Optional

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    from PIL import ImageGrab, Image
except ImportError:
    ImageGrab = None
    Image = None

logger = logging.getLogger(__name__)


class WindowManager:
    """窗口管理器，提供窗口列举、激活和截图功能"""

    def get_all_windows(self) -> list:
        """
        获取当前系统中所有可见窗口的标题列表。
        过滤掉标题为空的窗口。

        返回：包含 (hwnd_or_index, title) 元组的列表
        """
        windows = []
        if gw is None:
            logger.error("pygetwindow 未安装，无法获取窗口列表")
            return windows

        try:
            all_wins = gw.getAllWindows()
            for win in all_wins:
                title = (win.title or "").strip()
                if title:
                    windows.append(title)
        except Exception as e:
            logger.error(f"获取窗口列表失败：{e}")

        return windows

    def get_window(self, title: str):
        """
        通过标题获取窗口对象。
        支持精确匹配，如果没有找到则返回 None。

        参数：
            title: 窗口标题

        返回：窗口对象或 None
        """
        if gw is None:
            logger.error("pygetwindow 未安装")
            return None

        try:
            wins = gw.getWindowsWithTitle(title)
            if wins:
                return wins[0]
        except Exception as e:
            logger.error(f"获取窗口失败（标题='{title}'）：{e}")
        return None

    def activate_window(self, title: str) -> bool:
        """
        激活（置于前台）指定标题的窗口。

        参数：
            title: 窗口标题

        返回：成功返回 True，失败返回 False
        """
        win = self.get_window(title)
        if win is None:
            logger.warning(f"未找到窗口：{title}")
            return False

        try:
            if win.isMinimized:
                win.restore()
            win.activate()
            logger.info(f"已激活窗口：{title}")
            return True
        except Exception as e:
            logger.error(f"激活窗口失败（标题='{title}'）：{e}")
            return False

    def capture_window(self, title: str) -> Optional[object]:
        """
        对指定窗口进行截图。

        参数：
            title: 窗口标题

        返回：PIL Image 对象，失败时返回 None
        """
        if ImageGrab is None:
            logger.error("Pillow 未安装，无法进行截图")
            return None

        win = self.get_window(title)
        if win is None:
            logger.warning(f"未找到窗口，无法截图：{title}")
            return None

        try:
            # 获取窗口边界坐标
            left = win.left
            top = win.top
            right = win.left + win.width
            bottom = win.top + win.height

            if win.width <= 0 or win.height <= 0:
                logger.warning(f"窗口尺寸无效：{title}，宽={win.width}，高={win.height}")
                return None

            # 截取窗口区域
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            logger.debug(f"截图成功：{title}，尺寸={screenshot.size}")
            return screenshot
        except Exception as e:
            logger.error(f"截图失败（标题='{title}'）：{e}")
            return None
