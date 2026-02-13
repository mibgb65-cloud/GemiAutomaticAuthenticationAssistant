# services/browser_actions.py
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# --- 辅助小工具 ---

def random_sleep(min_t=3, max_t=8):
    """页面跳转或大步骤间的长等待"""
    t = random.uniform(min_t, max_t)
    time.sleep(t)

def type_slowly(element, text):
    """模拟真人打字"""
    try:
        element.click()
    except:
        pass
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))

# --- 核心业务逻辑函数 ---

def perform_login(driver, account):
    """执行登录流程"""
    print(f"   正在登录: {account.email}")
    driver.get("https://accounts.google.com/signin")

    # 1. 输入账号
    try:
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        type_slowly(email_input, account.email)
        random_sleep(1, 2)
        driver.find_element(By.ID, "identifierNext").click()
    except Exception as e:
        print(f"   ⚠️ 账号输入步骤异常: {e}")
        return

    # 2. 输入密码
    try:
        pwd_input = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.NAME, "Passwd"))
        )
        random_sleep(2, 4)
        type_slowly(pwd_input, account.password)
        random_sleep(1, 2)
        driver.find_element(By.ID, "passwordNext").click()
    except Exception as e:
        print(f"   ⚠️ 密码输入步骤异常: {e}")
        return

    # 3. 处理 2FA
    try:
        totp_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel'], input[id='totpPin']"))
        )
        print("   🔒 检测到 2FA 验证...")
        code = account.get_totp_code()
        if code:
            print(f"   输入 2FA: {code}")
            random_sleep(2, 4)
            type_slowly(totp_input, code)
            time.sleep(1)
            totp_input.send_keys(Keys.ENTER)
            time.sleep(5)
        else:
            print("   ⚠️ 需要 2FA 但无法获取密钥")
    except:
        pass

    # 4. 确认结果
    time.sleep(5)
    current_url = driver.current_url
    if "myaccount.google.com" in current_url or "google.com" in current_url:
        print("   ✅ 登录成功")
    else:
        print(f"   ℹ️ 登录后页面: {current_url[:50]}...")


def check_subscription_status(driver, retry_count=0):
    """跳转并检测订阅状态"""
    print(f"   正在检测订阅状态 (尝试次数: {retry_count + 1})...")

    if retry_count > 0:
        print("   🔄 链接无效，正在刷新页面重试...")
        driver.refresh()
    else:
        driver.get("https://one.google.com/ai-student")

    time.sleep(8)

    status = "未知状态"
    link = ""

    xpath_sub = "//*[contains(text(), \"You're already subscribed\")] | //a[@aria-label='Manage plan']"
    xpath_certified = "//*[contains(text(), 'Get student offer')]"
    xpath_verify = "//a[contains(@href, 'sheerid')] | //a[contains(@aria-label, 'Verify')] | //a[contains(@aria-label, '验证')] | //*[contains(text(), 'Verify')]"

    try:
        if driver.find_elements(By.XPATH, xpath_sub):
            return "已订阅", ""
    except:
        pass

    try:
        if driver.find_elements(By.XPATH, xpath_certified):
            return "已认证/未订阅", ""
    except:
        pass

    try:
        btns = driver.find_elements(By.XPATH, xpath_verify)
        if btns:
            status = "未订阅 (需验证)"
            found_link = ""
            for btn in btns:
                href = btn.get_attribute("href")
                if href and "http" in href:
                    found_link = href
                    break
            if not found_link:
                try:
                    found_link = btns[0].find_element(By.XPATH, "./..").get_attribute("href")
                except:
                    pass

            if found_link:
                if "services.sheerid.com/verify" in found_link and "verificationId=" in found_link:
                    val = found_link.split("verificationId=")[-1]
                    if not val.strip():
                        print(f"   ⚠️ 检测到无效跳转链接 (ID为空): {found_link[:60]}...")
                        if retry_count < 3:
                            return check_subscription_status(driver, retry_count + 1)
                        else:
                            link = "获取失败: 链接ID为空且重试无效"
                    else:
                        link = found_link
                else:
                    link = found_link
            else:
                link = "无法提取链接"
            return status, link
    except Exception as e:
        print(f"   ⚠️ 检测出错: {e}")
        pass

    return status, link


def fill_payment_form(driver, card_info, name, zip_code):
    """自动填写信用卡表单"""
    TAB_SLEEP = 1.5
    DOUBLE_TAB_SLEEP = 1.0
    TYPING_SPEED = 0.2
    print(f"   💳 开始处理支付页面...")

    try:
        # 1. Offer
        offer_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Get student offer')]")))
        offer_btn.click()
        time.sleep(5)

        # 2. Add Card
        print("   -> 寻找 'Add card'...")
        target_xpaths = ["//button[.//span[contains(text(), 'Add card')]]", "//span[contains(text(), 'Add card')]",
                         "//div[contains(text(), 'Add card')]"]
        add_btn = None
        for xp in target_xpaths:
            try:
                add_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xp)))
                if add_btn: break
            except:
                continue

        if not add_btn:
            # 尝试 Iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for f in iframes:
                driver.switch_to.frame(f)
                for xp in target_xpaths:
                    try:
                        add_btn = driver.find_element(By.XPATH, xp)
                        if add_btn: break
                    except:
                        pass
                if add_btn: break
                driver.switch_to.default_content()

        if add_btn:
            driver.execute_script("arguments[0].click();", add_btn)
            print("   -> 点击了 Add card")
        else:
            print("   ⚠️ 未找到 Add card (可能已直接显示表单)")

        time.sleep(8)

        # 3. 填表
        pan = str(card_info.get('pan', ''))
        cvv = str(card_info.get('cvv', ''))
        exp = f"{str(card_info.get('exp_month', '')).zfill(2)}/{str(card_info.get('exp_year', ''))[-2:]}"

        driver.switch_to.default_content()
        ac = ActionChains(driver)

        # 卡号
        for c in pan: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 日期 (Tab)
        ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in exp: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # CVV (这里简化假设)
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in cvv: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 姓名 (Tab)
        ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in name: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 邮编 (Tab*2)
        ActionChains(driver).send_keys(Keys.TAB).pause(DOUBLE_TAB_SLEEP).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ac = ActionChains(driver)
        for c in zip_code: ac.send_keys(c).pause(TYPING_SPEED)
        ac.perform()
        time.sleep(TAB_SLEEP)

        # 4. 保存
        print("   -> 保存卡片...")
        ActionChains(driver).send_keys(Keys.TAB).pause(0.5).send_keys(Keys.TAB).pause(0.5).send_keys(
            Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        print("   -> 等待保存跳转 (10s)...")
        time.sleep(10)

        # 5. 订阅
        print("   -> 点击订阅...")
        ActionChains(driver).send_keys(Keys.TAB).pause(0.5).send_keys(Keys.TAB).pause(0.5).send_keys(
            Keys.TAB).pause(0.5).send_keys(Keys.TAB).pause(0.5).send_keys(Keys.TAB).perform()
        time.sleep(TAB_SLEEP)
        ActionChains(driver).send_keys(Keys.ENTER).perform()

        print("   ⏳ 等待订阅处理 (15s)...")
        time.sleep(15)

        # 6. 最终检查 (递归调用同文件中的 check 函数)
        print("   🔄 最终校验...")
        final_status, _ = check_subscription_status(driver)
        if "已订阅" in final_status:
            print(f"   🎉 成功！")
            return True, "成功"
        else:
            return False, f"流程走完但状态为: {final_status}"

    except Exception as e:
        err = str(e)[:100]
        print(f"   ❌ 填表/订阅异常: {err}")
        return False, f"异常: {err}"