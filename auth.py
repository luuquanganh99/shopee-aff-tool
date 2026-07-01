import hashlib
import random
import os
import requests as http_requests
from datetime import datetime, timezone
from supabase_client import supabase

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def send_otp_email(email: str, code: str) -> bool:
    try:
        response = http_requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "AffBot <onboarding@resend.dev>",
                "to": [email],
                "subject": "Mã xác thực AffBot của bạn",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto;">
                    <h2 style="color: #FF6B35;">🤖 AffBot</h2>
                    <p>Xin chào! Đây là mã xác thực tài khoản của bạn:</p>
                    <div style="background: #f5f5f5; padding: 20px; text-align: center; border-radius: 8px;">
                        <h1 style="color: #FF6B35; letter-spacing: 8px;">{code}</h1>
                    </div>
                    <p>Mã có hiệu lực trong <strong>10 phút</strong>.</p>
                    <p style="color: #999; font-size: 12px;">Nếu bạn không đăng ký AffBot, hãy bỏ qua email này.</p>
                </div>
                """
            }
        )
        return response.status_code == 200
    except:
        return False

def register_user(email: str, password: str, full_name: str) -> dict:
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        return {"success": False, "message": "Email này đã được đăng ký."}

    # Tạo user chưa kích hoạt
    supabase.table("users").insert({
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "is_approved": False,
        "plan": "free"
    }).execute()

    # Tạo mã OTP 6 số
    code = str(random.randint(100000, 999999))

    # Xóa OTP cũ nếu có
    supabase.table("otp_codes").delete().eq("email", email).execute()

    # Lưu OTP mới
    supabase.table("otp_codes").insert({
        "email": email,
        "code": code,
        "is_used": False
    }).execute()

    # Gửi email
    sent = send_otp_email(email, code)
    if sent:
        return {"success": True, "message": "Đăng ký thành công! Kiểm tra email để lấy mã xác thực.", "need_otp": True, "email": email}
    else:
        return {"success": True, "message": "Đăng ký thành công! Nhưng gửi email thất bại — liên hệ admin.", "need_otp": False, "email": email}

def verify_otp(email: str, code: str):
    result = supabase.table("otp_codes").select("*").eq("email", email).eq("code", code).eq("is_used", False).execute()

    if not result.data:
        return {"success": False, "message": "Mã xác thực không đúng."}

    otp = result.data[0]

    # Kiểm tra hết hạn
    expires_at = datetime.fromisoformat(otp["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        return {"success": False, "message": "Mã xác thực đã hết hạn. Vui lòng đăng ký lại."}

    # Kích hoạt tài khoản
    supabase.table("users").update({"is_approved": True}).eq("email", email).execute()
    supabase.table("otp_codes").update({"is_used": True}).eq("id", otp["id"]).execute()

    return {"success": True, "message": "Xác thực thành công! Bạn có thể đăng nhập."}

def login_user(email: str, password: str) -> dict:
    result = supabase.table("users").select("*").eq("email", email).eq("password_hash", hash_password(password)).execute()

    if not result.data:
        return {"success": False, "message": "Email hoặc mật khẩu không đúng."}

    user = result.data[0]

    if not user["is_approved"]:
        return {"success": False, "message": "Tài khoản chưa xác thực email. Kiểm tra hộp thư của bạn."}

    return {"success": True, "user": user}

def get_all_users_for_admin() -> list:
    result = supabase.table("users").select("*").order("created_at", desc=True).execute()
    return result.data

def approve_user(user_id: str):
    supabase.table("users").update({"is_approved": True}).eq("id", user_id).execute()

def reject_user(user_id: str):
    supabase.table("users").delete().eq("id", user_id).execute()