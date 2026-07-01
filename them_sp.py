import requests
from bs4 import BeautifulSoup
import json, re, os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

def chuan_hoa_link(link):
    # Trích shop_id và item_id từ link
    match = re.search(r'i\.(\d+)\.(\d+)', link)
    if match:
        shop_id, item_id = match.group(1), match.group(2)
        return f"https://shopee.vn/product/{shop_id}/{item_id}", shop_id, item_id
    
    match2 = re.search(r'product/(\d+)/(\d+)', link)
    if match2:
        shop_id, item_id = match2.group(1), match2.group(2)
        return f"https://shopee.vn/product/{shop_id}/{item_id}", shop_id, item_id
    
    return link, None, None

def lay_thong_tin(link):
    link_sach, shop_id, item_id = chuan_hoa_link(link)
    
    print(f"   🔍 Đang đọc trang sản phẩm...")
    
    try:
        # Cách 1: Đọc meta tags từ HTML
        r = requests.get(link_sach, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        
        # Lấy tên từ og:title
        ten = ""
        og_title = soup.find("meta", property="og:title")
        if og_title:
            ten = og_title.get("content", "").replace(" | Shopee Việt Nam", "").strip()
        if not ten:
            title = soup.find("title")
            if title:
                ten = title.text.replace("| Shopee Việt Nam", "").strip()

        # Lấy ảnh từ og:image
        anh_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            anh_url = og_image.get("content", "")

        # Lấy mô tả
        mo_ta = ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            mo_ta = og_desc.get("content", "")

        # Trích giá từ mô tả nếu có
        gia = "Xem tại link"
        gia_match = re.search(r'([\d,\.]+)\s*[₫đ]', mo_ta)
        if gia_match:
            gia = gia_match.group(1)

        # Cách 2: Thử API không cần đăng nhập
        if shop_id and item_id:
            try:
                api_url = f"https://shopee.vn/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
                headers_api = {**HEADERS, "X-API-SOURCE": "pc", "Referer": link_sach}
                r2 = requests.get(api_url, headers=headers_api, timeout=10)
                data = r2.json().get("data", {})
                
                if data:
                    ten_api = data.get("name", "")
                    if ten_api:
                        ten = ten_api
                    
                    gia_api = int(data.get("price_min", data.get("price", 0))) // 100000
                    if gia_api > 0:
                        gia = f"{gia_api:,}"
                    
                    giam = data.get("raw_discount", data.get("discount", 0))
                    luot_ban = data.get("sold", 0)
                    danh_gia = round(data.get("item_rating", {}).get("rating_star", 5.0), 1)
                    
                    images = data.get("images", [])
                    if images and not anh_url:
                        anh_url = f"https://down-vn.img.susercontent.com/file/{images[0]}"
                    
                    return {
                        "ten": ten[:100],
                        "gia": gia,
                        "giam": giam,
                        "luot_ban": luot_ban,
                        "danh_gia": danh_gia,
                        "anh_url": anh_url,
                        "link_goc": link_sach
                    }
            except:
                pass

        return {
            "ten": ten[:100] if ten else "Sản phẩm Shopee",
            "gia": gia,
            "giam": 0,
            "luot_ban": 0,
            "danh_gia": 5.0,
            "anh_url": anh_url,
            "link_goc": link_sach
        }

    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return None

def doc_products():
    if os.path.exists("products.json"):
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def luu_products(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def chay():
    print("="*50)
    print("🛍 THÊM SẢN PHẨM SHOPEE")
    print("="*50)
    print("Paste link Shopee vào đây (Enter để kết thúc)\n")

    products = doc_products()
    them_moi = 0

    while True:
        link = input("🔗 Link sản phẩm: ").strip()
        
        if not link:
            break
        
        if "shopee.vn" not in link:
            print("   ⚠ Không phải link Shopee, thử lại!\n")
            continue

        print(f"   ⏳ Đang lấy thông tin...")
        sp = lay_thong_tin(link)
        
        if not sp:
            print("   ❌ Không lấy được thông tin!\n")
            continue

        print(f"\n   ✅ Lấy được:")
        print(f"   📦 {sp['ten'][:55]}...")
        print(f"   💰 {sp['gia']}đ | 📉{sp['giam']}% | 👥{sp['luot_ban']:,} | ⭐{sp['danh_gia']}")
        print(f"   🖼 Ảnh: {'✓ Có' if sp['anh_url'] else '✗ Không có'}")

        xac_nhan = input("\n   Thêm sản phẩm này? (Enter=Có / n=Không): ").strip().lower()
        if xac_nhan != 'n':
            products.append(sp)
            luu_products(products)
            them_moi += 1
            print(f"   ✓ Đã thêm! Tổng: {len(products)} sản phẩm\n")
        else:
            print("   Bỏ qua.\n")

    print(f"\n🎉 Hoàn thành! Đã thêm {them_moi} sản phẩm mới")
    print(f"📦 Tổng kho: {len(products)} sản phẩm")
    print("👉 Chạy python main.py để đăng bài!")

if __name__ == "__main__":
    chay()