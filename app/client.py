import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from env or streamlit secrets
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # We can handle this error gracefully in the UI, but for now let's just create a client that might fail if used
    # Or return None
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> Client:
    if supabase is None:
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in .env or .streamlit/secrets.toml")
        st.stop()
    return supabase
