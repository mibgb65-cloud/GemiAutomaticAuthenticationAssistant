import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import threading
import os
import shutil
import main  # 引入核心逻辑

# === 全局外观设置 ===
ctk.set_appearance_mode("Dark")  # 模式: System, Dark, Light
ctk.set_default_color_theme("blue")  # 主题色

# === 路径配置 ===
BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定义文件路径和提示文案
FILES_CONFIG = {
    "accounts": {
        "path": os.path.join(INPUT_DIR, "accounts.txt"),
        "title": "📋 账号列表 (Accounts)",
        "tip": "格式：邮箱----密码----辅助邮箱 (每行一条)\n示例：test@gmail.com----password123----rec@mail.com"
    },
    "card_token": {
        "path": os.path.join(INPUT_DIR, "card_token.txt"),
        "title": "🔑 卡密令牌 (Tokens)",
        "tip": "此处粘贴购买的卡密/Token，每行一个。\n脚本会自动读取第一行并删除。"
    },
    "name": {
        "path": os.path.join(INPUT_DIR, "name.txt"),
        "title": "👤 姓名库 (Names)",
        "tip": "随机使用的英文姓名，每行一个。\n如果不填则使用默认姓名。"
    },
    "zip_code": {
        "path": os.path.join(INPUT_DIR, "zip_code.txt"),
        "title": "📫 邮编库 (Zip Codes)",
        "tip": "美国邮编 (5位数字)，每行一个。\n用于填写支付账单地址。"
    },
    "proxies": {
        "path": os.path.join(INPUT_DIR, "proxies.txt"),
        "title": "🌐 代理IP (Proxies)",
        "tip": "格式：ip:port 或 user:pass@ip:port\n如果为空则直连，强烈建议配置代理。"
    },
    "links": {
        "path": os.path.join(OUTPUT_DIR, "links.txt"),
        "title": "🔗 提取结果 (Links)",
        "tip": "自动提取的验证链接会保存在这里。"
    },
    "manu_process": {
        "path": os.path.join(OUTPUT_DIR, "manu_process.txt"),
        "title": "⚠️ 人工处理 (Manual)",
        "tip": "遇到异常或流程失败的账号记录。"
    },
    "used_card": {
        "path": os.path.join(OUTPUT_DIR, "used_card.txt"),
        "title": "🗑️ 已用卡密 (Used)",
        "tip": "使用过或过期的卡密流水记录。"
    }
}

# 初始化空文件
for key, config in FILES_CONFIG.items():
    if not os.path.exists(config["path"]):
        with open(config["path"], "w", encoding="utf-8") as f: pass


class PrintRedirector:
    """重定向 print 到 GUI 的文本框"""

    def __init__(self, text_widget, status_label):
        self.text_widget = text_widget
        self.status_label = status_label

    def write(self, str_msg):
        try:
            # 更新日志框
            self.text_widget.configure(state='normal')
            self.text_widget.insert("end", str_msg)
            self.text_widget.see("end")
            self.text_widget.configure(state='disabled')

            # 更新底部状态栏 (只取非空的最后一行)
            clean_msg = str_msg.strip()
            if clean_msg:
                # 截取过长的信息
                display_msg = (clean_msg[:80] + '...') if len(clean_msg) > 80 else clean_msg
                self.status_label.configure(text=f"执行中: {display_msg}")
        except:
            pass

    def flush(self):
        pass


class FileCard(ctk.CTkFrame):
    """自定义组件：带标题、提示、按钮和文本框的卡片"""

    def __init__(self, master, file_key, is_input=True, **kwargs):
        super().__init__(master, corner_radius=10, fg_color=("#EBEBEB", "#2B2B2B"), **kwargs)

        self.config = FILES_CONFIG[file_key]
        self.file_path = self.config["path"]

        # --- 顶部栏 ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        # 标题
        title_lbl = ctk.CTkLabel(header, text=self.config["title"], font=("微软雅黑", 14, "bold"))
        title_lbl.pack(side="left")

        # 按钮组
        if is_input:
            ctk.CTkButton(header, text="保存", width=50, height=24, font=("Arial", 11),
                          fg_color="#10B981", hover_color="#059669",
                          command=self.save_file).pack(side="right", padx=5)
            ctk.CTkButton(header, text="导入", width=50, height=24, font=("Arial", 11),
                          fg_color="#3B8ED0", hover_color="#1D4ED8",
                          command=self.import_file).pack(side="right")
        else:
            ctk.CTkButton(header, text="导出", width=50, height=24, font=("Arial", 11),
                          fg_color="#F59E0B", hover_color="#D97706",
                          command=self.export_file).pack(side="right", padx=5)
            ctk.CTkButton(header, text="刷新", width=50, height=24, font=("Arial", 11),
                          fg_color="#6366F1", hover_color="#4338CA",
                          command=self.load_file).pack(side="right")

        # --- 提示文字 ---
        tip_lbl = ctk.CTkLabel(self, text=self.config["tip"], font=("Arial", 11),
                               text_color="gray", anchor="w", justify="left")
        tip_lbl.pack(fill="x", padx=10, pady=(0, 5))

        # --- 文本编辑区 ---
        self.textbox = ctk.CTkTextbox(self, font=("Consolas", 12), fg_color=("#FFFFFF", "#1E1E1E"), corner_radius=6)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.load_file()

    def load_file(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0", "end")
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.textbox.insert("0.0", f.read())
            except Exception as e:
                self.textbox.insert("0.0", f"❌ 读取错误: {e}")
        else:
            self.textbox.insert("0.0", "")

    def save_file(self):
        content = self.textbox.get("0.0", "end").strip()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.flash_success()
        except Exception as e:
            tk.messagebox.showerror("保存失败", str(e))

    def import_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.textbox.delete("0.0", "end")
                self.textbox.insert("0.0", content)
                self.save_file()
            except Exception as e:
                tk.messagebox.showerror("导入失败", str(e))

    def export_file(self):
        default_name = os.path.basename(self.file_path)
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name)
        if path:
            try:
                shutil.copy2(self.file_path, path)
                tk.messagebox.showinfo("成功", f"文件已导出至:\n{path}")
            except Exception as e:
                tk.messagebox.showerror("导出失败", str(e))

    def flash_success(self):
        # 简单的视觉反馈：边框变绿一下
        original_color = self._fg_color
        self.configure(fg_color="#064E3B")  # 深绿色
        self.after(200, lambda: self.configure(fg_color=original_color))


class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # === 窗口设置 ===
        self.title("Google Automation Pro v2.0")
        self.geometry("1200x800")

        # === 布局网格 ===
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === 左侧导航栏 ===
        self.setup_sidebar()

        # === 右侧内容区 (TabView) ===
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        # 创建标签页
        self.tab_console = self.tabview.add("console")
        self.tab_data = self.tabview.add("data")
        self.tab_result = self.tabview.add("result")

        # 隐藏 Tab 头部，用侧边栏控制
        self.tabview._segmented_button.grid_remove()

        # 初始化各页面内容
        self.setup_console_page()
        self.setup_data_page()
        self.setup_result_page()

        # 默认显示控制台
        self.select_frame("console")
        self.is_running = False
        self.original_stdout = sys.stdout

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        # Logo
        ctk.CTkLabel(self.sidebar, text="🤖 AUTO\nASSISTANT", font=("Montserrat", 22, "bold")).grid(row=0, column=0,
                                                                                                   padx=20,
                                                                                                   pady=(30, 20))

        # 导航按钮
        self.btn_console = self.create_nav_btn("📊 运行控制台", "console", 1)
        self.btn_data = self.create_nav_btn("⚙️ 数据配置", "data", 2)
        self.btn_result = self.create_nav_btn("📂 结果导出", "result", 3)

        # 主题切换
        ctk.CTkLabel(self.sidebar, text="Appearance Mode:", font=("Arial", 10), text_color="gray").grid(row=6, column=0,
                                                                                                        padx=20,
                                                                                                        pady=(10, 0),
                                                                                                        sticky="w")
        ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light", "System"], command=ctk.set_appearance_mode).grid(row=7,
                                                                                                                  column=0,
                                                                                                                  padx=20,
                                                                                                                  pady=(
                                                                                                                      5,
                                                                                                                      20))

    def create_nav_btn(self, text, frame_name, row):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, corner_radius=8,
                            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                            anchor="w", font=("微软雅黑", 13),
                            command=lambda: self.select_frame(frame_name))
        btn.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return btn

    def select_frame(self, name):
        self.tabview.set(name)
        # 高亮当前按钮
        for btn in [self.btn_console, self.btn_data, self.btn_result]:
            btn.configure(fg_color="transparent")

        if name == "console": self.btn_console.configure(fg_color=("gray75", "gray25"))
        if name == "data": self.btn_data.configure(fg_color=("gray75", "gray25"))
        if name == "result": self.btn_result.configure(fg_color=("gray75", "gray25"))

    # --- 1. 控制台页面 ---
    def setup_console_page(self):
        frame = self.tab_console
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # 顶部大按钮
        self.btn_start = ctk.CTkButton(frame, text="🚀 启动自动化任务", font=("微软雅黑", 16, "bold"),
                                       height=50, corner_radius=10,
                                       fg_color="#10B981", hover_color="#059669",
                                       command=self.start_thread)
        self.btn_start.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 10))

        # 日志区域
        log_frame = ctk.CTkFrame(frame, corner_radius=10, fg_color=("#EBEBEB", "#2B2B2B"))
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_frame, text="💻 系统日志 (System Log)", font=("微软雅黑", 12, "bold")).grid(row=0, column=0,
                                                                                                    sticky="w", padx=15,
                                                                                                    pady=10)

        self.console_box = ctk.CTkTextbox(log_frame, font=("Consolas", 12), activate_scrollbars=True,
                                          fg_color="transparent")
        self.console_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.console_box.configure(state="disabled")

        # 底部状态条
        self.status_bar = ctk.CTkLabel(frame, text="就绪", font=("Arial", 11), text_color="#A3A3A3", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=5)

        # 重定向
        sys.stdout = PrintRedirector(self.console_box, self.status_bar)
        sys.stderr = PrintRedirector(self.console_box, self.status_bar)

    # --- 2. 数据配置页面 ---
    def setup_data_page(self):
        frame = self.tab_data
        # 2x2 网格布局
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # 放置卡片
        FileCard(frame, "accounts").grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        FileCard(frame, "card_token").grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        FileCard(frame, "name").grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        FileCard(frame, "zip_code").grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        # 如果需要配置代理，可以把布局改成 3行，或者把 zip_code 和 name 合并
        # 这里演示把 proxies 加在最下面，跨两列
        frame.grid_rowconfigure(2, weight=1)
        FileCard(frame, "proxies").grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    # --- 3. 结果页面 ---
    def setup_result_page(self):
        frame = self.tab_result
        # 1行3列
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        FileCard(frame, "links", is_input=False).grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        FileCard(frame, "manu_process", is_input=False).grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        FileCard(frame, "used_card", is_input=False).grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

    # --- 逻辑 ---
    def start_thread(self):
        if self.is_running:
            return

        self.is_running = True
        self.btn_start.configure(text="⏳ 正在运行...", fg_color="#EF4444", state="disabled")
        self.status_bar.configure(text="正在初始化线程...")

        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        try:
            print("🚀 任务已启动...")
            main.main()
            print("✅ 任务完成")
            tk.messagebox.showinfo("完成", "所有任务执行完毕")
        except Exception as e:
            print(f"❌ 严重错误: {e}")
            tk.messagebox.showerror("运行错误", str(e))
        finally:
            self.is_running = False
            self.btn_start.configure(text="🚀 启动自动化任务", fg_color="#10B981", state="normal")
            self.status_bar.configure(text="就绪")

    def on_closing(self):
        sys.stdout = self.original_stdout
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = ModernApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()