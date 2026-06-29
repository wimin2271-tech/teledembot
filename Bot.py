import telebot
import sqlite3
import threading
import http.server
import socketserver
import os
from datetime import datetime

# --- KHỞI TẠO WEB SERVER ẢO ĐỂ CHẠY FREE TRÊN RENDER ---
def run_web_server():
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot Check File XX88 dang hoat dong!")

    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- CẤU HÌNH BOT TELEGRAM (BẠN ĐIỀN TOKEN THẬT CỦA BẠN VÀO ĐÂY) ---
TOKEN = '8475285725:AAGfVclXoJ9padzX6sOkcF8YXvicn3ZoF0g' 
bot = telebot.TeleBot(TOKEN)

# --- CƠ SỞ DỮ LIỆU LƯU FILE THỰC TẾ ---
def init_db():
    conn = sqlite3.connect('xx88_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_date TEXT,       -- Định dạng lưu: YYYY-MM-DD
            tg_time TEXT,       -- Định dạng lưu: HH:MM:SS
            username TEXT,
            user_id TEXT,
            file_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_file(date_str, time_str, username, user_id, file_name):
    conn = sqlite3.connect('xx88_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO file_logs (tg_date, tg_time, username, user_id, file_name) VALUES (?, ?, ?, ?, ?)', 
                   (date_str, time_str, username, user_id, file_name))
    conn.commit()
    conn.close()

# --- LỆNH ĐIỀU KHIỂN CHÍNH (XUẤT BÁO CÁO GIỐNG ẢNH MẪU) ---

# Cú pháp: /group xx88 Ngày/Tháng/Năm (Hoặc chỉ cần gõ /thongke)
@bot.message_handler(commands=['group', 'thongke'])
def export_group_report(message):
    # Lấy ngày hiện tại làm mặc định nếu người dùng không gõ ngày cụ thể
    target_date = datetime.now().strftime("%Y-%m-%d")
    display_date = datetime.now().strftime("%d/%m/%Y")
    
    # Nếu người dùng gõ /group xx88 28/06/2026, tách chuỗi để lấy ngày
    args = message.text.split()
    if len(args) >= 3:
        raw_date = args[2] # Lấy chuỗi "28/06/2026"
        try:
            # Chuyển đổi định dạng để truy vấn DB
            target_date = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
            display_date = raw_date
        except:
            pass

    conn = sqlite3.connect('xx88_database.db')
    cursor = conn.cursor()
    # Lấy toàn bộ file trong ngày được chọn
    cursor.execute('SELECT username, file_name FROM file_logs WHERE tg_date = ? ORDER BY id ASC', (target_date,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.reply_to(message, f"📊 Không có dữ liệu file nào cho ngày {display_date}.")
        return

    # Gom nhóm file theo từng thành viên
    user_files = {}
    total_files = len(rows)
    for username, file_name in rows:
        if username not in user_files:
            user_files[username] = []
        user_files[username].append(file_name)

    # Xây dựng nội dung tin nhắn giống y hệt mẫu ảnh bạn gửi
    report = f"📊 **BÁO CÁO FILE NHÓM XX88**\n📅 Ngày {display_date}\n\n"
    
    for user, files in user_files.items():
        report += f"👤 @{user}: {len(files)} file\n"
        for f in files:
            report
