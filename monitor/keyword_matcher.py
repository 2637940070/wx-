"""
关键字匹配模块
负责检测文字中是否包含配置的关键字，并实现冷却（cooldown）机制防止重复触发
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """
    关键字匹配器。
    检测文字中是否包含指定关键字，并通过冷却机制避免同一关键字短时间内重复触发。
    """

    def __init__(self, cooldown: float = 30.0):
        """
        初始化关键字匹配器。

        参数：
            cooldown: 冷却时间（秒），同一关键字在此时间内不会重复触发
        """
        self.cooldown = cooldown
        # 记录每个关键字最后一次触发时间，格式：{keyword: timestamp}
        self._last_triggered: dict = {}

    def set_cooldown(self, cooldown: float) -> None:
        """设置冷却时间"""
        self.cooldown = cooldown

    def reset(self) -> None:
        """重置所有关键字的触发记录"""
        self._last_triggered.clear()
        logger.info("已重置所有关键字冷却记录")

    def match(self, text: str, rules: list) -> Optional[dict]:
        """
        在文字中查找第一个匹配且未处于冷却中的关键字规则。

        参数：
            text: 要检测的文字内容
            rules: 规则列表，每条规则为 {'keyword': str, 'reply': str, 'enabled': bool}

        返回：匹配的规则字典，未找到匹配时返回 None
        """
        if not text:
            return None

        for rule in rules:
            if not rule.get("enabled", True):
                continue

            keyword = rule.get("keyword", "")
            if not keyword:
                continue

            if keyword in text:
                # 检查冷却时间
                last_time = self._last_triggered.get(keyword, 0)
                elapsed = time.time() - last_time
                if elapsed >= self.cooldown:
                    logger.info(f"匹配到关键字：'{keyword}'（上次触发距今 {elapsed:.1f} 秒）")
                    return rule
                else:
                    remaining = self.cooldown - elapsed
                    logger.debug(
                        f"关键字 '{keyword}' 处于冷却中，还需等待 {remaining:.1f} 秒"
                    )

        return None

    def mark_triggered(self, keyword: str) -> None:
        """
        标记关键字已触发，更新最后触发时间。

        参数：
            keyword: 已触发的关键字
        """
        self._last_triggered[keyword] = time.time()
        logger.debug(f"已记录关键字触发时间：'{keyword}'")

    def is_in_cooldown(self, keyword: str) -> bool:
        """
        检查关键字是否处于冷却状态。

        参数：
            keyword: 要检查的关键字

        返回：处于冷却状态返回 True，否则返回 False
        """
        last_time = self._last_triggered.get(keyword, 0)
        elapsed = time.time() - last_time
        return elapsed < self.cooldown
