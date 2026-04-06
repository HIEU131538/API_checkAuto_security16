import requests
import re
from core.api_client import APIClient

class SecurityFunction(APIClient):

    def hien_thi_log(self, method, url, response): # Thêm lại tham số url cho đúng chuẩn lớp cha

        # Kiểm tra nếu url hiện tại chứa openapi hoặc swagger
        if "openapi.json" in url or "swagger.json" in url:
            return 

        print(f"  [>] {method} {url} | Status: {response.status_code}")

    def post_data(self, endpoint, data_input):

        if "/token" in endpoint:
            # FIX: Giữ nguyên định dạng urlencoded của hệ thống
            header_form = {"Content-Type": "application/x-www-form-urlencoded"}
            return self._xu_ly_yeu_cau("POST", endpoint, data=data_input, headers=header_form)
        else:
            return self._xu_ly_yeu_cau("POST", endpoint, json=data_input)

    def find_api(self): # Bỏ tham số đầu vào, dùng thẳng self.base_url
        pos_path = [
            "/openapi.json", "/swagger.json", "/api/swagger.json",
            "/v1/swagger.json", "/v2/api-docs", "/v3/api-docs",
            "/docs/openapi.json", "/api-docs", "/v2/swagger.json", "/v3/swagger.json"
        ]

        for path in pos_path:
            # Tự động ghép self.base_url  với đường dẫn path
            scan_url = f"{self.base_url}{path}"
            try:
                check = self.get(path, silent=True) # Dùng silent để đỡ rác log
                if check.status_code == 200:
                    data = check.json()
                    if "openapi" in data or "swagger" in data:
                        return path
            except Exception:
                   pass
        print(" Không tìm thấy file OpenAPI/Swagger nào cả T-T")
        return None
    
    def load_wordlist(self,file_path):
        try:
            wordlist = []
            with open(file_path,'r',encoding = 'utf-8') as file:
                for line in file.readlines():
                    pwd = line.strip()
                    if pwd:
                        wordlist.append(pwd)
                return wordlist
        except FileNotFoundError:
            print("Loi roi @@")
            return []
        
    def login(self, login_data):
        res = self.post_data("/token", login_data)
        if res.status_code == 200:
            token = res.json().get("access_token")
            if token:
                self.gan_token(token)
                print(" Đã lưu Token thành công cho các lần test sau.")
                return token
        print(" Đăng nhập thất bại, kiểm tra lại tài khoản.")
        return None

    def get_endpoint_map(self):
        api_path = self.find_api() 
        if not api_path: return {}
        
        data = self.get(api_path).json()
        paths = data.get("paths", {})
        mapping = {}

        for path, methods in paths.items():
            for method, detail in methods.items():
                if method.lower() == "get": continue
                body = detail.get("requestBody", {})
                content = body.get("content", {})
                for app, schema_info in content.items():
                    schema = schema_info.get("schema", {})
                    ref = schema.get("$ref")
                    if ref:
                        schema_name = ref.split("/")[-1]
                        mapping[f"{path.lower()} {method}"] = schema_name
        return mapping

    def get_component_map(self):
        api_path = self.find_api()
        if not api_path: return {}
        data = self.get(api_path).json()
        components = data.get("components", {})
        schemas = components.get("schemas", {})

        result_map = {}
        for component, schema_content in schemas.items():
            properties = schema_content.get("properties", {})
            required = schema_content.get("required", [])
            tmp_map = {}
            for field_name, field_info in properties.items():
                # Chỉ lấy thông tin nếu trường đó bắt buộc (Required)
                if field_name in required:
                    tmp_map[field_name] = {
                        "type": field_info.get('type'),
                        "format": field_info.get('format')
                    }
            result_map[component] = tmp_map     
        return result_map

    def all_endpoint(self):
        api_path = self.find_api() 
        if not api_path: return []
        data = self.get(api_path).json()
        return list(data.get("paths", {}).keys())