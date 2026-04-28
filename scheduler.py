import schedule
import time
import subprocess
import sys

def chay_tool():
    print("⏰ Đang chạy tool đăng bài...")
    subprocess.run([sys.executable, "main.py"])
    print("✅ Xong!\n")

# Lên lịch 3 khung giờ mỗi ngày
schedule.every().day.at("08:00").do(chay_tool)
schedule.every().day.at("16:00").do(chay_tool)
schedule.every().day.at("20:00").do(chay_tool)

print("🚀 Scheduler đang chạy...")
print("📅 Lịch đăng bài:")
print("   ⏰ 08:00 sáng")
print("   ⏰ 16:00 chiều")
print("   ⏰ 20:00 tối")
print("\nĐể dừng: nhấn Ctrl+C\n")

while True:
    schedule.run_pending()
    time.sleep(30)
