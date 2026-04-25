import requests
import json

# --- DÁN LINK CỦA BẠN VÀO ĐÂY ---
URL = "https://script.google.com/macros/library/d/13vfaETblQW2z4CTVeNKTezpN_ndI8dBV6EKIsJkgINvLgdvm8VIUoXTl/3" 
# --------------------------------

print("--- ĐANG KIỂM TRA KẾT NỐI GOOGLE SHEET ---")

# 1. Test Lấy danh sách (GET)
try:
    print(f"1. Đang thử tải danh sách từ: {URL}...")
    response = requests.get(URL)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ KẾT NỐI THÀNH CÔNG!")
        print(f"   Dữ liệu nhận được: {len(data)} dòng.")
        print(f"   Mẫu dòng đầu: {data[0] if len(data)>0 else 'Trống'}")
    elif response.status_code == 302:
        print("❌ LỖI: Link bị chuyển hướng. Có thể do bạn chưa chọn quyền 'Bất kỳ ai' (Anyone).")
    else:
        print(f"❌ LỖI: Mã phản hồi {response.status_code}")
        print("Nội dung lỗi:", response.text)

except Exception as e:
    print("❌ LỖI NGHIÊM TRỌNG:", str(e))

# 2. Test Lưu dữ liệu (POST)
print("\n2. Đang thử lưu một dòng test...")
try:
    test_data = {
        "matchId": "TEST_KET_NOI",
        "round": "Test",
        "blueName": "Test Xanh",
        "blueScore": 0,
        "redName": "Test Đỏ",
        "redScore": 0,
        "winner": "KHÔNG"
    }
    res = requests.post(URL, json=test_data)
    print("   Phản hồi khi lưu:", res.text)
except Exception as e:
    print("❌ Lỗi khi lưu:", str(e))