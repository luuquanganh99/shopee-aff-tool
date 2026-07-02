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
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Mã xác thực AffBot của bạn"
        msg["From"] = f"AffBot <{GMAIL_USER}>"
        msg["To"] = email

        html = f"""
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

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, email, msg.as_string())
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False