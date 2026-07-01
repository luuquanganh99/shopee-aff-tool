import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Load .env từ đúng thư mục project
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("URL:", SUPABASE_URL)  # debug tạm thời
print("KEY:", SUPABASE_KEY[:20] if SUPABASE_KEY else None)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)