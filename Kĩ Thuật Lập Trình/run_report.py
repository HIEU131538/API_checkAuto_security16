import os
import time
import shutil

def create_environment_file(target_url):
    """Tạo file thông tin môi trường cho Allure"""
    env_content = f"""Target_URL={target_url}
    OS=Window (Docker Desktop)
    Framework=FastAPI
    Language=Python 3.9
    Database=SQLite (Dev)
    Tester=Hiếu đẹp try
    Project=Security API Testing KMA
    """
    if not os.path.exists("allure-results"):
        os.makedirs("allure-results")
    with open("allure-results/environment.properties", "w", encoding="utf-8") as f:
        f.write(env_content)

def create_executor_file(target_url):
    import json
    executor_info = {
        "name": "Hiếu đẹp try",
        "type": "github", # Để jenkins cho nó ngầu, Allure sẽ hiện icon
        "reportName": "Security Testing Report",
        "buildName": "Build #1.0.4",
        "buildUrl": target_url
    }
    if not os.path.exists("allure-results"):
        os.makedirs("allure-results")
    with open("allure-results/executor.json", "w", encoding="utf-8") as f:
        json.dump(executor_info, f, ensure_ascii=False, indent=4)

def run():
    print("\n" + "="*50)
    
    # 1. KIỂM TRA BIẾN MÔI TRƯỜNG TRƯỚC (Dành cho Docker/Automation)
    target_url = os.getenv("TARGET_URL")
    
    if target_url:
        print(f">>> [HỆ THỐNG] Phát hiện TARGET_URL từ môi trường: {target_url}")
    else:
        # 2. NẾU KHÔNG CÓ BIẾN MÔI TRƯỜNG THÌ MỚI HỎI (Dành cho chạy tay)
        target_url = input("Nhập API url cần test (mặc định localhost:8000): ").rstrip()
        if not target_url:
            target_url = "http://host.docker.internal:8000"
    
    # Đảm bảo TARGET_URL này được đẩy vào os.environ để api_client.py dùng được
    os.environ["TARGET_URL"] = target_url
    
    
    print(">>> [3/7] Dọn dẹp & Kế thừa lịch sử Allure...")
    if os.path.exists("allure-results"):
        for item in os.listdir("allure-results"):
            if item != "history":
                path = os.path.join("allure-results", item)
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): shutil.rmtree(path)

    if os.path.exists("allure-report/history"):
        if not os.path.exists("allure-results/history"): os.makedirs("allure-results/history")
        for item in os.listdir("allure-report/history"):
            shutil.copy2(os.path.join("allure-report/history", item), os.path.join("allure-results/history", item))

    # --- ĐÂY LÀ CHỖ TẠO LẠI ENVIRONMENT ---
    print(">>> [4/7] Cấu hình môi trường báo cáo...")
    create_environment_file(target_url)
    create_executor_file(target_url)

    print(">>> [5/7] Thực thi Test...")
    os.system("python -m pytest tool.py --alluredir=./allure-results")

    print(">>> [6/7] Tạo báo cáo...")
    os.system("allure generate allure-results -o allure-report --clean")
    
    print(">>> [7/7] Hoàn thành! Mở trình duyệt...")
    os.system("allure open allure-report")

if __name__ == "__main__":
    run()