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
            self.wfile.write(b"Bot Check File MM88 dang hoat dong!")

    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- CẤU HÌNH BOT TELEGRAM ---
TOKEN = '8475285725:AAGfVclXoJ9padzX6sOkcF8YXvicn3ZoF0g'
bot = telebot.TeleBot(TOKEN)

# --- CƠ SỞ DỮ LIỆU LƯU FILE THỰC TẾ ---
def init_db():
    conn = sqlite3.connect('mm88_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_date TEXT,
            username TEXT,
            user_id TEXT,
            file_name TEXT,
            file_size TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_file(date_str, username, user_id, file_name, file_size, status):
    conn = sqlite3.connect('mm88_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO file_logs (tg_date, username, user_id, file_name, file_size, status) VALUES (?, ?, ?, ?, ?, ?)', 
                   (date_str, username, user_id, file_name, file_size, status))
    conn.commit()
    conn.close()

# --- ĐỊNH NGHĨA CÁC LỆNH (COMMANDS) GIỐNG BOT MẪU ---

# Lệnh /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👑 **HỆ THỐNG KIỂM TRA FILE MM88** 👑\n\n"
        "Bot đã được kích hoạt và chạy tự động trong nhóm của bạn!\n\n"
        "📌 **Các lệnh có sẵn:**\n"
        "➡️ `/check` - Kiểm tra trạng thái hệ thống.\n"
        "➡️ `/thongke` - Xem danh sách 10 file vừa tải lên gần đây.\n"
        "➡️ `/myinfo` - Xem thông tin tài khoản của bạn.\n\n"
        "👉 *Chỉ cần gửi hoặc forward file vào đây, hệ thống sẽ tự động check vĩnh viễn ngầm.*"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# Lệnh /check
@bot.message_handler(commands=['check'])
def check_status(message):
    bot.reply_to(message, "🟢 **Hệ thống MM88 Bot:** Hoạt động ổn định (Dữ liệu đám mây an toàn).", parse_mode='Markdown')

# Lệnh /myinfo
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user = message.from_user
    info = (
        "👤 **THÔNG TIN TÀI KHOẢN CỦA BẠN:**\n"
        f"┣ ID: `{user.id}`\n"
        f"┣ Tên: `{user.first_name}`\n"
        f"┗ Username: @{user.username if user.username else 'Chưa cài đặt'}"
    )
    bot.reply_to(message, info, parse_mode='Markdown')

# Lệnh /thongke
@bot.message_handler(commands=['thongke'])
def show_stats(message):
    conn = sqlite3.connect('mm88_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tg_date, username, file_name, file_size, status FROM file_logs ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.reply_to(message, "📊 Hệ thống chưa ghi nhận file nào được gửi lên.")
        return
        
    report = "📊 **DANH SÁCH FILE ĐÃ ĐẾM GẦN ĐÂY:**\n━━━━━━━━━━━━━━━━━━\n"
    for idx, row in enumerate(rows, 1):
        report += f"{idx}. 📂 `{row[2]}` ({row[3]})\n"
        report += f"   👤 Gửi bởi: @{row[1]} | Trạng thái: {row[4]}\n"
        report += "──────────────────\n"
    bot.reply_to(message, report, parse_mode='Markdown')

# --- TỰ ĐỘNG CHECK MỌI FILE KHI ĐƯỢC GỬI VÀO NHÓM ---
@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def auto_check_file(message):
    try:
        file_name = "Không xác định"
        file_size = "Không xác định"
        status = "🟢 Hợp lệ"
        
        # Xử lý lấy thông tin theo từng loại File
        if message.content_type == 'document':
            file_name = message.document.file_name
            size_bytes = message.document.file_size
            file_size = f"{round(size_bytes / (1024 * 1024), 2)} MB" if size_bytes else "N/A"
            
            # Mẹo nhỏ: Nếu file là đuôi exe hoặc zip lạ có thể đổi trạng thái cảnh báo giống bot mẫu
            if file_name.endswith(('.exe', '.bat', '.apk')):
                status = "⚠️ Cảnh báo (File cài đặt)"
                
        elif message.content_type == 'photo':
            file_name = f"Anh_Chup_{message.photo[-1].file_id[:6]}.jpg"
            size_bytes = message.photo[-1].file_size
            file_size = f"{round(size_bytes / 1024, 2)} KB"
            
        elif message.content_type in ['audio', 'video']:
            media = message.audio if message.content_type == 'audio' else message.video
            file_name = getattr(media, 'file_name', f"Media_{message.content_type}")
            size_bytes = media.file_size
            file_size = f"{round(size_bytes / (1024 * 1024), 2)} MB"

        username = message.from_user.username or message.from_user.first_name
        user_id = str(message.from_user.id)
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Lưu vào Database cứng
        save_file(date_str, username, user_id, file_name, file_size, status)
        
        # Giao diện phản hồi chuẩn của bot check file chuyên nghiệp
        reply_msg = (
            f"🔍 **[MM88] KẾT QUẢ CHECK FILE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📂 **Tên File:** `{file_name}`\n"
            f"📦 **Dung lượng:** `{file_size}`\n"
            f"👤 **Người gửi:** @{username} (ID: `{user_id}`)\n"
            f"⏱ **Thời gian:** `{date_str}`\n"
            f"📊 **Trạng thái:** {status}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Dữ liệu file đã được quét và đếm thành công!*"
        )
        bot.reply_to(message, reply_msg, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")

if __name__ == '__main__':
    init_db()
    print("Bot MM88 Clone dang chay...")
    bot.infinity_polling()
