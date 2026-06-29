import telebot
import sqlite3
import threading
import http.server
import socketserver
import os
from datetime import datetime

# --- KHỞI TẠO WEB SERVER ẢO ĐỂ QUA MẶT RENDER ---
def run_web_server():
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot check file dang hoat dong!")

    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- CẤU HÌNH BOT TELEGRAM ---
TOKEN = '8475285725:AAGfVc1XoJ9padzX6sOkcF8YXvicn3Zof0g'  # Token chuẩn của bạn
bot = telebot.TeleBot(TOKEN)

# --- KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE TRÊN ĐĨA ẢO ---
def init_db():
    # Thay đổi từ ':memory:' sang file thực tế để lưu dữ liệu không bị mất khi restart
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_date TEXT,
            username TEXT,
            file_name TEXT,
            file_size TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_file(date_str, username, file_name, file_size):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO file_logs (tg_date, username, file_name, file_size) VALUES (?, ?, ?, ?)', 
                   (date_str, username, file_name, file_size))
    conn.commit()
    conn.close()

# --- CÁC LỆNH ĐIỀU KHIỂN BOT ---

# Lệnh /start hoặc /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **HỆ THỐNG CHECK FILE TỰ ĐỘNG** 🤖\n\n"
        "Chào mừng bạn! Bot đang chạy ngầm ổn định.\n"
        "👉 **Cách dùng:** Bạn chỉ cần gửi hoặc chuyển tiếp (forward) bất kỳ FILE nào vào đây.\n"
        "📊 **Lệnh xem báo cáo:** Gõ `/thongke` để xem danh sách file đã đếm."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# Lệnh /thongke để xem danh sách file đã lưu giống bot mẫu
@bot.message_handler(commands=['thongke'])
def show_stats(message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tg_date, username, file_name, file_size FROM file_logs ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.reply_to(message, "📊 Chưa có file nào được lưu trữ trong hệ thống.")
        return
        
    report = "📊 **DANH SÁCH 10 FILE ĐƯỢC CHECK GẦN ĐÂY NHẤT:**\n\n"
    for idx, row in enumerate(rows, 1):
        report += f"{idx}. 📂 **{row[2]}** ({row[3]})\n"
        report += f"   👤 Gửi bởi: @{row[1]} | ⏱ {row[0]}\n"
        report += "---------------------\n"
        
    bot.reply_to(message, report, parse_mode='Markdown')

# --- TỰ ĐỘNG BẮT SỰ KIỆN KHI NGƯỜI DÙNG GỬI FILE ---
@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def handle_incoming_files(message):
    try:
        file_name = "Không xác định"
        file_size = "Không xác định"
        
        # 1. Nếu là tệp tài liệu (Document)
        if message.content_type == 'document':
            file_name = message.document.file_name
            # Tính dung lượng file ra MB
            size_bytes = message.document.file_size
            file_size = f"{round(size_bytes / (1024 * 1024), 2)} MB" if size_bytes else "N/A"
            
        # 2. Nếu là hình ảnh (Photo)
        elif message.content_type == 'photo':
            file_name = f"Hinh_Anh_{message.photo[-1].file_id[:8]}.jpg"
            size_bytes = message.photo[-1].file_size
            file_size = f"{round(size_bytes / 1024, 2)} KB"
            
        # 3. Nếu là Audio/Video
        elif message.content_type in ['audio', 'video']:
            media = message.audio if message.content_type == 'audio' else message.video
            file_name = getattr(media, 'file_name', f"Media_{message.content_type}_{message.message_id}")
            size_bytes = media.file_size
            file_size = f"{round(size_bytes / (1024 * 1024), 2)} MB"

        # Lấy thông tin người gửi
        username = message.from_user.username or message.from_user.first_name
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Lưu vào Database
        save_file(date_str, username, file_name, file_size)
        
        # Phản hồi giống con bot check file chuyên nghiệp
        reply_msg = (
            f"✅ **CHECK FILE THÀNH CÔNG**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📂 **Tên File:** `{file_name}`\n"
            f"📦 **Dung lượng:** `{file_size}`\n"
            f"👤 **Người gửi:** @{username}\n"
            f"⏱ **Thời gian:** `{date_str}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 *Đã ghi nhận dữ liệu vào hệ thống!*"
        )
        bot.reply_to(message, reply_msg, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == '__main__':
    init_db()
    print("Bot MM88 Clone dang chay...")
    bot.infinity_polling()
