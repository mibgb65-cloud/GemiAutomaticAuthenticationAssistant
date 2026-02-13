# entity.py
import pyotp


class GoogleAccount:
    def __init__(self, email, password, recovery_email, secret_key,
                 status="", verify_link="", query_time=""):
        self.email = str(email).strip()
        self.password = str(password).strip()
        self.recovery_email = str(recovery_email).strip()
        self.secret_key = str(secret_key).replace(" ", "").strip().upper()

        # 运行结果状态
        self.status = str(status).strip() if str(status).lower() != 'nan' else ""
        self.verify_link = str(verify_link).strip() if str(verify_link).lower() != 'nan' else ""
        self.query_time = str(query_time).strip()

    def get_totp_code(self):
        """获取当前 2FA 验证码"""
        try:
            if not self.secret_key or len(self.secret_key) < 16:
                return None
            totp = pyotp.TOTP(self.secret_key)
            return totp.now()
        except:
            return None

    def is_completed(self):
        """判断该账号是否已经处理完成（跳过逻辑）"""
        if not self.status:
            return False
        if "报错" in self.status:
            return False

        # 情况 1: 已订阅 -> 跳过
        if "已订阅" in self.status:
            return True

        # 情况 2: 已认证/未订阅 -> 跳过 (根据你的需求，这算已完成)
        if "已认证" in self.status:
            return True

        # 情况 3: 未订阅 (需验证) -> 必须要有链接才算完成
        if "未订阅" in self.status:
            if self.verify_link and "http" in self.verify_link and "无法提取" not in self.verify_link:
                return True
            return False  # 缺链接，视为未完成

        return False

    def to_dict(self):
        """转为字典用于保存 Excel"""
        return {
            '账号': self.email,
            '密码': self.password,
            '辅助邮箱': self.recovery_email,
            '2fa': self.secret_key,
            '当前状态': self.status,
            '验证链接': self.verify_link,
            '查询时间': self.query_time
        }