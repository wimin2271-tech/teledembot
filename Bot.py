import telebot
import sqlite3
import threading
import http.server
import socketserver
import os
import datetime  # <-- Đã thêm khai báo bắt buộc này để sửa lỗi sập sớm

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
TOKEN = '8475285725:AAGfVc1XoJ9padzX6sOkcF8YXvicn3Zof0g' 
bot = telebot.TeleBot(TOKEN)

# --- CƠ SỞ DỮ LIỆU LƯU FILE THỰC TẾ ---
def init_db():
    conn = sqlite3.connect('xx88_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_date TEXT,       
            tg_time TEXT,       
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

# --- LỆNH XUẤT BÁO CÁO THEO TỪNG THÀNH VIÊN GIỐNG ẢNH MẪU ---
@bot.message_handler(commands=['group', 'thongke'])
def export_group_report(message):
    target_date = datetime.datetime.now().strftime("%Y-%m-%d")
    display_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    args = message.text.split()
    if len(args) >= 3:
        raw_date = args[2] 
        try:
            target_date = datetime.datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m-%d")
            display_date = raw_date
        except:
            pass

    conn = sqlite3.connect('xx88_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, file_name FROM file_logs WHERE tg_date = ? ORDER BY id ASC', (target_date,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.reply_to(message, f"📊 Không có dữ liệu file nào cho ngày {display_date}.")
        return

    user_files = {}
    total_files = len(rows)
    for username, file_name in rows:
        if username not in user_files:
            user_files[username] = []
        user_files[username].append(file_name)

    report = f"📊 **BÁO CÁO FILE NHÓM XX88**\n📅 Ngày {display_date}\n\n"
    
    for user, files in user_files.items():
        report += f"👤 @{user}: {len(files)} file\n"
        for f in files:
            report += f"- {f}\n"
        report += "\n" 
        
    report += f"✅ **Tổng XX88: {total_files} file**"
    bot.reply_to(message, report, parse_mode='Markdown')

# --- TỰ ĐỘNG LƯU FILE KHI THÀNH VIÊN GỬI VÀO NHÓM ---
@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def auto_log_file(message):
    try:
        file_name = "Không xác định"
        
        if message.content_type == 'document':
            file_name = message.document.file_name
        elif message.content_type == 'photo':
            file_name = f"XT6_{message.photo[-1].file_id[:4]}.png" 
        elif message.content_type in ['audio', 'video']:
            media = message.audio if message.content_type == 'audio' else message.video
            file_name = getattr(media, 'file_name', f"Media_{message.content_type}.mp4")

        username = message.from_user.username or message.from_user.first_name
        user_id = str(message.from_user.id)
        
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d") 
        time_str = now.strftime("%H:%M:%S")
        
        save_file(date_str, time_str, username, user_id, file_name)
        
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == '__main__':
    init_db()
    print("Bot XX88 Group Running...")
    bot.infinity_polling()
