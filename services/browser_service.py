# services/browser_service.py
import os
import random
import undetected_chromedriver as uc
from services.browser_fingerprints import FINGERPRINTS
# 导入拆分出去的逻辑模块
import services.browser_actions as actions

# 系统补丁
os.environ['DISTUTILS_USE_SDK'] = '1'


class BrowserService:
    def __init__(self):
        self.driver = None
        self.fingerprints = FINGERPRINTS

    def start_driver(self, proxy=None):
        """启动浏览器，加载指纹混淆配置"""
        # 1. 随机选择一套指纹配置
        fp = random.choice(self.fingerprints)
        current_ua = fp["ua"]
        current_platform = fp["platform"]

        # 2. Chrome 启动参数
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--user-agent={current_ua}")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            print(f"   🌐 使用代理启动: {proxy}")

        preferences = {
            "webrtc.ip_handling_policy": "default_public_interface_only",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False
        }
        options.add_experimental_option("prefs", preferences)

        # 3. 启动 UC Driver
        self.driver = uc.Chrome(version_main=144, use_subprocess=True, options=options)

        # 4. 注入 JS 脚本混淆深层指纹
        self._inject_fingerprint_scripts(current_platform)

        # 5. 调整窗口
        width = random.randint(1050, 1400)
        height = random.randint(800, 1000)
        self.driver.set_window_size(width, height)
        self.driver.set_window_position(random.randint(0, 100), random.randint(0, 50))
        print(f"   🎭 指纹已伪装: {current_platform} | 窗口: {width}x{height}")

    def _inject_fingerprint_scripts(self, platform):
        """注入 JS 混淆"""
        cpu_cores = random.choice([4, 8, 12, 16])
        memory = random.choice([4, 8, 16, 32])
        cmd = """
        (() => {
            Object.defineProperty(navigator, 'platform', {get: () => '%s'});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => %d});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => %d});
            // ... (省略部分Canvas噪音代码，保持原有逻辑即可，此处简化展示) ...
            const toBlob = HTMLCanvasElement.prototype.toBlob;
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            const getImageData = CanvasRenderingContext2D.prototype.getImageData;
            const noise = {r: 1, g: 1, b: 1}; // 简化
            // ...
        })();
        """ % (platform, cpu_cores, memory)

        # 实际代码中请保留完整的 Canvas 噪音逻辑
        # 这里为了演示引用，使用完整的逻辑请直接复制原文件该函数内容即可
        # 关键是这个函数属于 Driver 层面的配置，所以留在 Service 里没问题

        # 如果你想极致精简，也可以把这个 JS 字符串放到 fingerprints.py 里
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": cmd})

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    # --- 代理方法：供 main.py 调用，实际执行逻辑在 actions.py ---

    def login(self, account):
        if not self.driver: self.start_driver()
        return actions.perform_login(self.driver, account)

    def check_subscription(self, retry_count=0):
        return actions.check_subscription_status(self.driver, retry_count)

    def fill_payment_info(self, card_info, name, zip_code):
        return actions.fill_payment_form(self.driver, card_info, name, zip_code)