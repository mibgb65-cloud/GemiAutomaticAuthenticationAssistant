# main.py
import time
import datetime
import random
import sys

# 尝试导入 dateutil 用于解析 ISO 时间，如果没有安装则使用简单的字符串处理
try:
    from dateutil import parser

    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

from services.file_service import FileService
from services.browser_service import BrowserService
from services.api_service import ApiService


def is_token_expired(expire_str):
    """
    判断卡片是否过期
    expire_str 示例: "2026-02-13T10:07:54.457602+00:00"
    """
    if not expire_str:
        return True  # 没时间字段视为无效，安全起见算过期

    try:
        # 获取当前 UTC 时间
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        # 解析过期时间
        if HAS_DATEUTIL:
            expire_time = parser.parse(expire_str)
        else:
            # 兼容性写法 (Python 3.7+ fromisoformat 处理部分格式)
            # 简单处理：去掉微秒和时区，粗略对比 (不推荐，但作为 fallback)
            clean_str = expire_str.split('.')[0]  # 去掉微秒
            expire_time = datetime.datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
            # 强制加上 UTC 时区以便对比
            expire_time = expire_time.replace(tzinfo=datetime.timezone.utc)

        # 如果 当前时间 > 过期时间，则过期
        return now_utc > expire_time

    except Exception as e:
        print(f"   ⚠️ 时间解析错误 ({expire_str}): {e}")
        # 解析失败时，为防止使用废卡，建议视为过期
        return True


def main():
    # 1. 初始化服务
    file_service = FileService()
    browser_service = BrowserService()
    api_service = ApiService()

    # 2. 数据准备
    file_service.init_excel_from_txt()

    # 加载代理列表
    proxies = file_service.load_proxies()
    if proxies:
        print(f"🌐 加载了 {len(proxies)} 个代理 IP")
    else:
        print("⚠️ 未找到 proxies.txt 或文件为空，将直连访问")

    # 3. 读取任务
    accounts = file_service.load_accounts()
    if not accounts:
        print("没有可处理的账号 (Excel为空)。")
        return

    print(f"🚀 开始处理 {len(accounts)} 个账号...")

    for i, account in enumerate(accounts):
        # 跳过逻辑：已完成且状态明确的跳过
        if account.is_completed() and "已认证" not in account.status:
            print(f"⏩ [{i + 1}/{len(accounts)}] 跳过: {account.email}")
            continue

        if not account.email: continue

        print(f"\n▶️ [{i + 1}/{len(accounts)}] 处理: {account.email}")

        # 随机分配一个代理
        current_proxy = random.choice(proxies) if proxies else None

        try:
            # === A. 启动浏览器 & 登录 ===
            browser_service.start_driver(proxy=current_proxy)
            browser_service.login(account)

            # === B. 检测状态 ===
            status, link = browser_service.check_subscription()

            # 更新对象状态
            account.status = status
            account.verify_link = link
            print(f"   当前检测状态: {status}")

            # === C. 绑卡流程 (包含取卡逻辑) ===
            # 触发条件：状态是"已认证" (可以直接绑) 或者 "未订阅"且没链接 (可能是还没点击获取Offer)
            if "已认证" in status or ("未订阅" in status and not link):
                # 这里主要针对 "已认证" (Get student offer 按钮存在) 的情况
                if "已认证" in status:
                    print("   🔔 触发绑卡流程...")

                    card_data = None
                    token_key = None
                    valid_card_found = False

                    # --- [循环取卡直到成功或无卡] ---
                    while True:
                        # 1. 从文件取一个 Token (并从源文件删除)
                        token_key = file_service.get_next_card_token()

                        if not token_key:
                            print("   ❌ input/card_token.txt 已空，无法继续！")
                            break

                        print(f"   🔍 尝试 Token: {token_key[:10]}...")

                        # 2. 调用 API 查询/激活
                        success, api_resp = api_service.redeem_card(token_key)

                        if success:
                            # 3. 校验是否过期
                            expire_time = api_resp.get("expire_time")

                            if is_token_expired(expire_time):
                                print(f"   ⚠️ 卡片已过期 ({expire_time})，丢弃...")
                                file_service.save_used_token(token_key, f"过期: {expire_time}")
                                continue  # 取下一个

                            # 4. 有效卡片
                            print("   ✅ 卡片有效，准备使用")
                            card_data = api_resp
                            valid_card_found = True
                            break  # 跳出取卡循环
                        else:
                            print(f"   ⚠️ API请求失败或Key无效")
                            file_service.save_used_token(token_key, f"API报错: {api_resp}")
                            continue  # 取下一个

                    # --- [执行填表] ---
                    if valid_card_found and card_data:
                        # 记录这次使用的账号到 JSON
                        card_data['account_email'] = account.email
                        card_data['redeem_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        file_service.save_card_json(card_data)

                        # 获取姓名 (随机)
                        rnd_name = file_service.get_random_line("name.txt")
                        if not rnd_name: rnd_name = "John Doe"

                        # 获取邮编 (优先使用卡里的 legal_address)
                        zip_code = "10001"
                        if "legal_address" in card_data and isinstance(card_data["legal_address"], dict):
                            zip_code = card_data["legal_address"].get("postal_code", "10001")
                        else:
                            # 兜底：随机邮编
                            rnd_zip = file_service.get_random_line("zip_code.txt")
                            if rnd_zip: zip_code = rnd_zip

                        print(f"   💳 使用卡片: {card_data.get('pan')[-4:]} | Zip: {zip_code}")

                        # 执行浏览器操作 (获取返回结果)
                        is_success, msg = browser_service.fill_payment_info(card_data, rnd_name, zip_code)

                        if is_success:
                            # 成功：标记 Token 为正常使用
                            file_service.save_used_token(token_key, f"已使用: {account.email}")
                            account.status = "已自动绑卡"
                        else:
                            # 失败：记录到人工处理文件
                            print(f"   ⚠️ 订阅流程失败，已记录到 manu_process.txt")
                            file_service.save_manu_process(account.email, f"订阅失败: {msg}")

                            # 标记 Token 为尝试过但失败 (方便后续排查，也可以视为已废弃)
                            file_service.save_used_token(token_key, f"尝试失败: {account.email} | {msg}")
                            account.status = f"需人工: {msg}"

                    else:
                        print("   ⚠️ 未能获取有效卡片，跳过绑卡步骤")
                        account.status = "缺卡/无有效卡"

            # === D. 保存结果 ===
            account.query_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_service.save_results(accounts)
            file_service.append_link_to_txt(account.verify_link)

        except Exception as e:
            error_msg = str(e)[:150]  # 截断错误信息防止太长
            print(f"   ❌ 主流程异常: {error_msg}")
            account.status = f"报错: {error_msg}"
            file_service.save_results(accounts)

        finally:
            # 无论成功失败，关闭浏览器清理内存
            browser_service.close_driver()

        # 随机等待，模拟真人操作间隔
        sleep_t = random.uniform(3, 8)
        print(f"💤 等待 {sleep_t:.1f}s...")
        time.sleep(sleep_t)

    print("\n🎉 所有任务处理完成！")


if __name__ == "__main__":
    main()