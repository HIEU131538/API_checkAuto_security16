import re
from tests.security.security_function import SecurityFunction

# [FIX]: Đã xóa bỏ các biến url và open_api cứng ở đầu file.
# Toàn bộ hệ thống sẽ dùng self.base_url kế thừa từ lớp cha.

login_admin = {
    "username": "admin",
    "password": "password"
}

# Thông tin user để test BOLA (phải tồn tại trong database)
login_user_1 = {
    "username": "user_100", 
    "password": "password123"
}

class MyTester(SecurityFunction):
    
    def BOLA_hpp(self):
        """
        Kiểm tra lỗ hổng BOLA thông qua HTTP Parameter Pollution (HPP).
        Mục tiêu: Chèn thêm tham số trùng tên để đánh lừa Backend.
        """
        # doc_file_json được kế thừa từ APIClient
        data_test = self.doc_file_json("data/test_data.json")
        lo_hong = False
        du_lieu_bi_lo = None 
        
        for part in data_test:
            if part.get("id") != 13:
                continue

            test_case = part.get("payloads", [])
            token_u1 = self.login(login_user_1) # login() kế thừa từ SecurityFunction
            
            for case in test_case:
                my_id = case["my_id"]
                target_id = case["target_id"]
                print(f"  [>] Đang test HPP: {case['description']}")

                # all_endpoint() kế thừa từ SecurityFunction, đã dùng self.base_url
                endpoints = self.all_endpoint()

                for end in endpoints:
                    # Tìm các endpoint có chứa tham số ID trong ngoặc nhọn {id}
                    match = re.search(r'\{([^}]*id[^}]*)\}', end, re.IGNORECASE)
                    
                    if match:
                        header = {"Authorization": f"Bearer {token_u1}"}
                        param_ngoac = match.group(0)
                        param_name = match.group(1)

                        # Kỹ thuật HPP: /users/101?user_id=104
                        target_endpoint = end.replace(param_ngoac, str(my_id) + f"?{param_name}={target_id}")
                        
                        try:
                            # _xu_ly_yeu_cau() kế thừa từ APIClient, tự động ghép self.base_url
                            shoot = self._xu_ly_yeu_cau("GET", target_endpoint, headers=header)

                            if shoot.status_code == 200:
                                # Nếu thấy dữ liệu của target_id mà không phải của my_id -> Dính BOLA
                                if str(target_id) in shoot.text and str(my_id) not in shoot.text:
                                    print(f"  [!] CẢNH BÁO: Phát hiện BOLA HPP tại {target_endpoint}")
                                    lo_hong = True
                                    du_lieu_bi_lo = shoot.json()
                                    return lo_hong, du_lieu_bi_lo
                        except Exception as e:
                            print(f"  [X] Lỗi thực thi BOLA HPP: {e}")
                            
        return False, None

    def BOLA_classic(self):
        """
        Kiểm tra lỗ hổng BOLA Classic (IDOR cơ bản).
        Mục tiêu: Thay đổi ID trực tiếp trên URL để truy cập dữ liệu người khác.
        """
        data_test = self.doc_file_json("data/test_data.json")
        lo_hong = False
        du_lieu_bi_lo= None
        
        for part in data_test:
            if part.get("id") != 13:
                continue

            test_case = part.get("payloads", [])
            token_u1 = self.login(login_user_1)
            
            for case in test_case:
                target_id = case["target_id"]
                my_id = case["my_id"]
                print(f"  [>] Đang test Classic: {case['description']}")

                endpoints = self.all_endpoint()
                for end in endpoints:
                    match = re.search(r'\{([^}]*id[^}]*)\}', end, re.IGNORECASE)

                    if match:
                        header = {"Authorization": f"Bearer {token_u1}"}
                        param_ngoac = match.group(0)

                        # Thay thế {id} bằng target_id của nạn nhân
                        target_end = end.replace(param_ngoac, str(target_id))
                        try:
                            shoot = self._xu_ly_yeu_cau("GET", target_end, headers=header)

                            if shoot.status_code == 200:
                                if str(target_id) in shoot.text and str(my_id) not in shoot.text:
                                    print(f"  [!] CẢNH BÁO: Phát hiện BOLA Classic tại {target_end}")
                                    lo_hong = True
                                    du_lieu_bi_lo = shoot.json()
                                    return lo_hong,du_lieu_bi_lo
                        except Exception as e:
                            print(f"  [X] Lỗi thực thi BOLA Classic: {e}")
                            
        return False, None

# [FIX]: Đã xóa toàn bộ các hàm test_bola_... và dòng tool = MyTester(url) ở cuối file.
# Các hàm này giờ đã được Pytest quản lý tập trung tại file tool.py.