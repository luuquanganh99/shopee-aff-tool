import os
import requests
import random
from supabase_client import supabase
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

VIETNAM_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

CAPTIONS = [
    "🔥 Sản phẩm HOT hôm nay: {name}\n💰 Hoa hồng lên đến {commission}%\n👉 Mua ngay: {link}\n#shopee #affiliate #muasam",
    "✨ Đừng bỏ lỡ! {name}\n🎯 Hoa hồng {commission}% - Cực hấp dẫn!\n🛒 Order ngay: {link}\n#dealhot #shopee #tietkiem",
    "💥 Deal của ngày: {name}\n⚡ Hoa hồng {commission}%\n📦 Đặt hàng: {link}\n#deal #shopee #muasamonline",
    "🛍️ Gợi ý mua sắm hôm nay!\n📌 {name}\n💵 Hoa hồng {commission}%\n👇 Link mua: {link}\n#gợiý #shopee #affiliate",
    "🌟 Sản phẩm chất lượng cao!\n🏷️ {name}\n💎 Hoa hồng {commission}%\n🔗 Xem ngay: {link}\n#chatluong #shopee #muasam",
]

def post_to_threads(token: str, text: str) -> bool:
    try:
        # Lấy user ID
        me = requests.get(
            "https://graph.threads.net/v1.0/me",
            params={"fields": "id", "access_token": token}
        ).json()
        user_id = me.get("id")
        if not user_id:
            return False

        # Tạo container
        container = requests.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads",
            params={
                "media_type": "TEXT",
                "text": text,
                "access_token": token
            }
        ).json()
        container_id = container.get("id")
        if not container_id:
            return False

        # Publish
        result = requests.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": token
            }
        ).json()
        return "id" in result
    except:
        return False

def run_scheduler():
    now = datetime.now(VIETNAM_TZ)
    current_hour = now.hour
    print(f"[{now.strftime('%H:%M %d/%m/%Y')}] Đang kiểm tra lịch đăng...")

    # Lấy tất cả user có lịch đăng giờ này
    schedules = supabase.table("schedules").select("*").eq("platform", "threads").eq("hour", current_hour).eq("is_active", True).execute()

    if not schedules.data:
        print("Không có user nào cần đăng bài giờ này.")
        return

    for schedule in schedules.data:
        user_id = schedule["user_id"]
        print(f"Xử lý user: {user_id}")

        # Lấy token Threads
        platform = supabase.table("platforms").select("*").eq("user_id", user_id).eq("platform", "threads").eq("is_active", True).execute()
        if not platform.data:
            print(f"  ❌ Không có token Threads")
            continue
        token = platform.data[0]["access_token"]

        # Lấy sản phẩm ngẫu nhiên
        products = supabase.table("products").select("*").eq("user_id", user_id).execute()
        if not products.data:
            print(f"  ❌ Không có sản phẩm")
            continue

        product = random.choice(products.data)
        caption_template = random.choice(CAPTIONS)
        text = caption_template.format(
            name=product.get("product_name", "Sản phẩm hot"),
            commission=product.get("commission_rate", ""),
            link=product.get("affiliate_link", ""),
        )

        # Đăng bài
        success = post_to_threads(token, text)
        if success:
            print(f"  ✅ Đã đăng bài cho user {user_id}")
        else:
            print(f"  ❌ Đăng thất bại cho user {user_id}")

if __name__ == "__main__":
    run_scheduler()