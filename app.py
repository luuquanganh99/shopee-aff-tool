import streamlit as st
from auth import register_user, login_user, get_all_users_for_admin, approve_user, reject_user
from supabase_client import supabase

st.set_page_config(page_title="AffBot", page_icon="🤖", layout="centered")

# ─── Session State ───────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ─── Hàm logout ──────────────────────────────────────────
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

    st.title(f"👋 Xin chào, {user['full_name']}!")
    st.caption(f"Gói hiện tại: **{user['plan'].upper()}**")

    if st.button("Đăng xuất"):
        logout()
        st.rerun()

    st.divider()

    # ── Kiểm tra token Threads đã có chưa ──
    existing = supabase.table("platforms").select("*").eq("user_id", user["id"]).eq("platform", "threads").execute()
    threads_connected = len(existing.data) > 0

    if threads_connected:
        st.success("✅ Threads đã kết nối thành công!")
        if st.button("🔄 Cập nhật token mới"):
            supabase.table("platforms").delete().eq("user_id", user["id"]).eq("platform", "threads").execute()
            st.rerun()
    else:
        st.warning("⚠️ Bạn chưa kết nối Threads. Làm theo hướng dẫn bên dưới.")

        with st.expander("📋 Hướng dẫn lấy Threads Token — Bấm để xem", expanded=True):
            st.markdown("""
### Bước 1 — Vào trang Graph API Explorer
👉 Truy cập: https://developers.facebook.com/tools/explorer/

---

### Bước 2 — Chọn đúng ứng dụng
- Nhìn góc trên bên phải, phần **"Meta App"**
- Chọn app **AFFShopee** trong danh sách

---

### Bước 3 — Chọn tài khoản Threads
- Phần **"User or Page"** → chọn tài khoản Threads của bạn
- Nếu không thấy tài khoản, nhờ admin thêm bạn vào danh sách thử nghiệm

---

### Bước 4 — Thêm quyền cần thiết
Nhấn **"Add a Permission"** và thêm lần lượt:
- ✅ `threads_basic`
- ✅ `threads_content_publish`

---

### Bước 5 — Lấy Access Token
- Nhấn nút **"Generate Access Token"** (màu xanh)
- Facebook sẽ hỏi xác nhận quyền → nhấn **"Đồng ý"**
- Copy toàn bộ chuỗi token xuất hiện (rất dài, khoảng 200 ký tự)

---

### Bước 6 — Dán token vào ô bên dưới ⬇️
""")

        st.subheader("🔗 Kết nối Threads")
        token_input = st.text_area(
            "Dán Threads Access Token vào đây:",
            height=120,
            placeholder="EAAxxxxxxxxx..."
        )

        if st.button("✅ Lưu và kết nối Threads", use_container_width=True):
            if not token_input.strip():
                st.error("❌ Bạn chưa điền token!")
            else:
                # Lưu token vào Supabase
                supabase.table("platforms").insert({
                    "user_id": user["id"],
                    "platform": "threads",
                    "access_token": token_input.strip(),
                    "is_active": True
                }).execute()
                st.success("🎉 Kết nối Threads thành công!")
                st.rerun()

    st.divider()
    st.info("🚧 Kết nối Instagram và Facebook sẽ có trong bản cập nhật tiếp theo!")