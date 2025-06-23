# pesapal_client.py

import httpx
import uuid
from datetime import datetime, timezone
from lucopay.pesapal.config import (
    CONSUMER_KEY,
    CONSUMER_SECRET,
    TOKEN_URL,
    IPN_REGISTER_URL,
    SUBMIT_ORDER_URL,
    TRANSACTION_STATUS_URL,
    CALLBACK_BASE_URL
)

class PesapalClientError(Exception):
    """Custom exception for Pesapal API client errors."""
    def __init__(self, message, response_text=None):
        super().__init__(message)
        self.response_text = response_text

    def __str__(self):
        return f"{super().__str__()} - Details: {self.response_text}"

# A more robust in-memory cache for the access token (with expiry) and IPN ID
_cache = {
    "access_token": None,
    "access_token_expiry": None,
    "ipn_id": None
}

async def get_access_token() -> str:
    """
    Fetches a new access token from Pesapal if the cached one is invalid or expired.
    Raises an exception on failure.
    """
    # Check if a valid, non-expired token exists in the cache
    if _cache.get("access_token") and _cache.get("access_token_expiry"):
        if datetime.now(timezone.utc) < _cache["access_token_expiry"]:
            return _cache["access_token"]

    # If no valid token, fetch a new one
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"consumer_key": CONSUMER_KEY, "consumer_secret": CONSUMER_SECRET}

    async with httpx.AsyncClient() as client:
        try:
            print("Fetching new Pesapal access token...")
            resp = await client.post(TOKEN_URL, json=payload, headers=headers)
            resp.raise_for_status()
            
            data = resp.json()
            token = data.get("token")
            expiry_str = data.get("expiryDate")

            if not token or not expiry_str:
                raise PesapalClientError("Token or expiryDate not found in Pesapal response.", resp.text)

            # Pesapal expiry format can end in 'Z', which fromisoformat doesn't like before Python 3.11
            if expiry_str.endswith('Z'):
                expiry_str = expiry_str[:-1] + '+00:00'
            
            expiry_dt = datetime.fromisoformat(expiry_str)

            _cache["access_token"] = token
            _cache["access_token_expiry"] = expiry_dt
            print("Successfully fetched and cached new access token.")
            return token
        except httpx.HTTPStatusError as e:
            # If fetching a new token fails, clear the expired one from cache
            _cache["access_token"] = None
            _cache["access_token_expiry"] = None
            raise PesapalClientError(f"Failed to fetch access token from Pesapal: {e.response.status_code}", e.response.text)
        except (ValueError, KeyError) as e:
            # Handle potential parsing errors for the date or missing keys
            _cache["access_token"] = None
            _cache["access_token_expiry"] = None
            raise PesapalClientError(f"Error processing Pesapal token response: {e}", resp.text)

async def register_ipn_url() -> str:
    """Registers the application's IPN URL with Pesapal, raising an exception on failure."""
    if _cache["ipn_id"]:
        return _cache["ipn_id"]

    token = await get_access_token()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    ipn_webhook_url = f"{CALLBACK_BASE_URL}/ipn-webhook"
    payload = {"url": ipn_webhook_url, "ipn_notification_type": "POST"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(IPN_REGISTER_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            ipn_id = data.get("ipn_id")
            if not ipn_id:
                raise PesapalClientError("IPN ID not found in Pesapal response.", resp.text)
            
            _cache["ipn_id"] = ipn_id
            print(f"Successfully registered IPN URL: {data.get('url')} with ID: {ipn_id}")
            return ipn_id
        except httpx.HTTPStatusError as e:
            raise PesapalClientError("Failed to register IPN URL with Pesapal.", e.response.text)

async def submit_order(amount: float, email: str, phone: str, first_name: str, last_name: str) -> dict:
    """Submits a payment order to Pesapal, raising an exception on failure."""
    token = await get_access_token()
    ipn_id = await register_ipn_url() # Ensures IPN is registered before submitting

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # payment_callback_url = f"{CALLBACK_BASE_URL}/payment-callback"
    payment_callback_url = "https://lucosms-ui.vercel.app/topup"

    payload = {
        "id": str(uuid.uuid4()),
        "currency": "UGX",
        "amount": amount,
        "description": "Payment for Order",
        "callback_url": payment_callback_url,
        "notification_id": ipn_id,
        "billing_address": {
            "email_address": email,
            "phone_number": phone,
            "first_name": first_name,
            "last_name": last_name,
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(SUBMIT_ORDER_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise PesapalClientError("Failed to submit order to Pesapal.", e.response.text)

async def get_transaction_status(order_tracking_id: str) -> dict:
    """Gets the status of a specific transaction, raising an exception on failure."""
    token = await get_access_token()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    url = f"{TRANSACTION_STATUS_URL}?orderTrackingId={order_tracking_id}"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise PesapalClientError("Failed to get transaction status from Pesapal.", e.response.text)
