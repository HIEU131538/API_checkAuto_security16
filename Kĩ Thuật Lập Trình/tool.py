import pytest
import allure
import json
from tests.funtional.test_chuc_nang import FunctionalTester
from tests.security.Broken_auth_v1 import MyTester
import os

def get_test_data():
    with open("data/test_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def api_tools():
    base_url = os.getenv("TARGET_URL","http://127.0.0.1:8000")
    
    return {
        "runner": FunctionalTester(base_url),
        "security": MyTester(base_url)
    }

# ==========================================
# NHÓM 1: CHỨC NĂNG & SQL INJECTION (ID 1 -> 12)
# ==========================================
@allure.epic("Đồ Án Kiểm Thử API")
@allure.feature("Kiểm Thử Chức Năng & SQL Injection")
@pytest.mark.parametrize("case", get_test_data())
def test_main_cases(case, api_tools):
    runner = api_tools["runner"]
    case_id = case.get("id")
    expected = case.get("expected_status")

    # Bỏ qua các ID từ 13 trở đi vì đã có kịch bản quét bảo mật riêng ở dưới
    if case_id > 12:
        pytest.skip("Kịch bản bảo mật chuyên sâu được quét riêng biệt")

    allure.dynamic.title(f"[Case {case_id}] {case.get('case_name')}")
    
    # Thực thi test
    response = runner.execute_single_case(case)
    actual = response.status_code if response is not None else None
    
    # Logic Xanh/Đỏ: Khớp Status thì Xanh, Lệch Status thì Đỏ
    with allure.step(f"Kiểm tra Status Code: Mong đợi {expected} - Thực tế {actual}"):
        assert actual == expected, f"❌ Thất bại! Mong đợi {expected} nhưng thực tế nhận {actual}"

# ==========================================
# NHÓM 2: BẢO MẬT BOLA (ID 13 TÁCH ĐÔI)
# ==========================================
@allure.epic("Đồ Án Kiểm Thử API")
@allure.feature("Kiểm Thử Bảo Mật BOLA / IDOR")
def test_bola_classic(api_tools):
    allure.dynamic.title("[Case 13.1] Quét lỗ hổng BOLA Classic (Sửa ID trực tiếp)")
    security = api_tools["security"]
    
    is_vulnerable, leaked_data = security.BOLA_classic()
    
    with allure.step("Kết luận bảo mật BOLA Classic"):
        if is_vulnerable:
            bang_chung = json.dumps(leaked_data, indent=4, ensure_ascii=False)
            allure.attach(bang_chung, name="📦 DỮ LIỆU NẠN NHÂN BỊ ĐÁNH CẮP", attachment_type=allure.attachment_type.JSON)
            print("\n" + "="*40)
            print("[!] CẢNH BÁO: ĐÃ LẤY ĐƯỢC DỮ LIỆU NẠN NHÂN")
            print(bang_chung)
            print("="*40 + "\n")
            assert False, "❌ LỖI: Hệ thống dính lỗ hổng BOLA Classic!"
        else:
            assert True # Hệ thống trả về 401/403 -> An toàn (Xanh)

@allure.epic("Đồ Án Kiểm Thử API")
@allure.feature("Kiểm Thử Bảo Mật BOLA / IDOR")
def test_bola_hpp(api_tools):
    allure.dynamic.title("[Case 13.2] Quét lỗ hổng BOLA HPP (Parameter Pollution)")
    security = api_tools["security"]
    
    is_vulnerable, leaked_data = security.BOLA_hpp()
    
    with allure.step("Kết luận bảo mật BOLA HPP"):
        if is_vulnerable:
            # 🔥 ĐÍNH KÈM DATA VÀO ĐÂY
            bang_chung = json.dumps(leaked_data, indent=4, ensure_ascii=False)
            allure.attach(bang_chung, name="📦 DỮ LIỆU NẠN NHÂN (HPP)", attachment_type=allure.attachment_type.JSON)
            print("\n" + "="*40)
            print("[!] CẢNH BÁO: ĐÃ LẤY ĐƯỢC DỮ LIỆU NẠN NHÂN")
            print(bang_chung)
            print("="*40 + "\n")
            assert False, "❌ LỖI: Hệ thống dính lỗ hổng BOLA HPP!"
        else:
            assert True

# ==========================================
# NHÓM 3: BROKEN AUTH & BRUTE FORCE (ID 14)
# ==========================================
@allure.epic("Đồ Án Kiểm Thử API")
@allure.feature("Kiểm Thử Brute Force")
def test_brute_force(api_tools):
    allure.dynamic.title("[Case 14] Tấn công Brute Force / Password Spraying")
    security = api_tools["security"]
    
    is_vulnerable, hack_creds = security.Brute_force()
    
    with allure.step("Kết luận bảo mật Brute Force"):
        if is_vulnerable:
            # Ép kiểu đẹp để in lên Allure
            bang_chung = json.dumps(hack_creds, indent=2, ensure_ascii=False)
            allure.attach(bang_chung, name="🔥 TÀI KHOẢN DÒ TRÚNG", attachment_type=allure.attachment_type.JSON)
            print("\n" + "="*40)
            print("[!] BRUTE FORCE THÀNH CÔNG! THÔNG TIN TÀI KHOẢN:")
            print(bang_chung)
            print("="*40 + "\n")
            assert False, "❌ LỖI: Hệ thống bị Brute Force thành công!"
        else:
            assert True
# ==========================================
# NHÓM 4: BẢO MẬT JWT (ID 15)
# ==========================================
@allure.epic("Đồ Án Kiểm Thử API")
@allure.feature("Kiểm Thử Bảo Mật JWT")
def test_jwt_vulnerabilities(api_tools):
    allure.dynamic.title("[Case 15] Tấn công giả mạo JWT (Broken Authentication)")
    security = api_tools["security"]
    user_cred = {"username": "duynt", "password": "duynt"}

    with allure.step("Tấn công JWT No Signature (Xóa chữ ký)"):
        is_no_sig_vuln = security.jwt_manipulation_payload(user_cred, "/users")
        if is_no_sig_vuln:
            allure.attach("Hệ thống chấp nhận Token bị xóa chữ ký", name="CẢNH BÁO BẢO MẬT")
            assert False, "❌ LỖI: Dính lỗ hổng JWT No Signature!"

    with allure.step("Tấn công JWT None Algorithm (Đổi thuật toán None)"):
        is_none_alg_vuln = security.jwt_none_algro(user_cred, "/users")
        if is_none_alg_vuln:
            allure.attach("Hệ thống chấp nhận Token với Algorithm = none", name="CẢNH BÁO BẢO MẬT")
            assert False, "❌ LỖI: Dính lỗ hổng JWT None Algorithm!"