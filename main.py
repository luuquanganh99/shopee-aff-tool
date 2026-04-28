import pandas as pd
import requests, os, time, random, re
from dotenv import load_dotenv

load_dotenv()
THREADS_TOKEN = os.getenv("THREADS_TOKEN")
CSV_FILE = "products_aff.csv"

def doc_san_pham():
    print("📂 Đang đọc file CSV...")
    try:
        df = pd.read_csv(CSV_FILE, header=None, encoding="utf-8-sig")
        san_pham = []
        for _, row in df.iterrows():
            try:
                cells = row.tolist()
                ten = str(cells[1]) if len(cells) > 1 else ""
                gia_raw = str(cells[2]) if len(cells) > 2 else "0"
                luot_ban_raw = str(cells[3]) if len(cells) > 3 else "0"
                hoa_hong_raw = str(cells[4]) if len(cells) > 4 else "0"
                gia_goc_raw = str(cells[5]) if len(cells) > 5 else "0"
                link_sp = str(cells[6]) if len(cells) > 6 else ""
                link_aff = str(cells[7]) if len(cells) > 7 else ""

                gia_num = re.sub(r'[^\d]', '', gia_goc_raw.replace('k','000'))
                gia = f"{int(gia_num):,}" if gia_num else "Xem tại link"

                luot_raw = luot_ban_raw.replace('k+','000').replace('k','000')
                luot_num = int(re.sub(r'[^\d]', '', luot_raw) or 0)

                hh = re.sub(r'[^\d]', '', hoa_hong_raw)
                hoa_hong = int(hh) if hh else 0

                if ten and len(ten) > 3 and "shopee" in link_aff.lower():
                    san_pham.append({
                        "ten": ten[:100],
                        "gia": gia,
                        "luot_ban": luot_num,
                        "hoa_hong": hoa_hong,
                        "anh_url": "",
                        "link_sp": link_sp,
                        "link_aff": link_aff
                    })
            except:
                continue
        print(f"   ✓ Đọc được {len(san_pham)} sản phẩm!")
        return san_pham
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return []

def lay_anh(link_sp):
    try:
        # Cách 1: Lấy từ og:image của trang sản phẩm
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        }
        r = requests.get(link_sp, headers=headers, timeout=10, allow_redirects=True)
        
        # Tìm og:image trong HTML
        match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https://[^"\']+)["\']', r.text)
        if match:
            return match.group(1)
        
        # Cách 2: Tìm ảnh susercontent trong HTML
        match2 = re.search(r'(https://down-vn\.img\.susercontent\.com/file/[a-z0-9]+)', r.text)
        if match2:
            return match2.group(1)
            
    except Exception as e:
        print(f"   ⚠ Lỗi ảnh: {e}")
    return ""

def phan_tich_san_pham(sp):
    ten = sp["ten"].lower()
    
    # Phân loại sản phẩm
    if any(x in ten for x in ["áo", "váy", "quần", "set", "đầm", "thun"]):
        loai = "thời trang"
        noi_dau = ["mặc đẹp mà không cần tốn nhiều tiền", 
                   "mặc gì cũng không ưng", 
                   "tủ đồ toàn đồ mà không có gì mặc"]
        ket_qua = ["mặc là được khen ngay", 
                   "tự tin hơn hẳn mỗi khi ra ngoài",
                   "bạn bè hỏi mua ở đâu liên tục"]
    elif any(x in ten for x in ["kem", "son", "serum", "mặt", "dưỡng", "chống nắng"]):
        loai = "làm đẹp"
        noi_dau = ["skincare mãi không thấy da đẹp lên",
                   "tốn tiền mua đồ mà da vẫn vậy",
                   "không biết dùng gì cho da mình"]
        ket_qua = ["da thay đổi rõ rệt sau 2 tuần",
                   "được hỏi bí quyết dưỡng da liên tục",
                   "tiết kiệm được cả triệu mỗi tháng"]
    elif any(x in ten for x in ["nước giặt", "nước xả", "vệ sinh", "tẩy"]):
        loai = "gia dụng"
        noi_dau = ["mãi không tìm được đồ gia dụng ưng ý",
                   "mua đồ không biết loại nào tốt",
                   "tốn tiền mà chất lượng không như mong đợi"]
        ket_qua = ["cả nhà đều thích",
                   "tiết kiệm được kha khá",
                   "dùng 1 lần là ghiền luôn"]
    elif any(x in ten for x in ["quạt", "đèn", "điều hòa", "điện"]):
        loai = "điện máy"
        noi_dau = ["mùa hè nóng không chịu nổi",
                   "điện máy giá cao mà không biết mua ở đâu uy tín",
                   "mua đồ điện tử không biết hàng nào tốt"]
        ket_qua = ["dùng mát lạnh cả nhà",
                   "tiết kiệm điện hơn hẳn",
                   "mua 1 lần dùng mãi"]
    else:
        loai = "hot trend"
        noi_dau = ["không biết mua gì trên Shopee cho đáng",
                   "toàn mua đồ về không dùng",
                   "muốn mua thứ gì đó thật sự hữu ích"]
        ket_qua = ["dùng xong là nghiện luôn",
                   "bạn bè ai cũng hỏi mua ở đâu",
                   "không ngờ giá lại rẻ thế này"]
    
    return loai, random.choice(noi_dau), random.choice(ket_qua)

def tao_caption_viral(sp):
    ten = sp["ten"][:60]
    gia = sp["gia"]
    luot_ban = sp.get("luot_ban", 0)
    link = sp["link_aff"]
    loai, noi_dau, ket_qua = phan_tich_san_pham(sp)

    templates = [
        # Template 1: Gây tò mò bằng câu hỏi
        f"""Tại sao {luot_ban:,} người mua cái này mà mình không biết?? 😳

Hôm qua lướt Shopee tình cờ thấy...

{ten}

Giá chỉ {gia}đ mà {ket_qua} 🤯

Thôi link đây ai cần cứ lấy 👇
{link}

#shopee #tiktokshopee #reviewsanpham #muasam""",

        # Template 2: Kể chuyện
        f"""Bạn thân mình cứ {noi_dau} mãi...

Mình mới tìm ra thứ này cho nó 👀

→ {ten}
→ Chỉ {gia}đ
→ {luot_ban:,} người đã mua trước rồi

Kết quả? {ket_qua} 😍

Link mua ở đây nè:
{link}

#shopee #review #cuocsong #muasam""",

        # Template 3: Gây sốc về giá
        f"""Không phải mình đang nói thật đâu nhé 😅

Cái này giá chỉ {gia}đ mà...

✅ {luot_ban:,} người đã mua
✅ {ket_qua}
✅ Ship nhanh tận nhà

{ten}

Ai cần thì đây 👇
{link}

#shopee #dealngon #surprising #muasam""",

        # Template 4: Đặt câu hỏi khơi gợi
        f"""Đố bạn đoán được cái này giá bao nhiêu? 🤔

👀 {ten}

Hint: Rẻ hơn 1 ly cà phê ngoài quán rất nhiều...

...

Đúng rồi, chỉ {gia}đ thôi! 😱
Mà {luot_ban:,} người đã mua rồi đó

Link đây cho ai cần:
{link}

#shopee #giatot #muasam #review""",

        # Template 5: FOMO
        f"""Hội chị em ơi cái này đang bán chạy lắm 😭

{ten}

💰 {gia}đ
🔥 {luot_ban:,} người đã mua
⚡ Còn hàng không biết đến khi nào

Mình vừa order rồi, ai nhanh thì theo link này:
{link}

#shopee #hottrend #muanhanh #chijemoi"""
    ]
    return random.choice(templates)

def dang_threads(sp):
    caption = tao_caption_viral(sp)
    anh_url = sp.get("anh_url", "")

    if not THREADS_TOKEN or THREADS_TOKEN == "điền_vào_sau":
        print("\n" + "="*55)
        print("📝 CAPTION VIRAL:")
        print(caption)
        print(f"🖼 Ảnh: {'✓ Có' if anh_url else '✗ Không'}")
        print("="*55 + "\n")
        return True

    try:
        payload = {
            "media_type": "IMAGE" if anh_url else "TEXT",
            "text": caption,
            "access_token": THREADS_TOKEN
        }
        if anh_url:
            payload["image_url"] = anh_url

        r1 = requests.post(
            "https://graph.threads.net/v1.0/me/threads",
            data=payload, timeout=20
        )
        container_id = r1.json().get("id")

        if not container_id:
            r1 = requests.post(
                "https://graph.threads.net/v1.0/me/threads",
                data={"media_type": "TEXT", "text": caption, "access_token": THREADS_TOKEN},
                timeout=15
            )
            container_id = r1.json().get("id")

        if not container_id:
            print(f"   ⚠ {r1.json()}")
            return False

        time.sleep(3)
        r2 = requests.post(
            "https://graph.threads.net/v1.0/me/threads_publish",
            data={"creation_id": container_id, "access_token": THREADS_TOKEN},
            timeout=15
        )
        return bool(r2.json().get("id"))

    except Exception as e:
        print(f"   Lỗi: {e}")
        return False

def chay():
    print("🚀 SHOPEE AFFILIATE TOOL — VIRAL EDITION\n" + "="*45)

    san_pham = doc_san_pham()
    if not san_pham:
        print("❌ Không đọc được sản phẩm!")
        return

    # Ưu tiên sản phẩm hoa hồng cao + bán chạy
    sp_sorted = sorted(san_pham,
        key=lambda x: (x["hoa_hong"] * 0.4 + min(x["luot_ban"]/1000, 10) * 0.6),
        reverse=True)
    
    chon = random.sample(sp_sorted[:15], min(3, len(sp_sorted)))

    print(f"\n📤 Chuẩn bị đăng {len(chon)} bài viral...\n")
    ok = 0

    for i, sp in enumerate(chon, 1):
        print(f"[{i}/3] {sp['ten'][:45]}...")
        print(f"   💰{sp['gia']}đ | 👥{sp['luot_ban']:,} | 🏷️HH:{sp['hoa_hong']}%")

        # Lấy ảnh sản phẩm
        if sp["link_sp"]:
            print(f"   📸 Đang lấy ảnh...")
            sp["anh_url"] = lay_anh(sp["link_sp"])
            print(f"   🖼 Ảnh: {'✓ Có' if sp['anh_url'] else '✗ Không lấy được'}")

        if dang_threads(sp):
            ok += 1
            print(f"   ✅ Đăng thành công!")
        else:
            print(f"   ❌ Thất bại!")

        if i < len(chon):
            time.sleep(5)

    print(f"\n🎉 Hoàn thành! {ok}/{len(chon)} bài đăng thành công")
    print("👉 Mở app Threads kiểm tra nhé!")

if __name__ == "__main__":
    chay()