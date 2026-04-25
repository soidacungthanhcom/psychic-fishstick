from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import socket
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vovinam_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- LINK APPS SCRIPT CỦA BẠN (Đã kiểm tra đúng định dạng) ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzUPw4t5y365-PTmaW1ka-2O_JSMfr-eOVBHVeOaNf-cmrDJ4oe2vsnY0oX-N7p6UQB/exec"
# --------------------------------

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

@app.route('/')
def index(): return "Server OK"

@app.route('/admin')
def admin(): return render_template('admin.html', ip=get_ip_address())

@app.route('/judge')
def judge(): return render_template('judge.html')

@app.route('/viewer')
def viewer(): return render_template('viewer.html')

# --- LẤY DANH SÁCH (CÓ IN LỖI RA MÀN HÌNH ĐỂ KIỂM TRA) ---
@app.route('/get_match_list', methods=['GET'])
def get_match_list():
    try:
        print("--- Đang kết nối Google Sheet để lấy danh sách... ---")
        response = requests.get(GOOGLE_SCRIPT_URL)
        
        # Kiểm tra xem Google có trả về lỗi 302/403 không
        if response.status_code != 200:
            print(f"❌ LỖI KẾT NỐI GOOGLE: Mã lỗi {response.status_code}")
            print("Nội dung lỗi:", response.text[:200]) # In 200 ký tự đầu xem lỗi gì
            return jsonify([])
        
        data = response.json()
        print(f"✅ Đã tải thành công {len(data)} trận đấu!")
        return jsonify(data)
    except Exception as e:
        print(f"❌ LỖI PYTHON: {str(e)}")
        return jsonify([])

# --- LƯU KẾT QUẢ (CÓ IN LỖI RA MÀN HÌNH) ---
@app.route('/save_to_sheet', methods=['POST'])
def save_to_sheet():
    try:
        print("--- Đang gửi kết quả lên Google Sheet... ---")
        response = requests.post(GOOGLE_SCRIPT_URL, json=request.json)
        print("Phản hồi từ Google:", response.text)
        return jsonify(response.json())
    except Exception as e:
        print(f"❌ LỖI LƯU SHEET: {str(e)}")
        return jsonify({"status": "error", "msg": str(e)})

# --- SOCKET EVENTS ---
@socketio.on('vote_event')
def handle_vote(data):
    # Gửi tín hiệu bấm nút cho CẢ Admin và Viewer
    emit('server_send_vote', data, broadcast=True)

@socketio.on('admin_update')
def handle_admin_update(data):
    emit('viewer_receive_update', data, broadcast=True)

# Sự kiện: KẾT THÚC TRẬN (Để nhấp nháy điểm)
@socketio.on('finish_match')
def handle_finish(data):
    emit('viewer_finish', data, broadcast=True)

if __name__ == '__main__':
    ip = get_ip_address()
    print(f"--- ADMIN: http://{ip}:5000/admin ---")
    print(f"--- VIEWER: http://{ip}:5000/viewer ---")
    socketio.run(app, host='0.0.0.0', port=5000)