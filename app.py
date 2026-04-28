import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import socket
import requests
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vovinam_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- LINK APPS SCRIPT CỦA BẠN ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzUPw4t5y365-PTmaW1ka-2O_JSMfr-eOVBHVeOaNf-cmrDJ4oe2vsnY0oX-N7p6UQB/exec"

# =========================================================
# Ổ KHÓA BẢO MẬT
# =========================================================
def check_auth(username, password):
    valid_user = os.environ.get('ADMIN_USER', 'vovinam')
    valid_pass = os.environ.get('ADMIN_PASS', 'vovinam2026')
    return username == valid_user and password == valid_pass

def authenticate():
    return Response('CẢNH BÁO: Khu vực dành cho Ban Tổ Chức!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password): return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except: ip = "127.0.0.1"
    finally: s.close()
    return ip

# =========================================================
# QUẢN LÝ ĐƯỜNG DẪN (ROUTES)
# =========================================================
@app.route('/')
def index(): return "HỆ THỐNG ĐIỀU HÀNH GIẢI VOVINAM - CHẠY TỐT CẢ ĐỐI KHÁNG VÀ QUYỀN"

# --- NHÓM ĐỐI KHÁNG ---
@app.route('/admin')
@requires_auth
def admin(): return render_template('admin.html', ip=get_ip_address())

@app.route('/judge')
@requires_auth
def judge(): return render_template('judge.html')

@app.route('/viewer')
def viewer(): return render_template('viewer.html')

# --- NHÓM QUYỀN ---
@app.route('/admin_quyen')
@requires_auth
def admin_quyen(): return render_template('admin_quyen.html', ip=get_ip_address())

@app.route('/judge_quyen')
@requires_auth
def judge_quyen(): return render_template('judge_quyen.html')

# =========================================================
# CẦU NỐI GOOGLE SHEET (DÙNG CHUNG)
# =========================================================
@app.route('/get_match_list', methods=['GET'])
def get_match_list():
    try:
        # Tự động đọc xem Frontend đang xin danh sách gì (Quyền hay Đối kháng)
        req_type = request.args.get('type', 'DOI_KHANG')
        print(f"--- Đang tải danh sách từ Google Sheet: Loại {req_type} ---")
        
        response = requests.get(GOOGLE_SCRIPT_URL + f"?type={req_type}")
        return jsonify(response.json())
    except Exception as e:
        print(f"❌ LỖI TẢI DANH SÁCH: {str(e)}")
        return jsonify([])

@app.route('/save_to_sheet', methods=['POST'])
def save_to_sheet():
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=request.json)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


# =========================================================
# TRUNG TÂM XỬ LÝ SOCKET - ĐỐI KHÁNG
# =========================================================
@socketio.on('vote_event')
def handle_vote(data): emit('server_send_vote', data, broadcast=True)

@socketio.on('admin_update')
def handle_admin_update(data): emit('viewer_receive_update', data, broadcast=True)

@socketio.on('finish_match')
def handle_finish(data): emit('viewer_finish', data, broadcast=True)


# =========================================================
# TRUNG TÂM XỬ LÝ SOCKET - QUYỀN
# =========================================================
current_quyen_scores = {}
quyen_config = {'num_judges': 5}

@socketio.on('submit_score')
def handle_score(data):
    judge_id = str(data['judge_id'])
    current_quyen_scores[judge_id] = {'val': float(data['score']), 'details': data.get('details', '')}
    emit('update_board', calculate_quyen_result(), broadcast=True)

@socketio.on('change_config')
def handle_config(data):
    quyen_config['num_judges'] = int(data['num'])
    current_quyen_scores.clear()
    emit('config_updated', {'num': quyen_config['num_judges']}, broadcast=True)
    emit('update_board', calculate_quyen_result(), broadcast=True)

@socketio.on('reset_scores')
def handle_reset():
    current_quyen_scores.clear()
    emit('update_board', calculate_quyen_result(), broadcast=True)

def calculate_quyen_result():
    num = quyen_config['num_judges']
    scores_list = []
    for i in range(1, num + 1):
        s_id = str(i)
        data = current_quyen_scores.get(s_id, {'val': 0, 'details': ''})
        scores_list.append({'id': s_id, 'val': data['val'], 'details': data['details']})

    if len(current_quyen_scores) < num:
        return {'scores': scores_list, 'total': 'Waiting...', 'dropped': []}

    vals = [s['val'] for s in scores_list]
    dropped_ids = []
    total = 0

    if num == 3: total = sum(vals)
    else: 
        max_v, min_v = max(vals), min(vals)
        found_max = found_min = False
        for s in scores_list:
            if s['val'] == max_v and not found_max:
                found_max = True; dropped_ids.append(s['id'])
            elif s['val'] == min_v and not found_min:
                found_min = True; dropped_ids.append(s['id'])
            else:
                total += s['val']

    return {'scores': scores_list, 'total': round(total, 2), 'dropped': dropped_ids, 'config': num}

# =========================================================
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
