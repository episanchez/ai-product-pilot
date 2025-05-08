from ai_product_pilot.core.settings import settings
from supabase import create_client

def get_supabase_client():
    return create_client(settings.supabase_url, settings.supabase_key)