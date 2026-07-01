import http.server
import urllib.parse
import requests
import webbrowser
import threading

APP_ID = "789322474057484"
APP_SECRET = "37273544a1e7fee04a68ea8b30afa7ce"
REDIRECT_URI = "http://localhost:8000"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Lấy code từ URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if "code" in params:
            code = params["code"][0]
            print(f"\n✓ Nhận được code: {code[:20]}...")
            
            # Đổi code → token
            r = requests.post("https://graph.threads.net/oauth/access_token", data={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code": code
            })
            data = r.json()
            short_token = data.get("access_token", "")
            
            # Đổi sang token dài hạn 60 ngày
            r2 = requests.get("https://graph.threads.net/access_token", params={
                "grant_type": "th_exchange_token",
                "client_secret": APP_SECRET,
                "access_token": short_token
            })
            long_token = r2.json().get("access_token", short_token)
            
            # Hiện kết quả
            print("\n" + "="*60)
            print("✅ TOKEN CỦA BẠN (copy dòng dưới vào file .env):")
            print("="*60)
            print(f"THREADS_TOKEN={long_token}")
            print("="*60)
            
            # Trả về trang thành công
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Thanh cong! Copy token trong VS Code terminal nhe!</h1>")
        else:
            self.send_response(200)
            self.end_headers()
        
        # Tắt server sau khi lấy xong
        threading.Thread(target=self.server.shutdown).start()
    
    def log_message(self, format, *args):
        pass  # Tắt log

# Mở trình duyệt tự động
auth_url = f"https://threads.net/oauth/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope=threads_basic,threads_content_publish&response_type=code"

print("🚀 Đang mở trình duyệt để đăng nhập Threads...")
print(f"Nếu trình duyệt không tự mở, dán link này vào:\n{auth_url}\n")

webbrowser.open(auth_url)

# Chạy server chờ nhận token
server = http.server.HTTPServer(("localhost", 8000), Handler)
print("⏳ Đang chờ bạn đăng nhập và cấp quyền...")
server.serve_forever()