"""
tkinter 主窗口界面模块
提供图形化界面用于配置和控制窗口文字监控自动回复工具
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import logging
import os

from monitor.config_manager import ConfigManager
from monitor.window_manager import WindowManager
from monitor.ocr_engine import OCREngine
from monitor.keyword_matcher import KeywordMatcher
from monitor.auto_sender import AutoSender

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "monitor.log")

# 激活窗口后等待其完成前台切换的时间（秒）
WINDOW_ACTIVATE_DELAY = 0.3


def setup_logging(log_widget=None):
    """配置日志系统，同时输出到文件和 GUI 日志组件"""
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 文件处理器
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    return root_logger


class GUILogHandler(logging.Handler):
    """将日志输出到 tkinter Text 组件的自定义日志处理器"""

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        )
        self.setFormatter(formatter)
        self.setLevel(logging.INFO)

    def emit(self, record):
        msg = self.format(record) + "\n"
        # 通过 after 方法在主线程中更新 GUI
        try:
            self.text_widget.after(0, self._append, msg)
        except Exception:
            pass

    def _append(self, msg: str):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, msg)
            self.text_widget.see(tk.END)  # 自动滚动到底部
            self.text_widget.configure(state="disabled")
        except Exception:
            pass


class MainWindow:
    """主窗口类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("窗口文字监控自动回复工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 核心组件
        self.config_manager = ConfigManager()
        self.window_manager = WindowManager()
        self.ocr_engine = OCREngine()
        self.keyword_matcher = KeywordMatcher(
            cooldown=self.config_manager.get_cooldown()
        )
        self.auto_sender = AutoSender(
            send_delay=self.config_manager.get_send_delay()
        )

        # 监控状态
        self._monitoring = False
        self._monitor_thread = None
        self._selected_window = tk.StringVar()

        # 构建界面
        self._build_ui()

        # 配置日志
        setup_logging()
        gui_handler = GUILogHandler(self.log_text)
        logging.getLogger().addHandler(gui_handler)

        self.logger = logging.getLogger(__name__)
        self.logger.info("程序启动，界面初始化完成")

        # 加载规则列表
        self._refresh_rules_table()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─────────────────────────── UI 构建 ───────────────────────────

    def _build_ui(self):
        """构建完整的用户界面"""
        # 使用 PanedWindow 实现上下可调节布局
        main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 上半部分：控制区
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=2)

        # 下半部分：日志区
        bottom_frame = ttk.LabelFrame(main_pane, text="📋 运行日志")
        main_pane.add(bottom_frame, weight=1)

        # 构建上半部分的各区域
        self._build_window_selector(top_frame)
        self._build_settings(top_frame)
        self._build_rules_area(top_frame)
        self._build_control_area(top_frame)

        # 构建日志区
        self._build_log_area(bottom_frame)

    def _build_window_selector(self, parent):
        """构建窗口选择区"""
        frame = ttk.LabelFrame(parent, text="🖥️ 目标窗口选择")
        frame.pack(fill=tk.X, padx=4, pady=4)

        inner = ttk.Frame(frame)
        inner.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(inner, text="监控窗口：").pack(side=tk.LEFT)

        self.window_combo = ttk.Combobox(
            inner,
            textvariable=self._selected_window,
            state="readonly",
            width=50
        )
        self.window_combo.pack(side=tk.LEFT, padx=6)

        ttk.Button(
            inner, text="🔄 刷新窗口列表",
            command=self._refresh_windows
        ).pack(side=tk.LEFT, padx=4)

        # 初始刷新
        self._refresh_windows()

    def _build_settings(self, parent):
        """构建参数设置区"""
        frame = ttk.LabelFrame(parent, text="⚙️ 参数设置")
        frame.pack(fill=tk.X, padx=4, pady=4)

        inner = ttk.Frame(frame)
        inner.pack(fill=tk.X, padx=8, pady=6)

        # 监控间隔
        ttk.Label(inner, text="监控间隔（秒）：").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.interval_var = tk.StringVar(
            value=str(self.config_manager.get_scan_interval())
        )
        ttk.Entry(inner, textvariable=self.interval_var, width=8).grid(
            row=0, column=1, sticky=tk.W, padx=4
        )

        # 冷却时间
        ttk.Label(inner, text="冷却时间（秒）：").grid(row=0, column=2, sticky=tk.W, padx=12)
        self.cooldown_var = tk.StringVar(
            value=str(self.config_manager.get_cooldown())
        )
        ttk.Entry(inner, textvariable=self.cooldown_var, width=8).grid(
            row=0, column=3, sticky=tk.W, padx=4
        )

        # 发送延迟
        ttk.Label(inner, text="发送延迟（秒）：").grid(row=0, column=4, sticky=tk.W, padx=12)
        self.delay_var = tk.StringVar(
            value=str(self.config_manager.get_send_delay())
        )
        ttk.Entry(inner, textvariable=self.delay_var, width=8).grid(
            row=0, column=5, sticky=tk.W, padx=4
        )

        ttk.Button(
            inner, text="保存设置",
            command=self._save_settings
        ).grid(row=0, column=6, padx=12)

    def _build_rules_area(self, parent):
        """构建规则管理区"""
        frame = ttk.LabelFrame(parent, text="📝 关键字-回复规则")
        frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 表格
        columns = ("keyword", "reply", "enabled")
        self.rules_tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=6
        )
        self.rules_tree.heading("keyword", text="关键字")
        self.rules_tree.heading("reply", text="回复内容")
        self.rules_tree.heading("enabled", text="启用")
        self.rules_tree.column("keyword", width=120, anchor=tk.CENTER)
        self.rules_tree.column("reply", width=400)
        self.rules_tree.column("enabled", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar.set)
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=6)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=6)

        # 按钮区
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)

        ttk.Button(btn_frame, text="➕ 添加规则", command=self._add_rule, width=14).pack(pady=3)
        ttk.Button(btn_frame, text="✏️ 编辑规则", command=self._edit_rule, width=14).pack(pady=3)
        ttk.Button(btn_frame, text="🔄 切换启用", command=self._toggle_rule, width=14).pack(pady=3)
        ttk.Button(btn_frame, text="🗑️ 删除规则", command=self._delete_rule, width=14).pack(pady=3)

    def _build_control_area(self, parent):
        """构建控制区（开始/停止监控按钮和状态指示）"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=4, pady=4)

        self.start_btn = ttk.Button(
            frame, text="▶ 开始监控",
            command=self._start_monitoring,
            width=16
        )
        self.start_btn.pack(side=tk.LEFT, padx=8)

        self.stop_btn = ttk.Button(
            frame, text="⏹ 停止监控",
            command=self._stop_monitoring,
            state=tk.DISABLED,
            width=16
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        ttk.Label(frame, text="状态：").pack(side=tk.LEFT, padx=(20, 4))
        self.status_label = ttk.Label(
            frame, text="● 未运行",
            foreground="gray"
        )
        self.status_label.pack(side=tk.LEFT)

    def _build_log_area(self, parent):
        """构建日志显示区"""
        self.log_text = tk.Text(
            parent,
            height=10,
            state="disabled",
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        log_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=6)
        log_scroll.pack(side=tk.LEFT, fill=tk.Y, pady=6)

        ttk.Button(
            parent, text="清空日志",
            command=self._clear_log,
            width=10
        ).pack(side=tk.LEFT, padx=4, pady=6, anchor=tk.N)

    # ─────────────────────────── 窗口管理 ───────────────────────────

    def _refresh_windows(self):
        """刷新窗口列表"""
        titles = self.window_manager.get_all_windows()
        self.window_combo["values"] = titles
        if titles and not self._selected_window.get():
            self._selected_window.set(titles[0])
        logging.getLogger(__name__).info(f"已刷新窗口列表，共 {len(titles)} 个窗口")

    # ─────────────────────────── 规则管理 ───────────────────────────

    def _refresh_rules_table(self):
        """刷新规则表格显示"""
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        for rule in self.config_manager.get_rules():
            enabled_text = "✓" if rule.get("enabled", True) else "✗"
            self.rules_tree.insert(
                "", tk.END,
                values=(rule.get("keyword", ""), rule.get("reply", ""), enabled_text)
            )

    def _add_rule(self):
        """弹出对话框添加新规则"""
        dialog = RuleDialog(self.root, title="添加规则")
        if dialog.result:
            keyword, reply, enabled = dialog.result
            if keyword:
                self.config_manager.add_rule(keyword, reply, enabled)
                self._refresh_rules_table()
                logging.getLogger(__name__).info(f"已添加规则：关键字='{keyword}'")

    def _edit_rule(self):
        """编辑选中的规则"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要编辑的规则")
            return

        index = self.rules_tree.index(selected[0])
        rules = self.config_manager.get_rules()
        if index >= len(rules):
            return

        rule = rules[index]
        dialog = RuleDialog(
            self.root, title="编辑规则",
            keyword=rule.get("keyword", ""),
            reply=rule.get("reply", ""),
            enabled=rule.get("enabled", True)
        )
        if dialog.result:
            keyword, reply, enabled = dialog.result
            if keyword:
                self.config_manager.update_rule(index, keyword, reply, enabled)
                self._refresh_rules_table()
                logging.getLogger(__name__).info(f"已更新规则：关键字='{keyword}'")

    def _toggle_rule(self):
        """切换选中规则的启用/禁用状态"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要切换的规则")
            return

        index = self.rules_tree.index(selected[0])
        rules = self.config_manager.get_rules()
        if index >= len(rules):
            return

        rule = rules[index]
        new_enabled = not rule.get("enabled", True)
        self.config_manager.update_rule(
            index, rule["keyword"], rule["reply"], new_enabled
        )
        self._refresh_rules_table()
        state_text = "启用" if new_enabled else "禁用"
        logging.getLogger(__name__).info(
            f"规则 '{rule['keyword']}' 已{state_text}"
        )

    def _delete_rule(self):
        """删除选中的规则"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的规则")
            return

        index = self.rules_tree.index(selected[0])
        rules = self.config_manager.get_rules()
        if index >= len(rules):
            return

        keyword = rules[index].get("keyword", "")
        if messagebox.askyesno("确认删除", f"确认删除关键字 '{keyword}' 的规则？"):
            self.config_manager.remove_rule(index)
            self._refresh_rules_table()
            logging.getLogger(__name__).info(f"已删除规则：关键字='{keyword}'")

    # ─────────────────────────── 设置管理 ───────────────────────────

    def _save_settings(self):
        """保存参数设置"""
        try:
            interval = float(self.interval_var.get())
            cooldown = float(self.cooldown_var.get())
            delay = float(self.delay_var.get())

            if interval <= 0 or cooldown <= 0 or delay < 0:
                raise ValueError("参数值必须为正数")

            self.config_manager.set_scan_interval(interval)
            self.config_manager.set_cooldown(cooldown)
            self.config_manager.set_send_delay(delay)

            # 同步更新运行时组件
            self.keyword_matcher.set_cooldown(cooldown)
            self.auto_sender.set_send_delay(delay)

            logging.getLogger(__name__).info(
                f"设置已保存：间隔={interval}s，冷却={cooldown}s，延迟={delay}s"
            )
            messagebox.showinfo("成功", "参数设置已保存")
        except ValueError as e:
            messagebox.showerror("输入错误", f"参数格式错误：{e}\n请输入有效的数字")

    # ─────────────────────────── 监控控制 ───────────────────────────

    def _start_monitoring(self):
        """开始监控"""
        window_title = self._selected_window.get()
        if not window_title:
            messagebox.showwarning("警告", "请先选择要监控的目标窗口")
            return

        if not self.config_manager.get_enabled_rules():
            messagebox.showwarning("警告", "没有启用的规则，请至少添加一条关键字-回复规则")
            return

        if not self.ocr_engine.is_available():
            if not messagebox.askyesno(
                "Tesseract 未安装",
                "未检测到 Tesseract OCR，无法进行文字识别。\n"
                "是否仍要继续？（将无法识别窗口文字）\n\n"
                "下载地址：https://github.com/UB-Mannheim/tesseract/wiki"
            ):
                return

        self._monitoring = True
        self.keyword_matcher.reset()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status_label.configure(text="● 监控中", foreground="green")

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(window_title,),
            daemon=True
        )
        self._monitor_thread.start()
        logging.getLogger(__name__).info(f"开始监控窗口：{window_title}")

    def _stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="● 已停止", foreground="red")
        logging.getLogger(__name__).info("监控已停止")

    def _monitor_loop(self, window_title: str):
        """
        监控主循环，在独立线程中运行。
        定时截图 → OCR 识别 → 关键字匹配 → 自动回复
        """
        logger = logging.getLogger(__name__)

        while self._monitoring:
            try:
                interval = self.config_manager.get_scan_interval()
                rules = self.config_manager.get_enabled_rules()

                # 对目标窗口截图
                screenshot = self.window_manager.capture_window(window_title)
                if screenshot is None:
                    logger.warning(f"无法截图窗口：{window_title}，将在 {interval}s 后重试")
                    time.sleep(interval)
                    continue

                # OCR 识别文字
                text = self.ocr_engine.extract_text(screenshot)
                if text:
                    logger.debug(f"OCR 识别文字（{len(text)} 字符）")

                    # 匹配关键字
                    matched_rule = self.keyword_matcher.match(text, rules)
                    if matched_rule:
                        keyword = matched_rule["keyword"]
                        reply = matched_rule["reply"]
                        logger.info(f"触发关键字：'{keyword}'，准备回复：'{reply[:30]}'")

                        # 标记已触发（更新冷却计时器）
                        self.keyword_matcher.mark_triggered(keyword)

                        # 激活目标窗口并发送回复
                        self.window_manager.activate_window(window_title)
                        time.sleep(WINDOW_ACTIVATE_DELAY)  # 等待窗口激活完成
                        success = self.auto_sender.send_message(reply)
                        if success:
                            logger.info(f"回复已发送：'{reply[:50]}'")
                        else:
                            logger.error("回复发送失败")

            except Exception as e:
                logger.error(f"监控循环异常：{e}")

            # 等待下一次扫描
            if self._monitoring:
                time.sleep(interval)

        logger.info("监控线程已退出")

    # ─────────────────────────── 日志操作 ───────────────────────────

    def _clear_log(self):
        """清空日志显示区"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    # ─────────────────────────── 关闭处理 ───────────────────────────

    def _on_close(self):
        """程序关闭时的处理"""
        if self._monitoring:
            self._stop_monitoring()
        self.root.destroy()

    def run(self):
        """启动主事件循环"""
        self.root.mainloop()


class RuleDialog(tk.Toplevel):
    """添加/编辑规则的弹出对话框"""

    def __init__(self, parent, title="规则", keyword="", reply="", enabled=True):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()  # 模态对话框

        self.result = None

        # 构建表单
        frame = ttk.Frame(self)
        frame.pack(padx=20, pady=12, fill=tk.BOTH)

        ttk.Label(frame, text="关键字：").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.keyword_entry = ttk.Entry(frame, width=30)
        self.keyword_entry.grid(row=0, column=1, padx=8, pady=4)
        self.keyword_entry.insert(0, keyword)

        ttk.Label(frame, text="回复内容：").grid(row=1, column=0, sticky=tk.NW, pady=4)
        self.reply_text = tk.Text(frame, width=40, height=4)
        self.reply_text.grid(row=1, column=1, padx=8, pady=4)
        self.reply_text.insert("1.0", reply)

        self.enabled_var = tk.BooleanVar(value=enabled)
        ttk.Checkbutton(
            frame, text="启用此规则",
            variable=self.enabled_var
        ).grid(row=2, column=1, sticky=tk.W, padx=8, pady=4)

        # 按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="确定", command=self._ok, width=10).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.LEFT, padx=8)

        # 自动聚焦关键字输入框
        self.keyword_entry.focus_set()
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

        # 等待对话框关闭
        self.wait_window()

    def _ok(self):
        keyword = self.keyword_entry.get().strip()
        reply = self.reply_text.get("1.0", tk.END).strip()
        enabled = self.enabled_var.get()

        if not keyword:
            messagebox.showwarning("提示", "关键字不能为空", parent=self)
            return
        if not reply:
            messagebox.showwarning("提示", "回复内容不能为空", parent=self)
            return

        self.result = (keyword, reply, enabled)
        self.destroy()
