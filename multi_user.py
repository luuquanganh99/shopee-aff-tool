import json, os, time, random, re, requests, pandas as pd
from datetime import datetime
import io

USERS_FILE = "users.json"
LOG_FILE = "post_log.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_log(log):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def tao_caption_viral(sp):
    ten = sp.get("ten", "")[:70]
    gia = sp.get("gia", "Xem tại link")
    luot_ban = sp.get("luot_ban", 0)
    link = sp.get("link_aff", "")

    templates = [
        f"""🔥 Tại sao {luot_ban:,} người mua cái này mà mình không biết?? 😳

{ten}

Giá chỉ {gia}đ mà dùng xong là nghiền luôn 🤯

Link đây ai cần cứ lấy 👇
{link}

#shopee #deal #muasắm #giảmgiá""",

        f"""✨ Không ngờ cái này lại rẻ đến vậy...

{ten}

💰 Chỉ {gia}đ
👥 {luot_ban:,} người đã mua trước rồi

Ai cần thì đây 👇
{link}

#trending #shopee #hotdeal""",

        f"""💥 Hội chị em ơi cái này đang hot lắm!

{ten}

🏷️ {gia}đ thôi!
🛒 {luot_ban:,} đã mua

Link: {link}

#shopee #muanhanh #sale #giảmgiá""",

        f"""😱 Mình không tin giá lại rẻ thế này...

{ten}

⚡ Chỉ {gia}đ
✅ {luot_ban:,} người đã mua và hài lòng

Mua ngay kẻo hết 👇
{link}

#shopee #dealngon #muasắm""",

        f"""🎯 Tip tiết kiệm cho hội mua sắm online!

Đừng bỏ qua cái này nha:
{ten}

💸 Giá: {gia}đ
👥 {luot_ban:,} người mua rồi

Link mua 👉 {link}

#shopee #tipsmuasắm #deal"""
    ]
    return random.choice(templates)

def doc_san_pham_tu_csv(csv_content):
    san_pham = []
    try:
        df = pd.read_csv(io.StringIO(csv_content), header=None, encoding="utf-8-sig")
        for _, row in df.iterrows():
            try:
                cells = row.tolist()
                ten = str(cells[1]) if len(cells) > 1 else ""
                gia_goc = re.sub(r'[^\d]', '', str(cells[5]).replace('k','000'))
                gia = f"{int(gia_goc):,}" if gia_goc else "Xem tại link"
                luot_raw = str(cells[3]).replace('k+','000').replace('k','000')
                luot_ban = int(re.sub(r'[^\d]', '', luot_raw) or 0)
                hoa_hong_raw = re.sub(r'[^\d]', '', str(cells[4]))
                hoa_hong = int(hoa_hong_raw) if hoa_hong_raw else 0
                link_aff = str(cells[7]) if len(cells) > 7 else ""
                if ten and len(ten) > 3 and "shopee" in link_aff.lower():
                    san_pham.append({
                        "ten": ten[:100],
                        "gia": gia,
                        "luot_ban": luot_ban,
                        "hoa_hong": hoa_hong,
                        "link_aff": link_aff
                    })
            except:
                continue
    except Exception as e:
        print(f"   Lỗi đọc CSV: {e}")
    return san_pham

def dang_len_threads(token, caption):
    try:
        r1 = requests.post(
            "https://graph.threads.net/v1.0/me/threads",
            data={"media_type": "TEXT", "text": caption, "access_token": token},
            timeout=20
        )
        container_id = r1.json().get("id")
        if not container_id:
            return False, str(r1.json())
        time.sleep(3)
        r2 = requests.post(
            "https://graph.threads.net/v1.0/me/threads_publish",
            data={"creation_id": container_id, "access_token": token},
            timeout=15
        )
        if r2.json().get("id"):
            return True, "OK"
        return False, str(r2.json())
    except Exception as e:
        return False, str(e)

def chay_cho_user(username, udata, log):
    print(f"\n👤 Đang xử lý: {username}")

    # Kiểm tra tài khoản active
    if not udata.get("active"):
        print(f"   ⏭ Bỏ qua — tài khoản chưa kích hoạt")
        return

    token = udata.get("threads_token", "")
    csv_content = udata.get("csv_content", "")

    if not token:
        print(f"   ⏭ Bỏ qua — chưa có Threads Token")
        return

    if not csv_content:
        print(f"   ⏭ Bỏ qua — chưa có file CSV")
        return

    # Đọc sản phẩm
    san_pham = doc_san_pham_tu_csv(csv_content)
    if not san_pham:
        print(f"   ❌ Không đọc được sản phẩm!")
        return

    print(f"   ✓ Có {len(san_pham)} sản phẩm")

    # Chọn 3 sản phẩm hoa hồng cao
    sp_sorted = sorted(san_pham, key=lambda x: x["hoa_hong"], reverse=True)
    chon = random.sample(sp_sorted[:20], min(3, len(sp_sorted)))

    ok = 0
    for i, sp in enumerate(chon, 1):
        caption = tao_caption_viral(sp)
        success, msg = dang_len_threads(token, caption)
        if success:
            ok += 1
            print(f"   ✅ Bài {i}: {sp['ten'][:35]}...")
        else:
            print(f"   ❌ Bài {i} lỗi: {msg[:50]}")
        if i < len(chon):
            time.sleep(5)

    # Ghi log
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if username not in log:
        log[username] = []
    log[username].append({
        "time": now,
        "posts": ok,
        "total": len(chon)
    })

    print(f"   🎉 Xong! {ok}/{len(chon)} bài thành công")

def chay_tat_ca():
    print("🚀 AUTO AFFILIATE — MULTI USER\n" + "="*45)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    users = load_users()
    log = load_log()

    if not users:
        print("❌ Chưa có user nào!")
        return

    active_users = {k: v for k, v in users.items() if v.get("active")}
    print(f"👥 Tổng: {len(users)} user | Active: {len(active_users)} user\n")

    for username, udata in users.items():
        chay_cho_user(username, udata, log)
        time.sleep(2)

    save_log(log)
    print(f"\n✅ Hoàn thành tất cả!")

    # In báo cáo
    print("\n📊 BÁO CÁO HÔM NAY:")
    today = datetime.now().strftime("%Y-%m-%d")
    for uname, entries in log.items():
        today_posts = [e for e in entries if e["time"].startswith(today)]
        if today_posts:
            total_ok = sum(e["posts"] for e in today_posts)
            print(f"   {uname}: {total_ok} bài đăng thành công")

if __name__ == "__main__":
    chay_tat_ca()