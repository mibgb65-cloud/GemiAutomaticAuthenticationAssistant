# services/api_service.py
import requests
import json


class ApiService:
    def __init__(self):
        self.redeem_url = "https://actcard.xyz/api/keys/redeem"
        self.query_url = "https://actcard.xyz/api/keys/query"  # 新增查询接口
        self.headers = {
            "Content-Type": "application/json"
        }

    def _parse_card_data(self, data):
        """
        内部辅助函数：统一解析 API 返回的 JSON 数据
        """
        # 检查 success 字段和 card 字段
        if data.get("success") is True and "card" in data:
            card_data = data["card"]
            # 顺便把地址信息也合进去，以防万一
            if "legal_address" in data:
                card_data["legal_address"] = data["legal_address"]
            return True, card_data
        return False, None

    def redeem_card(self, key_id):
        """
        尝试激活卡密。如果激活失败（如已使用），自动尝试查询。
        """
        key_id = key_id.strip()
        payload = {"key_id": key_id}

        # === 第 1 步：尝试激活 (Redeem) ===
        print(f"   📡 [Redeem] 正在请求激活 (Key: {key_id})...")
        try:
            response = requests.post(self.redeem_url, headers=self.headers, json=payload, timeout=15)

            # 情况 A: 激活成功 (HTTP 200 且 success=True)
            if response.status_code == 200:
                data = response.json()
                success, card_data = self._parse_card_data(data)
                if success:
                    print("   ✅ 激活成功，获取到新卡信息")
                    return True, card_data

            # 如果没成功，打印一下原因
            print(f"   ⚠️ 激活未通过 (状态码: {response.status_code})")
            try:
                err_msg = response.json().get('error', response.text)
                print(f"      服务端提示: {err_msg}")
            except:
                pass

        except Exception as e:
            print(f"   ❌ 激活请求异常: {e}")
            # 注意：网络异常通常也不影响尝试查询，继续往下走

        # === 第 2 步：激活失败，自动降级为查询 (Query) ===
        print(f"   🔄 [Query] 尝试切换查询接口...")
        try:
            # query 接口参数也是 {"key_id": "..."}
            query_resp = requests.post(self.query_url, headers=self.headers, json=payload, timeout=15)

            if query_resp.status_code == 200:
                q_data = query_resp.json()
                success, card_data = self._parse_card_data(q_data)

                if success:
                    print("   ✅ 查询成功！获取到卡片详情 (该卡可能已被激活)")
                    return True, card_data
                else:
                    return False, f"查询接口返回失败: {q_data}"
            else:
                return False, f"查询接口请求错误: {query_resp.status_code}"

        except Exception as e:
            return False, f"查询请求异常: {e}"