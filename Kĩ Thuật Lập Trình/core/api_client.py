import requests
import json
import time
import os
from datetime import timedelta

# 1. Định nghĩa FakeResponse ở ngoài cùng để dùng chung
class FakeResponse:
    def __init__(self):
        self.status_code = 503
        self.text = "Service Unavailable (Connection Refused)"
        self.headers = {}
        self.elapsed = timedelta(seconds=0)
        self.duration_ms = 0 # Quan trọng: Để hien_thi_log không bị lỗi

    def json(self):
        return {"error": "Connection Failed"}

class APIClient:
    """
    [LƯU Ý CHO CẢ NHÓM]
    - Đây là file xương sống của dự án.
    """

    def __init__(self, base_url, timeout=10):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def gan_token(self, token):
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        print(f">>> [HỆ THỐNG]: Đã nạp Token.")

    def xoa_token(self):
        if "Authorization" in self.session.headers:
            self.session.headers.pop("Authorization")
            print(">>> [HỆ THỐNG]: Đã xóa sạch Token.")

    def _xu_ly_yeu_cau(self, method, endpoint, silent=False, **kwargs):
        full_url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=full_url,
                timeout=self.timeout,
                **kwargs
            )
            # Tính thời gian cho response thật
            response.duration_ms = (time.time() - start_time) * 1000

            if not silent:
                self.hien_thi_log(method, full_url, response)
            
            return response

        except requests.exceptions.RequestException as e:
            print(f"  [X] SERVER SẬP HOẶC TỪ CHỐI KẾT NỐI TẠI {endpoint}: {e}")
            # Trả về object FakeResponse đã định nghĩa ở trên
            return FakeResponse()

    def hien_thi_log(self, method, url, response):
        print(f"\n{'='*20} [LOG] {'='*20}")
        print(f"[*] ACTION: {method} {url}")
        # Dùng .get để an toàn hoặc đảm bảo duration_ms luôn tồn tại
        duration = getattr(response, 'duration_ms', 0)
        print(f"[*] STATUS: {response.status_code} | TIME: {duration:.2f}ms")
        try:
            content = json.dumps(response.json(), indent=2, ensure_ascii=False)
            print(f"[*] DATA: {content[:200]}..." if len(content) > 200 else f"[*] DATA: {content}")
        except:
            text = getattr(response, 'text', "No content")
            print(f"[*] TEXT: {text[:100]}...")
        print(f"{'='*47}\n")

    def get(self, endpoint, **kwargs):
        return self._xu_ly_yeu_cau("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._xu_ly_yeu_cau("POST", endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._xu_ly_yeu_cau("PUT", endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._xu_ly_yeu_cau("DELETE", endpoint, **kwargs)

    @staticmethod
    def doc_file_json(duong_dan):
        if not os.path.exists(duong_dan):
            print(f"  [!] LỖI: File {duong_dan} không tồn tại!")
            return []
        try:
            with open(duong_dan, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"  [!] LỖI ĐỊNH DẠNG JSON: {e}")
            return []