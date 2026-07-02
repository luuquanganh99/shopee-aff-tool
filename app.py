import streamlit as st
import os
import requests
from auth import register_user, login_user, verify_otp, get_all_users_for_admin, approve_user, reject_user
from supabase_client import supabase

st.set_page_config(page_title="AffBot", page_icon="🤖", layout="centered")

# ─── Threads OAuth Config ─────────────────────────────────
THREADS_APP_ID = os.getenv("THREADS_APP_ID")
THREADS_APP_SECRET = os.getenv("THREADS_APP_SECRET")
THREADS_REDIRECT_URI = os.getenv("THREADS_REDIRECT_URI")
FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")

def get_facebook_oauth_url(user_id):
    return (
        f"https://www.facebook.com/v18.0/dialog/oauth"
        f"?client_id={FB_APP_ID}"
        f"&redirect_uri={FB_REDIRECT_URI}"
        f"&scope=pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish"
        f"&response_type=code"
        f"&state=facebook|{user_id}"
    )

def exchange_fb_code_for_token(code):
    import urllib.parse
    response = requests.get(
        "https://graph.facebook.com/v18.0/oauth/access_token",
        params={
            "client_id": FB_APP_ID,
            "client_secret": FB_APP_SECRET,
            "redirect_uri": FB_REDIRECT_URI,
            "code": code,
        }
    )
    data = response.json()
    return data.get("access_token")

def get_pages_and_ig(access_token):
    response = requests.get(
        "https://graph.facebook.com/v18.0/me/accounts",
        params={
            "fields": "id,name,access_token,instagram_business_account",
            "access_token": access_token
        }
    )
    return response.json().get("data", [])

def get_threads_oauth_url(user_id):
    return (
        f"https://threads.net/oauth/authorize"
        f"?client_id={THREADS_APP_ID}"
        f"&redirect_uri={THREADS_REDIRECT_URI}"
        f"&scope=threads_basic,threads_content_publish"
        f"&response_type=code"
        f"&state=threads|{user_id}"
    )

def exchange_code_for_token(code):
    response = requests.post(
        "https://graph.threads.net/oauth/access_token",
        data={
            "client_id": THREADS_APP_ID,
            "client_secret": THREADS_APP_SECRET,
            "redirect_uri": THREADS_REDIRECT_URI,
            "code": code,
            "grant_type": "authorization_code",
        }
    )
    data = response.json()
    return data.get("access_token")

# ─── Session State ────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

def logout():
    st.session_state.user = None
    st.session_state.page = "login"

# ═══════════════════════════════════════════════════════════
# TRANG LOGIN / REGISTER
# ═══════════════════════════════════════════════════════════
if st.session_state.user is None:
    st.title("🤖 AffBot")
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])

    with tab1:
        st.subheader("Đăng nhập")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mật khẩu", type="password", key="login_pass")
        if st.button("Đăng nhập", use_container_width=True):
            result = login_user(email, password)
            if result["success"]:
                st.session_state.user = result["user"]
                st.session_state.page = "admin" if result["user"]["is_admin"] else "dashboard"
                st.rerun()
            else:
                st.error(result["message"])

    with tab2:
        st.subheader("Đăng ký tài khoản")

        if "otp_email" not in st.session_state:
            st.session_state.otp_email = None

        if st.session_state.otp_email:
            # Màn hình nhập OTP
            st.success(f"📧 Mã xác thực đã gửi đến **{st.session_state.otp_email}**")
            st.markdown("Kiểm tra hộp thư (kể cả thư mục Spam) và nhập mã 6 số bên dưới:")
            otp_input = st.text_input("Mã xác thực 6 số:", max_chars=6, key="otp_input")
            if st.button("✅ Xác thực", use_container_width=True):
                if len(otp_input) != 6:
                    st.error("Vui lòng nhập đủ 6 số.")
                else:
                    result = verify_otp(st.session_state.otp_email, otp_input)
                    if result["success"]:
                        st.success("🎉 Xác thực thành công! Bạn có thể đăng nhập ngay.")
                        st.session_state.otp_email = None
                    else:
                        st.error(result["message"])
            if st.button("Đăng ký lại với email khác"):
                st.session_state.otp_email = None
                st.rerun()
        else:
            # Form đăng ký
            full_name = st.text_input("Họ tên", key="reg_name")
            email_reg = st.text_input("Email", key="reg_email")
            password_reg = st.text_input("Mật khẩu", type="password", key="reg_pass")
            if st.button("Đăng ký", use_container_width=True):
                if not full_name or not email_reg or not password_reg:
                    st.warning("Vui lòng điền đầy đủ thông tin.")
                else:
                    result = register_user(email_reg, password_reg, full_name)
                    if result["success"]:
                        st.success(result["message"])
                        if result.get("need_otp"):
                            st.session_state.otp_email = result["email"]
                            st.rerun()
                    else:
                        st.error(result["message"])

# ═══════════════════════════════════════════════════════════
# TRANG ADMIN
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "admin":
    user = st.session_state.user
    st.title("🛠️ Admin Panel")
    st.caption(f"Đăng nhập với: {user['email']}")

    if st.button("Đăng xuất"):
        logout()
        st.rerun()

    st.divider()
    st.subheader("Danh sách người dùng")

    users = get_all_users_for_admin()
    for u in users:
        if u["is_admin"]:
            continue
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            status = "✅ Đã duyệt" if u["is_approved"] else "⏳ Chờ duyệt"
            st.write(f"**{u['full_name']}** — {u['email']} — {status} — Gói: {u['plan']}")
        with col2:
            if not u["is_approved"]:
                if st.button("Duyệt", key=f"approve_{u['id']}"):
                    approve_user(u["id"])
                    st.rerun()
        with col3:
            if st.button("Xóa", key=f"reject_{u['id']}"):
                reject_user(u["id"])
                st.rerun()

# ═══════════════════════════════════════════════════════════
# TRANG DASHBOARD USER
# ═══════════════════════════════════════════════════════════
elif st.session_state.page == "dashboard":
    user = st.session_state.user

    # Xử lý OAuth callback
    query_params = st.query_params
    query_params = st.query_params
    if "code" in query_params and "state" in query_params:
        code = query_params["code"]
        state = query_params["state"]
        platform = state.split("|")[0] if "|" in state else ""

        if platform == "threads":
            with st.spinner("Đang kết nối Threads..."):
                token = exchange_code_for_token(code)
                if token:
                    supabase.table("platforms").delete().eq("user_id", user["id"]).eq("platform", "threads").execute()
                    supabase.table("platforms").insert({
                        "user_id": user["id"],
                        "platform": "threads",
                        "access_token": token,
                        "is_active": True
                    }).execute()
                    st.query_params.clear()
                    st.success("🎉 Kết nối Threads thành công!")
                    st.rerun()
                else:
                    st.error("❌ Kết nối thất bại. Thử lại nhé!")
                    st.query_params.clear()

        elif platform == "facebook":
            with st.spinner("Đang kết nối Facebook & Instagram..."):
                token = exchange_fb_code_for_token(code)
                if token:
                    pages = get_pages_and_ig(token)
                    saved = 0
                    for page in pages:
                        # Lưu Facebook Fanpage token
                        supabase.table("platforms").delete().eq("user_id", user["id"]).eq("platform", "facebook").eq("page_id", page["id"]).execute()
                        supabase.table("platforms").insert({
                            "user_id": user["id"],
                            "platform": "facebook",
                            "access_token": page["access_token"],
                            "page_id": page["id"],
                            "is_active": True
                        }).execute()
                        saved += 1
                        # Lưu Instagram nếu có
                        ig = page.get("instagram_business_account")
                        if ig:
                            supabase.table("platforms").delete().eq("user_id", user["id"]).eq("platform", "instagram").execute()
                            supabase.table("platforms").insert({
                                "user_id": user["id"],
                                "platform": "instagram",
                                "access_token": page["access_token"],
                                "page_id": ig["id"],
                                "is_active": True
                            }).execute()
                    st.query_params.clear()
                    st.success(f"🎉 Đã kết nối {saved} Facebook Fanpage và Instagram!")
                    st.rerun()
                else:
                    st.error("❌ Kết nối thất bại. Thử lại nhé!")
                    st.query_params.clear()

    st.title(f"👋 Xin chào, {user['full_name']}!")
    st.caption(f"Gói hiện tại: **{user['plan'].upper()}**")

    if st.button("Đăng xuất"):
        logout()
        st.rerun()

    st.divider()

    existing = supabase.table("platforms").select("*").eq("user_id", user["id"]).eq("platform", "threads").execute()
    threads_connected = len(existing.data) > 0

    if threads_connected:
        st.success("✅ Threads đã kết nối thành công!")
        if st.button("🔄 Kết nối lại token mới"):
            supabase.table("platforms").delete().eq("user_id", user["id"]).eq("platform", "threads").execute()
            st.rerun()
    else:
        st.warning("⚠️ Bạn chưa kết nối Threads.")
        st.markdown("### 🔗 Kết nối Threads")
        st.markdown("Nhấn nút bên dưới — bạn sẽ được chuyển sang trang Meta để đăng nhập và xác nhận quyền. Chỉ mất 30 giây!")
        oauth_url = get_threads_oauth_url(user["id"])
        st.link_button("🚀 Kết nối Threads ngay", oauth_url, use_container_width=True)

    st.divider()

    # ─── Upload CSV sản phẩm ─────────────────────────────
    st.subheader("📦 Sản phẩm Shopee Affiliate")

    existing_products = supabase.table("products").select("*").eq("user_id", user["id"]).execute()
    product_count = len(existing_products.data)

    if product_count > 0:
        st.success(f"✅ Đã có {product_count} sản phẩm trong hệ thống.")
        if st.button("🗑️ Xóa và upload lại"):
            supabase.table("products").delete().eq("user_id", user["id"]).execute()
            st.rerun()
    else:
        with st.expander("📋 Hướng dẫn lấy file CSV — Bấm để xem", expanded=True):
            st.markdown("""
### Bước 1 — Vào Shopee Affiliate
👉 Truy cập: https://affiliate.shopee.vn

---

### Bước 2 — Vào mục Sản phẩm
- Nhấn **"Sản phẩm"** trên menu trên cùng
- Chọn **"Danh sách sản phẩm"**

---

### Bước 3 — Lọc sản phẩm hoa hồng cao
- Sắp xếp theo **"Hoa hồng"** từ cao đến thấp
- Chọn những sản phẩm muốn đăng

---

### Bước 4 — Xuất file CSV
- Nhấn nút **"Xuất"** hoặc **"Export"**
- Tải file CSV về máy

---

### Bước 5 — Upload file CSV bên dưới ⬇️
""")

        uploaded_file = st.file_uploader("Chọn file CSV sản phẩm Shopee Affiliate", type=["csv"])

        if uploaded_file:
            import pandas as pd
            import io
            df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode("utf-8")))
            st.dataframe(df.head(5))

            # Tự động detect cột
            col_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if "tên" in col_lower or "name" in col_lower or "product" in col_lower:
                    col_map["name"] = col
                if "link" in col_lower or "url" in col_lower or "affiliate" in col_lower:
                    col_map["link"] = col
                if "hoa hồng" in col_lower or "commission" in col_lower or "%" in col_lower:
                    col_map["commission"] = col
                if "giá" in col_lower or "price" in col_lower:
                    col_map["price"] = col
                if "ảnh" in col_lower or "image" in col_lower or "hình" in col_lower:
                    col_map["image"] = col

            if st.button("✅ Lưu sản phẩm vào hệ thống", use_container_width=True):
                products_to_insert = []
                for _, row in df.iterrows():
                    products_to_insert.append({
                        "user_id": user["id"],
                        "product_name": str(row.get(col_map.get("name", df.columns[0]), "")),
                        "affiliate_link": str(row.get(col_map.get("link", ""), "")),
                        "commission_rate": float(str(row.get(col_map.get("commission", ""), 0)).replace("%","").replace(",",".") or 0),
                        "price": float(str(row.get(col_map.get("price", ""), 0)).replace(",","").replace(".","") or 0),
                        "image_url": str(row.get(col_map.get("image", ""), "")),
                    })
                supabase.table("products").insert(products_to_insert).execute()
                st.success(f"🎉 Đã lưu {len(products_to_insert)} sản phẩm!")
                st.rerun()

    st.divider()

    # ─── Chọn khung giờ đăng ─────────────────────────────
    st.subheader("⏰ Khung giờ đăng bài")

    if threads_connected:
        existing_schedules = supabase.table("schedules").select("*").eq("user_id", user["id"]).eq("platform", "threads").execute()
        saved_hours = [s["hour"] for s in existing_schedules.data]

        st.markdown("Chọn các giờ bạn muốn đăng bài mỗi ngày (giờ Việt Nam):")

        all_hours = list(range(6, 23))
        selected_hours = st.multiselect(
            "Chọn khung giờ:",
            options=all_hours,
            default=saved_hours if saved_hours else [7, 12, 20],
            format_func=lambda h: f"{h}:00"
        )

        if st.button("💾 Lưu khung giờ", use_container_width=True):
            supabase.table("schedules").delete().eq("user_id", user["id"]).eq("platform", "threads").execute()
            for h in selected_hours:
                supabase.table("schedules").insert({
                    "user_id": user["id"],
                    "platform": "threads",
                    "hour": h,
                    "is_active": True
                }).execute()
            st.success(f"✅ Đã lưu {len(selected_hours)} khung giờ đăng!")
    else:
        st.warning("⚠️ Kết nối Threads trước để chọn khung giờ đăng.")

    st.divider()
    st.info("🚧 Kết nối Instagram và Facebook sẽ có trong bản cập nhật tiếp theo!")