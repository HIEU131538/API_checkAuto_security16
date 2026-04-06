# API Security Testing Tool with Dockerized Environment

Dự án này là một công cụ kiểm thử bảo mật API tự động, được thiết kế để phát hiện các lỗ hổng phổ biến

Hệ thống được đóng gói hoàn toàn bằng Docker , giúp triển khai nhanh chóng và đảm bảo tính nhất quán trên mọi môi trường.
## Kiến trúc hệ thống
Dự án bao gồm 2 thành phần chính hoạt động trong các Container biệt lập:

1.  **Target API**: Một hệ thống FastAPI mô phỏng các nghiệp vụ thực tế (Quản lý User, Login, Data commit).
2.  **Security Tool**: Công cụ quét được viết bằng Python, sử dụng Pytest và Allure để thực hiện tấn công và xuất báo cáo (Module chức năng, Module bảo mật, Module báo cáo)

---
## Hướng dẫn triển khai
### 1. Yêu cầu hệ thống
- Đã cài đặt **Docker**, **Allure** và **Docker Compose**.
### 2. Khởi chạy môi trường Target API
Di chuyển vào thư mục API và khởi chạy:

B1 :( Mở API và tool nếu chưa mở) docker-compose down 

			docker-compose up -d --build
			
B2: docker exec fastapi_container python seed_db.py ( add data into API)

B3   docker-compose run --rm security-tool 

B4: allure serve ./allure-results

## Phân chia nhiệm vụ 
Dương Ngọc Hiếu : nhóm trưởng, viết FrameWork định hướng và phát triển chức năng tool ( module báo cáo , tool cuối)

Vũ Duy Điệp : phát triển xây dựng đối tượng kiểm thử ( Target_API), slide 

Nguyễn Trung Duy : phát triển chức năng tool ( module bảo mật) 

Nguyễn Quang Đạt : phụ trách viết báo cáo, word và lý thuyết 

Phạm Văn Qúy : phát triển chức năng tool ( module chức năng )
