"""
OCR 文字识别引擎模块
使用 pytesseract 从图片中提取文字内容
"""

import logging
from typing import Optional

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR 识别引擎，从图片中提取文字"""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        初始化 OCR 引擎。

        参数：
            tesseract_cmd: Tesseract 可执行文件路径（Windows 下通常需要手动指定）
                           例如：r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        """
        if pytesseract is None:
            logger.error("pytesseract 未安装，OCR 功能不可用")
            return

        # 如果提供了 Tesseract 路径则进行配置
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Windows 下尝试默认安装路径
            import sys
            if sys.platform == "win32":
                import os
                default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(default_path):
                    pytesseract.pytesseract.tesseract_cmd = default_path

    def extract_text(self, image) -> str:
        """
        从图片中提取文字。

        参数：
            image: PIL Image 对象

        返回：提取到的文字字符串，失败时返回空字符串
        """
        if pytesseract is None:
            logger.error("pytesseract 未安装，无法进行 OCR")
            return ""

        if image is None:
            logger.warning("图片为 None，无法进行 OCR")
            return ""

        try:
            # 使用中文和英文语言包进行识别
            # lang='chi_sim+eng' 表示同时识别简体中文和英文
            text = pytesseract.image_to_string(
                image,
                lang="chi_sim+eng",
                config="--psm 6"
            )
            logger.debug(f"OCR 识别结果（前100字符）：{text[:100]}")
            return text
        except pytesseract.TesseractNotFoundError:
            logger.error(
                "未找到 Tesseract OCR，请先安装 Tesseract。"
                "Windows 下载地址：https://github.com/UB-Mannheim/tesseract/wiki"
            )
            return ""
        except Exception as e:
            logger.error(f"OCR 识别失败：{e}")
            return ""

    def is_available(self) -> bool:
        """检查 OCR 引擎是否可用"""
        if pytesseract is None:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
