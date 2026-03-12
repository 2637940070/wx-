"""
配置文件管理模块
负责读取、写入和管理 config.json 配置文件
"""

import json
import os
import logging

# 配置文件默认路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "rules": [
        {
            "keyword": "你好",
            "reply": "你好！有什么可以帮助你的吗？",
            "enabled": True
        },
        {
            "keyword": "价格",
            "reply": "请稍等，我马上为您查询价格信息。",
            "enabled": True
        },
        {
            "keyword": "在吗",
            "reply": "在的，请问有什么需要？",
            "enabled": True
        }
    ],
    "scan_interval": 3,
    "cooldown": 30,
    "send_delay": 0.5
}

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器，负责加载和保存配置文件"""

    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.config = {}
        self.load()

    def load(self) -> dict:
        """从文件加载配置，如果文件不存在则使用默认配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                logger.info(f"配置文件已加载：{self.config_path}")
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"加载配置文件失败：{e}，使用默认配置")
                self.config = DEFAULT_CONFIG.copy()
        else:
            logger.info("配置文件不存在，使用默认配置")
            self.config = DEFAULT_CONFIG.copy()
            self.save()
        return self.config

    def save(self) -> bool:
        """将当前配置保存到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置文件已保存：{self.config_path}")
            return True
        except OSError as e:
            logger.error(f"保存配置文件失败：{e}")
            return False

    def get_rules(self) -> list:
        """获取所有关键字-回复规则"""
        return self.config.get("rules", [])

    def get_enabled_rules(self) -> list:
        """获取所有已启用的规则"""
        return [r for r in self.get_rules() if r.get("enabled", True)]

    def add_rule(self, keyword: str, reply: str, enabled: bool = True) -> None:
        """添加新规则"""
        rule = {"keyword": keyword, "reply": reply, "enabled": enabled}
        self.config.setdefault("rules", []).append(rule)
        self.save()

    def remove_rule(self, index: int) -> bool:
        """删除指定索引的规则"""
        rules = self.config.get("rules", [])
        if 0 <= index < len(rules):
            rules.pop(index)
            self.save()
            return True
        return False

    def update_rule(self, index: int, keyword: str, reply: str, enabled: bool) -> bool:
        """更新指定索引的规则"""
        rules = self.config.get("rules", [])
        if 0 <= index < len(rules):
            rules[index] = {"keyword": keyword, "reply": reply, "enabled": enabled}
            self.save()
            return True
        return False

    def get_scan_interval(self) -> float:
        """获取扫描间隔时间（秒）"""
        return float(self.config.get("scan_interval", 3))

    def set_scan_interval(self, interval: float) -> None:
        """设置扫描间隔时间"""
        self.config["scan_interval"] = interval
        self.save()

    def get_cooldown(self) -> float:
        """获取冷却时间（秒），防止同一关键字重复触发"""
        return float(self.config.get("cooldown", 30))

    def set_cooldown(self, cooldown: float) -> None:
        """设置冷却时间"""
        self.config["cooldown"] = cooldown
        self.save()

    def get_send_delay(self) -> float:
        """获取发送后延迟时间（秒）"""
        return float(self.config.get("send_delay", 0.5))

    def set_send_delay(self, delay: float) -> None:
        """设置发送后延迟时间"""
        self.config["send_delay"] = delay
        self.save()
