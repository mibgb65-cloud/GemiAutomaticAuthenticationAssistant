# services/file_service.py
import os
import glob
import json
import random
import pandas as pd
from entity import GoogleAccount


class FileService:
    def __init__(self, input_dir="input", output_dir="output"):
        self.input_dir = input_dir
        self.output_dir = output_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.excel_path = os.path.join(input_dir, "input.xlsx")
        self.txt_output_path = os.path.join(output_dir, "links.txt")
        self.card_json_path = os.path.join(output_dir, "card.json")
        self.token_path = os.path.join(input_dir, "card_token.txt")
        self.used_token_path = os.path.join(output_dir, "used_card.txt")
        self.manu_process_path = os.path.join(output_dir, "manu_process.txt")

    def get_random_line(self, filename):
        """从 input 文件夹读取指定 txt 的随机一行"""
        path = os.path.join(self.input_dir, filename)
        if not os.path.exists(path):
            print(f"⚠️ 文件不存在: {path}")
            return ""

        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            if lines:
                return random.choice(lines)
            return ""
        except Exception as e:
            print(f"❌ 读取 {filename} 失败: {e}")
            return ""

    def save_card_json(self, card_data):
        """追加保存卡片信息到 JSON (JSON Lines 格式)"""
        try:
            # 采用追加模式，每行一个 JSON 对象，方便读取且不会破坏文件结构
            with open(self.card_json_path, "a", encoding="utf-8") as f:
                json.dump(card_data, f, ensure_ascii=False)
                f.write("\n")  # 换行
            print(f"   💾 卡片信息已保存到 card.json")
        except Exception as e:
            print(f"   ❌ 保存 card.json 失败: {e}")

    def init_excel_from_txt(self):
        """扫描 txt 并覆盖初始化 input.xlsx"""
        txt_files = glob.glob(os.path.join(self.input_dir, "*.txt"))
        if not txt_files:
            return

        print(f"📄 发现 TXT 文件，正在转换到 Excel...")
        all_data = []
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = [p.strip() for p in line.strip().split('----')]
                        if len(parts) >= 4:
                            all_data.append({
                                '账号': parts[0],
                                '密码': parts[1],
                                '辅助邮箱': parts[2],
                                '2fa': parts[3],
                                '当前状态': '', '验证链接': '', '查询时间': ''
                            })
            except Exception as e:
                print(f"❌ 读取 {txt_file} 失败: {e}")

        if all_data:
            df = pd.DataFrame(all_data)
            # 覆盖保存
            df.to_excel(self.excel_path, index=False)
            print(f"✅ 已初始化 {len(all_data)} 个账号到 {self.excel_path}")

    def load_accounts(self):
        """读取 Excel 并返回 Account 对象列表"""
        if not os.path.exists(self.excel_path):
            print("❌ Excel 文件不存在")
            return []

        try:
            df = pd.read_excel(self.excel_path, dtype=str)
            accounts = []
            for idx, row in df.iterrows():
                acc = GoogleAccount(
                    email=row.get('账号'),
                    password=row.get('密码'),
                    recovery_email=row.get('辅助邮箱'),
                    secret_key=row.get('2fa'),
                    status=row.get('当前状态'),
                    verify_link=row.get('验证链接'),
                    query_time=row.get('查询时间')
                )
                # 绑定行号方便回写（可选，或直接重写整个文件）
                acc.row_index = idx
                accounts.append(acc)
            return accounts
        except Exception as e:
            print(f"❌ 读取 Excel 失败: {e}")
            return []

    def save_results(self, accounts):
        """将最新的 Account 对象列表保存回 Excel"""
        data = [acc.to_dict() for acc in accounts]
        df = pd.DataFrame(data)
        try:
            df.to_excel(self.excel_path, index=False)
            print(f"💾 Excel 已保存")
        except PermissionError:
            print("❌ 保存失败：文件被占用！")

    def append_link_to_txt(self, link):
        """追加链接到 output txt"""
        if link and "http" in link and "无法提取" not in link:
            try:
                with open(self.txt_output_path, "a", encoding="utf-8") as f:
                    f.write(link + "\n")
                print(f"📝 链接已写入 TXT")
            except Exception as e:
                print(f"⚠️ TXT 写入失败: {e}")

    def get_next_card_token(self):
        """
        [新增] 读取 card_token.txt 的第一行并从文件中删除它
        返回: token字符串 或 None
        """
        if not os.path.exists(self.token_path):
            print(f"⚠️ 未找到卡密文件: {self.token_path}")
            return None

        lines = []
        try:
            with open(self.token_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 过滤空行
            lines = [line for line in lines if line.strip()]

            if not lines:
                return None

            # 取出第一行
            first_token = lines[0].strip()
            remaining_lines = lines[1:]

            # 写回文件（覆盖）
            with open(self.token_path, 'w', encoding='utf-8') as f:
                f.writelines(remaining_lines)

            return first_token

        except Exception as e:
            print(f"❌ 读取卡密文件失败: {e}")
            return None

    def save_used_token(self, token, reason="Expired"):
        """
        [新增] 将废弃或已使用的卡密追加到 used_card.txt
        """
        try:
            with open(self.used_token_path, "a", encoding="utf-8") as f:
                f.write(f"{token} | {reason}\n")
            # print(f"   🗑️ 卡密已移入回收站: {reason}")
        except Exception as e:
            print(f"❌ 写入 used_card 失败: {e}")

    def save_manu_process(self, email, reason):
        """
        [新增] 记录需要人工处理的账号
        """
        try:
            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.manu_process_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} | {email} | {reason}\n")
            print(f"   📝 已记录到 manual_process.txt")
        except Exception as e:
            print(f"❌ 写入 manual_process 失败: {e}")

    def load_proxies(self):
        """
        [新增] 加载 proxies.txt
        返回: list of strings (proxy strings)
        """
        proxy_path = os.path.join(self.input_dir, "proxies.txt")
        if not os.path.exists(proxy_path):
            # 如果文件不存在，返回空列表
            return []

        proxies = []
        try:
            with open(proxy_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 排除空行和注释
                    if line and not line.startswith("#"):
                        proxies.append(line)
            return proxies
        except Exception as e:
            print(f"❌ 读取 proxies.txt 失败: {e}")
            return []