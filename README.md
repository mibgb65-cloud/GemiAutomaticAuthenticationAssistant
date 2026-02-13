------

# 🤖 Google Automation Pro (GemiAssistant)

**Google Automation Pro** 是一款功能强大的桌面自动化工具，专为批量管理 Google 账号设计。它集成了现代化的图形界面 (GUI)，支持自动化登录、2FA (TOTP) 验证、订阅状态检测以及自动填写支付表单。

内置 **反指纹浏览器技术**，能够模拟真实用户环境（Canvas/WebGL 噪音、随机 UA、屏幕分辨率），有效降低被风控的风险。

------

## ✨ 核心功能

- **🖥️ 现代化 GUI 界面**：基于 CustomTkinter 构建的深色模式界面，操作直观，支持实时日志查看。
- **🔐 智能登录验证**：自动处理账号登录，集成 `PyOTP` 自动计算并输入 2FA 验证码。
- **🎭 深度指纹混淆**：
  - 动态注入 JS 混淆 Canvas、WebGL 和 AudioContext 指纹。
  - 随机化 User-Agent (Windows/macOS) 和硬件并发数。
- **💳 自动化订阅支付**：
  - 对接卡密 API，自动提取 Token。
  - 全自动填写信用卡信息（卡号、CVV、有效期、账单地址）。
  - 自动识别并提取 SheerID 验证链接。
- **🌐 代理支持**：支持 HTTP/Socks5 代理配置，实现单窗口单 IP。
- **📂 数据自动归档**：成功链接、异常账号、废弃卡密自动分类导出。

------

## 🛠️ 环境依赖

- **操作系统**: Windows 10/11 或 macOS
- **Python**: 3.10 或更高版本
- **浏览器**: Google Chrome (需安装最新版)

------

## 🚀 快速开始

### 1. 安装依赖

在项目根目录下打开终端 (CMD / PowerShell / Terminal)，运行以下命令安装所需库：

Bash

```
pip install -r requirements.txt
```

> **注意**: 如果没有 `requirements.txt`，请手动安装核心库：
>
> ```
> pip install customtkinter undetected-chromedriver selenium requests pandas openpyxl pyotp python-dateutil setuptools
> ```

### 2. 启动程序

运行以下命令启动图形化控制台：

Bash

```
python gui.py
```

------

## ⚙️ 配置说明 (Data Configuration)

启动 GUI 后，切换到 **"数据配置 (Data)"** 标签页，您可以直接在界面上编辑或导入以下文件：

### 1. 账号列表 (`accounts.txt`)

格式严格遵循：`邮箱----密码----辅助邮箱----2FA密钥` (使用 4 个短横线分隔)

Plaintext

```
test01@gmail.com----password123----recovery@email.com----JBSWY3DPEHPK3PXP
test02@gmail.com----password456----recovery@email.com----NB2HI4DTHIXS6LAM
```

### 2. 代理设置 (`proxies.txt`)

强烈建议配置代理以防止 IP 关联。格式支持：

- `ip:port`
- `user:pass@ip:port` (无密码代理更稳定)

Plaintext

```
192.168.1.100:8080
user123:pass456@10.0.0.1:7890
```

### 3. 卡密令牌 (`card_token.txt`)

在此处粘贴您购买的 API 卡密 Token，**每行一个**。

脚本每次成功使用后，会自动删除第一行。

### 4. 姓名与邮编 (`name.txt` / `zip_code.txt`)

- **name.txt**: 随机英文姓名，每行一个（如 `John Doe`）。
- **zip_code.txt**: 美国 5 位邮编，每行一个（如 `10001`）。

------

## 📂 输出结果 (Output)

程序运行结束后，结果会自动保存在 `output/` 文件夹中，您也可以在 GUI 的 **"结果导出 (Result)"** 标签页直接查看：

- **`links.txt`**: 提取到的验证链接 (SheerID Verifcation Links)。
- **`manu_process.txt`**: 运行中报错或需人工介入的账号记录。
- **`used_card.txt`**: 已使用、过期或无效的卡密流水记录。
- **`input/input.xlsx`**: 程序运行时的中间状态表格 (Excel 格式)。

------

## 📁 项目结构

Plaintext

```
Google-Automation-Pro/
├── gui.py                  # [入口] 图形用户界面程序
├── main.py                 # [核心] 业务逻辑主程序
├── requirements.txt        # 依赖列表
├── input/                  # 输入数据文件夹 (自动生成)
│   ├── accounts.txt
│   ├── proxies.txt
│   └── ...
├── output/                 # 输出结果文件夹 (自动生成)
│   ├── links.txt
│   └── ...
└── services/               # 核心服务模块
    ├── browser_service.py      # 浏览器驱动管理
    ├── browser_actions.py      # 页面操作逻辑 (登录/支付)
    ├── browser_fingerprints.py # 指纹数据池
    ├── file_service.py         # 文件读写服务
    └── api_service.py          # API 接口服务
```

------

## ❓ 常见问题 (FAQ)

**Q: 启动时报错 `ModuleNotFoundError: No module named 'distutils'`?**

A: 这是 Python 3.12+ 的常见问题。请运行 `pip install setuptools` 即可修复。

**Q: 浏览器启动后立即关闭或报错 `Chrome version mismatch`?**

A: `undetected-chromedriver` 通常会自动匹配版本。如果报错，请尝试更新您本地的 Google Chrome 浏览器到最新版，或者删除 `browser_service.py` 中 `version_main=144` 的参数让其自动检测。

**Q: 为什么显示的 IP 不是我设置的代理 IP?**

A: 请检查 `proxies.txt` 格式是否正确。如果代理带账号密码，Chrome 启动参数有时不支持直接注入，建议使用 IP 白名单模式的代理。

------

## ⚠️ 免责声明

本项目仅供**技术研究和教育目的**使用。

使用者应自行承担因使用本项目而产生的任何法律责任或后果。请勿将本项目用于任何非法用途或违反服务条款的行为。