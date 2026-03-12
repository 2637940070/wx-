"""
自动发送消息模块
使用 pyperclip（剪贴板）+ pyautogui 模拟键盘输入发送中文消息
"""

import time
import logging

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # 将鼠标移动到屏幕左上角可触发安全中断
    pyautogui.PAUSE = 0.05    # 每次操作间隔 0.05 秒
except ImportError:
    pyautogui = None

logger = logging.getLogger(__name__)


class AutoSender:
    """
    自动消息发送器。
    通过剪贴板粘贴方式发送消息，可正确处理中文字符。
    """

    def __init__(self, send_delay: float = 0.5):
        """
        初始化自动发送器。

        参数：
            send_delay: 发送完成后的延迟时间（秒），避免操作过快
        """
        self.send_delay = send_delay

    def set_send_delay(self, delay: float) -> None:
        """设置发送后延迟时间"""
        self.send_delay = delay

    def send_message(self, message: str) -> bool:
        """
        发送消息到当前激活的窗口。
        使用剪贴板粘贴方式，支持中文输入。

        参数：
            message: 要发送的消息内容

        返回：成功返回 True，失败返回 False
        """
        if not message:
            logger.warning("消息内容为空，跳过发送")
            return False

        if pyautogui is None:
            logger.error("pyautogui 未安装，无法发送消息")
            return False

        if pyperclip is None:
            logger.error("pyperclip 未安装，无法使用剪贴板发送中文消息")
            return False

        try:
            # 备份当前剪贴板内容
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                pass

            # 将消息写入剪贴板
            pyperclip.copy(message)
            logger.debug(f"已将消息复制到剪贴板：{message[:50]}")

            # 短暂等待剪贴板就绪
            time.sleep(0.1)

            # 使用 Ctrl+V 粘贴消息
            pyautogui.hotkey("ctrl", "v")
            logger.debug("已模拟 Ctrl+V 粘贴")

            # 短暂等待粘贴完成
            time.sleep(0.1)

            # 按下 Enter 键发送
            pyautogui.press("enter")
            logger.info(f"消息已发送：{message[:50]}")

            # 发送后延迟，避免操作过快
            if self.send_delay > 0:
                time.sleep(self.send_delay)

            # 恢复剪贴板内容
            try:
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            except Exception:
                pass

            return True

        except pyautogui.FailSafeException:
            logger.warning("pyautogui 安全中断（鼠标移至左上角触发）")
            return False
        except Exception as e:
            logger.error(f"发送消息失败：{e}")
            return False

    def click_input_area(self, x: int, y: int) -> bool:
        """
        点击指定坐标（通常用于点击输入框）。

        参数：
            x: 横坐标
            y: 纵坐标

        返回：成功返回 True，失败返回 False
        """
        if pyautogui is None:
            logger.error("pyautogui 未安装")
            return False

        try:
            pyautogui.click(x, y)
            time.sleep(0.1)
            logger.debug(f"已点击坐标 ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"点击失败：{e}")
            return False
