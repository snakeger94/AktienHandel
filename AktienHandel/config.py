import os

# Global Configuration

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PORTFOLIO_FILE = os.path.join(DATA_DIR, 'portfolio.json')
TRADE_LOG_FILE = os.path.join(DATA_DIR, 'trade_log.csv')
BENCHMARK_FILE = os.path.join(DATA_DIR, 'benchmark.json')

# ===== TRADING UNIVERSE CONFIGURATION =====
# Universe Mode Options:
# - 'all': All stocks + crypto (S&P500 + NASDAQ100 + European + Crypto)
# - 'sp500': S&P 500 stocks only
# - 'nasdaq100': NASDAQ-100 stocks only
# - 'us_stocks': Combined S&P500 + NASDAQ100 (no duplicates)
# - 'europe': Major European stocks (DAX, FTSE)
# - 'crypto': Cryptocurrencies only
# - 'custom': Use CUSTOM_UNIVERSE list below
UNIVERSE_MODE = 'us_stocks'  # <-- Change this to select your universe

# Custom universe (only used if UNIVERSE_MODE = 'custom')
CUSTOM_UNIVERSE = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'AMD', 'INTC', 'META', 'NFLX']

# Cryptocurrency Trading
ENABLE_CRYPTO = True  # Enable/disable cryptocurrency trading
MAX_CRYPTO_ALLOCATION_PCT = 0.20  # Max 20% of portfolio in crypto
MAX_CRYPTO_POSITION_SIZE_PCT = 0.03  # Max 3% per crypto position (more volatile)

# Market Filtering (to reduce scan time)
MIN_MARKET_CAP = 1_000_000_000  # Minimum $1B market cap (set to 0 to disable)
MIN_AVG_VOLUME = 100_000  # Minimum average daily volume (set to 0 to disable)
TOP_CANDIDATES_COUNT = 30  # Max number of stocks to analyze deeply after pre-filtering

# Risk Management Limits
MAX_TRADES_PER_DAY = 5
MAX_DRAWDOWN_PCT = 0.10  # Stop trading if portfolio is down 10%
MAX_POSITION_SIZE_PCT = 0.05  # Max 5% of portfolio per trade

# Simulation Settings
INITIAL_CASH = 10000.0  # Start with 10,000 EUR
PAPER_TRADING = True

# Data Settings
HISTORY_DAYS = 365  # Days of history to fetch for analysis

# Benchmark Settings
BENCHMARK_TICKER = 'URTH'  # MSCI World ETF for performance comparison

# AI Settings
USE_AI = True  # Enable/disable AI features

# AI Provider Selection
# Options: 'cloud' (Google Gemini) or 'local' (Ollama)
AI_PROVIDER = 'local'  # <-- Change to 'local' to use Ollama instead of cloud AI

# Cloud AI Settings (Gemini)
# Get your free API key from: https://aistudio.google.com/app/apikey
# Paste it here between the quotes:
GEMINI_API_KEY = "AIzaSyCmAJaWyg3TyuWkUzbkO6H1w8CvItUpC9Q"  # <-- Put your API key here
# You can also use environment variable if you prefer:
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Local AI Settings (Ollama)
# Note: Requires Ollama to be installed and running
# Install: https://ollama.ai/
# Download model: ollama pull gemma3:4b
LOCAL_AI_MODEL = 'gemma3:4b'  # Model name for Ollama
LOCAL_AI_URL = 'http://localhost:11434'  # Ollama API endpoint

# ===== NEWS & MARKET INTELLIGENCE =====
# News API Settings (for market news and sentiment)
# Get free API key from: https://newsapi.org/
# Free tier: 100 requests/day
ENABLE_NEWS = True  # Enable/disable news integration
NEWS_API_KEY = "7405212350cb44f8bc8fa75eb5f11bcd"  # <-- Put your NewsAPI key here (leave empty to disable)
# You can also use environment variable:
# NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

