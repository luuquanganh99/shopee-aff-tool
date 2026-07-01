import requests, os, json
from dotenv import load_dotenv

load_dotenv()

APP_SECRET = "37273544a1e7fee04a68ea8b30afa7ce"

def refresh_token():
    token = os.getenv("THREADS_TOKEN")
    if not token:
        print("❌ Không tìm thấy token!")
        return

    print("🔄 Đang refresh token...")
    try:
        r = requests.get(
            "https://graph.threads.net/refresh_access_token",
            params={
                "grant_type": "th_refresh_token",
                "access_token": token
            },
            timeout=15
        )
        data = r.json()
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)

        if new_token:
            print(f"✅ Refresh thành công!")
            print(f"⏰ Token mới có hiệu lực: {expires_in // 86400} ngày")
            print(f"\nToken mới:\n{new_token}")

            # Cập nhật file .env
            with open(".env", "w") as f:
                f.write(f"THREADS_TOKEN={new_token}\n")
            print("\n✅ Đã cập nhật file .env!")
        else:
            print(f"❌ Lỗi: {data}")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    refresh_token()