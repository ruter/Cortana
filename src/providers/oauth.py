import time
import json
from typing import Optional, Dict, Any
from .base import OAuthCredentials
from ..database import db

# Ported from pi-mono ai package logic

async def get_stored_credentials(user_id: int, provider_id: str) -> Optional[OAuthCredentials]:
    """Retrieve stored OAuth credentials from Supabase."""
    try:
        response = db.table("provider_credentials") \
            .select("credentials") \
            .eq("user_id", user_id) \
            .eq("provider_id", provider_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            creds_data = response.data[0]["credentials"]
            return OAuthCredentials(**creds_data)
    except Exception as e:
        print(f"Error retrieving credentials for {user_id} ({provider_id}): {e}")
    return None

async def store_credentials(user_id: int, provider_id: str, credentials: OAuthCredentials):
    """Store OAuth credentials in Supabase."""
    try:
        data = {
            "user_id": user_id,
            "provider_id": provider_id,
            "credentials": credentials.model_dump(),
            "updated_at": "now()"
        }
        
        # Upsert credentials
        db.table("provider_credentials").upsert(data).execute()
    except Exception as e:
        print(f"Error storing credentials for {user_id} ({provider_id}): {e}")

async def get_valid_access_token(user_id: int, provider_id: str, provider_impl: Any) -> Optional[str]:
    """Get a valid access token, refreshing it if expired."""
    creds = await get_stored_credentials(user_id, provider_id)
    if not creds:
        return None

    # Check if expired (with 5 min buffer)
    current_time_ms = int(time.time() * 1000)
    if current_time_ms >= (creds.expires - 5 * 60 * 1000):
        try:
            print(f"Refreshing token for {user_id} ({provider_id})...")
            new_creds = await provider_impl.refresh_token(creds)
            await store_credentials(user_id, provider_id, new_creds)
            return new_creds.access
        except Exception as e:
            print(f"Failed to refresh token for {user_id} ({provider_id}): {e}")
            return None
    
    return creds.access
