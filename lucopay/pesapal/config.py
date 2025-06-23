# config.py

# config.py

# Set your application environment: 'sandbox' or 'live'
APP_ENVIRONMENT = 'live'

# --- Pesapal Credentials ---
# IMPORTANT: Please ensure these are your PRODUCTION credentials for the 'live' environment.
CONSUMER_KEY = "BopfGlE7GfenAqGvS5SGdke4M67WLFxh"
CONSUMER_SECRET = "nnYh5QSFZUXRsQu6PQI4llLB5iU="

# --- Application URLs ---
# IMPORTANT: When you run ngrok, you must update this with your public URL.
# Example: "https://your-unique-id.ngrok-free.app"
CALLBACK_BASE_URL = "https://2477-41-210-146-229.ngrok-free.app"

# --- API Endpoints ---
# These are determined by the APP_ENVIRONMENT setting.
if APP_ENVIRONMENT == 'sandbox':
    BASE_API_URL = "https://cybqa.pesapal.com/pesapalv3/api"
else:
    BASE_API_URL = "https://pay.pesapal.com/v3/api"

TOKEN_URL = f"{BASE_API_URL}/Auth/RequestToken"
IPN_REGISTER_URL = f"{BASE_API_URL}/URLSetup/RegisterIPN"
IPN_LIST_URL = f"{BASE_API_URL}/URLSetup/GetIpnList"
SUBMIT_ORDER_URL = f"{BASE_API_URL}/Transactions/SubmitOrderRequest"
TRANSACTION_STATUS_URL = f"{BASE_API_URL}/Transactions/GetTransactionStatus"
