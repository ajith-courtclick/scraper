import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Settings
MYSQL_DATABASE = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'ecourts_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Scraping Settings
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

# Request Settings
REQUEST_TIMEOUT = 30
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Rate Limiting
RATE_LIMIT = {
    'min_time_between_requests': 1.0,  # seconds
    'max_requests_per_minute': 60
}

# Proxy Settings
PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'False').lower() == 'true'
PROXY_API_KEY = os.getenv('PROXY_API_KEY', '')

# Logging Settings
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scraper.log'

# Output Settings
OUTPUT_DIR = 'data'
EXPORT_FORMATS = ['csv', 'json']

# 2CAPTCHA API Keys
CAPTCHA_API_KEYS = [os.getenv('TWOCAPTCHA_API_KEY')]

# Ensure we have at least one valid API key
if not CAPTCHA_API_KEYS or not any(CAPTCHA_API_KEYS):
    raise ValueError("No 2CAPTCHA API keys configured. Please set TWOCAPTCHA_API_KEY in .env file") 