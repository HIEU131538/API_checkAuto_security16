from database import SessionLocal, User, engine, Base #

def seed_data():
    Base.metadata.create_all(bind=engine) # Đảm bảo có bảng
    db = SessionLocal()
    try:
        # Chỉ xóa user test cũ, giữ lại admin (thường có ID nhỏ hoặc username='admin')
        # Sửa dòng này: Giữ lại admin và giữ lại cả test_blocked
        db.query(User).filter(User.username != "admin").filter(User.username != "test_blocked").delete()
        
        # Nạp 50 user để test BOLA
        for i in range(99, 151):
            new_user = User(
                Id=i,
                username=f"user_{i}",
                password="password123",
                Ten=f"User Test {i}",
                role="user"
            )
            db.add(new_user)
        db.commit()
        print("✔ Đã nạp 50 user vào Docker thành công!")
    except Exception as e:
        print(f"✘ Lỗi nạp dữ liệu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()