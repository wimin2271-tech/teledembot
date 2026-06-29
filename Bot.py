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
            self.wfile.write(b"Bot is running!")

    # Render bắt buộc phải đọc được cổng từ os.environ này
    port = int(os.environ.get("PORT", 8080))
    
    # Cho phép chạy lại cổng nhanh mà không bị kẹt
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        print(f"Web server dang chay o cong {port}")
        httpd.serve_forever()

# Chạy kích hoạt Web Server trước
threading.Thread(target=run_web_server, daemon=True).start()

# --- CODE BOT TELEGRAM CỦA BẠN ---
TOKEN = '8475285725:AAGfVclXoJ9padzX6sOkcF8YXvicn3ZoF0g'
bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
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

# ... (Giữ nguyên phần đầu và phần khởi tạo database phía trên)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Bot đếm file đã sẵn sàng! Hãy gửi file vào đây.")

# ĐOẠN ĐƯỢC THÊM MỚI: Tự động bắt sự kiện khi người dùng gửi File (Tài liệu)
@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def handle_docs(message):
    try:
        # Lấy tên file (nếu là ảnh thì đặt tên mặc định)
        if message.content_type == 'document':
            file_name = message.document.file_name
        else:
            file_name = f"media_{message.content_type}_{message.message_id}"
            
        username = message.from_user.username or message.from_user.first_name
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Gọi hàm lưu vào database của bạn
        save_file(date_str, username, file_name)
        
        # Gửi lời nhắn đếm file lại cho bạn trên Telegram
        bot.reply_to(message, f"✅ Đã nhận và đếm thành công file: {file_name}\n👤 Người gửi: {username}")
        
    except Exception as e:
        bot.reply_to(message, f"Có lỗi xảy ra khi đếm file: {str(e)}")

if __name__ == '__main__':
    init_db()
    print("Bot dang chay...")
    bot.infinity_polling()

def save_file(date_str, username, file_name):
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO file_logs (tg_date, username, file_name) VALUES (?, ?, ?)', (date_str, username, file_name))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Bot dang chay...")
    # Giữ cho bot chạy vô tận
    bot.infinity_polling()
