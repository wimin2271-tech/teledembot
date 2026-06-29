import telebot
import sqlite3
import threading
import http.server
import socketserver
import os  # <-- Nhớ có import os này để lấy cổng của Render

def run_web_server():
    handler = http.server.SimpleHTTPRequestHandler
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Web server đang chạy ở cổng {port}")
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
from datetime import datetime

TOKEN = '8475285725:AAGfVclXoJ9padzX6sOkcF8YXvicn3ZoF0g'
bot = telebot.TeleBot(TOKEN)

# --- KHỞI TẠO DATABASE COOKIES/SQLITE ---
def init_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    # Tạo bảng lưu trữ thông tin file nếu chưa có
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_date TEXT,
            username TEXT,
            file_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Hàm lưu file vào database
def save_file(date_str, username, file_name):
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO file_logs (tg_date, username, file_name) VALUES (?, ?, ?)', 
                   (date_str, username, file_name))
    conn.commit()
    conn.close()

# Hàm lấy dữ liệu thống kê
def get_stats(date_str):
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('SELECT username, file_name FROM file_logs WHERE tg_date = ?', (date_str,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- LẮNG NGHE TIN NHẮN CHỨA FILE VÀ ẢNH ---
@bot.message_handler(content_types=['document', 'photo'])
def handle_files(message):
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Lấy username hoặc tên hiển thị
    if message.from_user.username:
        username = f"@{message.from_user.username}"
    else:
        username = message.from_user.first_name

    # Xử lý lấy tên file
    if message.document:
        file_name = message.document.file_name
    elif message.photo:
        # Nếu là ảnh gửi dạng Photo, Telegram không có tên file gốc nên ta đặt theo mã tin nhắn
        file_name = f"Photo_{message.message_id}.png"
    else:
        return

    # Lưu vào DB
    save_file(today, username, file_name)

# --- XỬ LÝ LỆNH THỐNG KÊ ---
@bot.message_handler(commands=['thongke'])
def send_report(message):
    # Phân tích cú pháp xem người dùng có gõ ngày cụ thể không (Ví dụ: /thongke 28/06/2026)
    args = message.text.split()
    if len(args) > 1:
        target_date = args[1]
    else:
        target_date = datetime.now().strftime("%d/%m/%Y")

    # Đang thống kê... (Tạo hiệu ứng chờ như trong ảnh)
    waiting_msg = bot.reply_to(message, f"⌛ Đang thống kê file ({target_date})...")

    # Lấy dữ liệu từ DB
    data = get_stats(target_date)

    if not data:
        report = f"📊 THỐNG KÊ FILE — Ngày {target_date}\n\n✅ Tổng: 0 file"
        bot.edit_message_text(report, chat_id=message.chat.id, message_id=waiting_msg.message_id)
        return

    # Gộp dữ liệu theo từng người dùng
    user_files = {}
    total_files = 0
    for username, file_name in data:
        if username not in user_files:
            user_files[username] = []
        user_files[username].append(file_name)
        total_files += 1

    # Tạo nội dung tin nhắn trả về giống hệt mẫu trong ảnh
    report = f"📊 THỐNG KÊ FILE — Ngày {target_date}\n\n"
    for username, files in user_files.items():
        report += f"👤 {username}: {len(files)} file\n"
        for f in files:
            report += f" - {f}\n"
            
    report += f"\n✅ Tổng: {total_files} file"

    # Cập nhật lại tin nhắn chờ thành tin nhắn kết quả
    bot.edit_message_text(report, chat_id=message.chat.id, message_id=waiting_msg.message_id)

# Chạy bot
if __name__ == '__main__':
    init_db()
    print("Bot đang chạy...")
    bot.infinity_polling()  # <-- BẮT BUỘC phải có dòng này ở cuối cùng file
