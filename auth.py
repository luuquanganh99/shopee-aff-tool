import hashlib
from supabase_client import supabase

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email: str, password: str, full_name: str) -> dict:
    # Kiểm tra email đã tồn tại chưa
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        return {"success": False, "message": "Email này đã được đăng ký."}
    
    result = supabase.table("users").insert({
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "is_approved": False,
        "plan": "free"
    }).execute()
    
    return {"success": True, "message": "Đăng ký thành công! Chờ admin duyệt tài khoản."}

def login_user(email: str, password: str) -> dict:
    result = supabase.table("users").select("*").eq("email", email).eq("password_hash", hash_password(password)).execute()
    
    if not result.data:
        return {"success": False, "message": "Email hoặc mật khẩu không đúng."}
    
    user = result.data[0]
    
    if not user["is_approved"]:
        return {"success": False, "message": "Tài khoản chưa được admin duyệt."}
    
    return {"success": True, "user": user}

def get_all_users_for_admin() -> list:
    result = supabase.table("users").select("*").order("created_at", desc=True).execute()
    return result.data

def approve_user(user_id: str):
    supabase.table("users").update({"is_approved": True}).eq("id", user_id).execute()

def reject_user(user_id: str):
    supabase.table("users").delete().eq("id", user_id).execute()