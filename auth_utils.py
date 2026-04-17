import os
import requests
from jose import jwt, JWTError
from dotenv import load_dotenv
from fastapi import HTTPException, WebSocket

load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")

# Cache for public keys
_public_keys = None

def get_public_keys():
    """Fetch public keys from Keycloak's JWKS endpoint."""
    global _public_keys
    if _public_keys is None:
        try:
            url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            _public_keys = response.json()["keys"]
        except Exception as e:
            print(f"❌ Failed to fetch Keycloak public keys: {e}")
            return None
    return _public_keys

def verify_token(token: str):
    """Verify a JWT token against Keycloak's public keys."""
    if not token:
        return None
        
    keys = get_public_keys()
    if not keys:
        return None
        
    try:
        # Get the unverified header to find which key (kid) was used
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # Find the matching key
        key = next((k for k in keys if k["kid"] == kid), None)
        if not key:
            print(f"❌ No matching key found for kid: {kid}")
            return None
            
        # Verify the token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience="account", # Keycloak often uses 'account' or the client_id
            options={"verify_aud": False} # Set to True if you want to strictly match audience
        )
        return payload
    except JWTError as e:
        print(f"❌ Token verification failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in token verification: {e}")
        return None
