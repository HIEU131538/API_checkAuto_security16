import json
import allure
from core.api_client import APIClient

class FunctionalTester(APIClient):
    def __init__(self, base_url):
        super().__init__(base_url)
        # Không cần self.results nữa vì Pytest và Allure sẽ lo việc báo cáo

    def execute_single_case(self, case):
        """
        Công nhân chuyên cần: Chỉ nhận đúng 1 case từ Pytest và thực thi nó.
        """
        cid = case.get('id')
        method = case.get('method')
        endpoint = case.get('endpoint')
        payload = case.get('payload')

        # [ALLURE] Đính kèm dữ liệu gửi đi vào báo cáo để thầy cô dễ chấm
        if payload:
            allure.attach(
                json.dumps(payload, indent=2), 
                name="Payload Gửi Đi", 
                attachment_type=allure.attachment_type.JSON
            )

        # 1. XỬ LÝ LOGIC ĐĂNG NHẬP (Lưu Token cho các case sau)
        # 1. XỬ LÝ LOGIC ĐĂNG NHẬP (Lưu Token cho các case sau)
        if endpoint == "/token" and method == "POST":
            # ĐỔI THÀNH GỬI FORM-DATA VÀ ÉP HEADER LẠI CHO ĐÚNG CHUẨN OAUTH2
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = self.post(endpoint, data=payload, headers=headers)
            
            # Nếu là Admin (ID = 1) và login thành công, lưu lại Token vào Session
            if response and response.status_code == 200 and cid == 1:
                token = response.json().get("access_token")
                if token:
                    self.gan_token(token)
                    print(f"\n  [INFO] Đã lưu Admin Token thành công. Các case sau sẽ có quyền Admin.")
            
            self._attach_response_to_allure(response)
            return response
            
        # 2. XỬ LÝ CÁC REQUEST CRUD THÔNG THƯỜNG (GET, POST, PUT, DELETE)
        else:
            # Dùng getattr để tự động gọi đúng hàm trong APIClient (self.get, self.post...)
            func = getattr(self, method.lower())
            
            # Nếu có payload thì gửi kèm json, không thì thôi
            response = func(endpoint, json=payload) if payload else func(endpoint)
            
            self._attach_response_to_allure(response)
            return response

    def _attach_response_to_allure(self, response):
        """Hệ thống phân tích tự động: Check JSON + Check Header + Check Timing"""
        if response is not None:
            # 1. Đo thời gian phản hồi (Check Timing)
            response_time = response.elapsed.total_seconds()
            time_msg = f"Thời gian phản hồi: {response_time}s"
            if response_time > 3:
                time_msg += " ⚠️ (Cảnh báo: Server phản hồi chậm, có dấu hiệu quá tải hoặc Brute Force)"
            allure.attach(time_msg, name="⏱️ Response Timing", attachment_type=allure.attachment_type.TEXT)

            # 2. So khớp Header bảo mật (Check Header)
            required_headers = ["X-Content-Type-Options", "X-Frame-Options", "Strict-Transport-Security"]
            missing = [h for h in required_headers if h not in response.headers]
            
            header_results = "✅ Header bảo mật đầy đủ." if not missing else f"❌ Thiếu Header quan trọng: {', '.join(missing)}"
            allure.attach(header_results, name="🛡️ Security Headers Check", attachment_type=allure.attachment_type.TEXT)

            # 3. Đính kèm Body Response (JSON) như cũ
            try:
                formatted_response = json.dumps(response.json(), indent=2, ensure_ascii=False)
                allure.attach(formatted_response, name="Kết Quả API Trả Về", attachment_type=allure.attachment_type.JSON)
            except:
                allure.attach(response.text, name="Kết Quả API (Text)", attachment_type=allure.attachment_type.TEXT)