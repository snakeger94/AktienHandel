# Multi-Agent Stock & Crypto Trading System

An AI-powered paper trading system using Google Gemini or local Ollama for intelligent stock and cryptocurrency analysis and decision-making.

## 🚀 Features

- **Expanded Universe**: Analyze 170+ stocks (S&P 500 + NASDAQ-100) and 15 major cryptocurrencies
- **Intelligent Scanning**: Multi-stage filtering to identify top opportunities from hundreds of tickers
- **News Integration**: Real-time market sentiment analysis for informed decisions
- **Crypto Trading**: Full cryptocurrency support with separate risk management
- **AI-Powered**: Uses Gemini AI or local Ollama for analysis and trading decisions
- **Risk Management**: Different position limits for stocks (5%) vs crypto (3%)
- **Portfolio Tracking**: Tracks crypto vs stock allocation, enforces 20% max crypto limit
- **Benchmarking**: Compares performance against MSCI World index
- **Paper Trading**: Simulates trades without real money

## 📊 Trading Universe

- **170 Stocks**: Top companies from S&P 500 and NASDAQ-100
- **15 Cryptocurrencies**: BTC, ETH, BNB, XRP, ADA, SOL, DOGE, MATIC, DOT, AVAX, LINK, UNI, ATOM, LTC, XLM
- **Configurable**: Choose specific market segments (US, Europe, Crypto only)
- **Smart Filtering**: Automatically identifies top 30 candidates from the full universe

## 🛠️ Setup

### 1. Install Dependencies

```powershell
pip install yfinance pandas google-generativeai requests
```

### 2. Configure AI Provider

**Option A: Cloud AI (Google Gemini)**
1. Visit https://aistudio.google.com/app/apikey
2. Create a free API key
3. Open `config.py` and set:
```python
AI_PROVIDER = 'cloud'
GEMINI_API_KEY = "your-api-key-here"
```

**Option B: Local AI (Ollama)**
1. Install Ollama from https://ollama.ai/
2. Download model: `ollama pull gemma3:4b`
3. Keep default settings in `config.py`:
```python
AI_PROVIDER = 'local'
LOCAL_AI_MODEL = 'gemma3:4b'
```

### 3. (Optional) Configure News API

For real-time market news and sentiment:
1. Get free API key from https://newsapi.org/ (100 requests/day)
2. Open `config.py` and set:
```python
ENABLE_NEWS = True
NEWS_API_KEY = "your-newsapi-key-here"
```

### 4. Run the System

```powershell
python main.py
```

### 5. Test the System

```powershell
python test_system.py
```

## ⚙️ Configuration

Edit `config.py` to customize:

### Universe Selection
```python
UNIVERSE_MODE = 'us_stocks'  # Options: 'all', 'sp500', 'nasdaq100', 'us_stocks', 'europe', 'crypto', 'custom'
ENABLE_CRYPTO = True          # Enable/disable cryptocurrency trading
```

### Risk Management
```python
MAX_TRADES_PER_DAY = 5                  # Daily trade limit
MAX_POSITION_SIZE_PCT = 0.05            # Max 5% per stock position
MAX_CRYPTO_POSITION_SIZE_PCT = 0.03     # Max 3% per crypto position
MAX_CRYPTO_ALLOCATION_PCT = 0.20        # Max 20% total crypto allocation
```

### Market Filtering
```python
MIN_MARKET_CAP = 1_000_000_000  # Minimum $1B market cap
MIN_AVG_VOLUME = 100_000        # Minimum daily volume
TOP_CANDIDATES_COUNT = 30       # Max tickers to analyze deeply
```

### Portfolio Settings
```python
INITIAL_CASH = 10000.0  # Start with €10,000
```

## 📁 Output Files

- `data/portfolio.json`: Current holdings, cash, and crypto allocation
- `data/trade_log.csv`: Complete trade history
- `data/benchmark.json`: Performance vs MSCI World

## 🤖 AI Features

When AI is enabled (Gemini or Ollama):
- **News-Aware Trading**: AI considers recent news and sentiment
- **Crypto-Specific Analysis**: Different prompts for crypto vs stocks
- **Context-Aware**: AI knows your current portfolio and recent trades
- **Intelligent Signals**: BUY/SELL/HOLD decisions with confidence scores
- **Portfolio Guidance**: AI suggests aggressive/conservative/hold strategies

## 📈 How It Works

1. **Universe Scan**: Loads 185 tickers (170 stocks + 15 cryptos)
2. **Pre-Filtering**: Filters by market cap and volume (optional)
3. **Technical Screening**: Batch analyzes price data, momentum, moving averages
4. **Ranking**: Scores all candidates, selects top 30
5. **News Integration**: Fetches recent news and sentiment for each candidate
6. **AI Analysis**: AI evaluates each ticker with news context
7. **Risk Checks**: Enforces crypto limits and position sizing
8. **Execution**: Simulates trades and tracks performance

## 🎯 Example Workflows

### Trade only US stocks (no crypto)
```python
UNIVERSE_MODE = 'us_stocks'
ENABLE_CRYPTO = False
```

### Trade only cryptocurrencies
```python
UNIVERSE_MODE = 'crypto'
```

### Custom universe
```python
UNIVERSE_MODE = 'custom'
CUSTOM_UNIVERSE = ['AAPL', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD']
```

### Enable news integration
```python
ENABLE_NEWS = True
NEWS_API_KEY = "your-key-here"
```

## 🧪 Testing

The system includes a comprehensive test suite:

```powershell
python test_system.py
```

Tests verify:
- ✅ Universe manager (170 stocks + 15 cryptos)
- ✅ News fetcher and sentiment analysis
- ✅ Data loader (stocks and crypto)
- ✅ Market scanner initialization
- ✅ AI strategy with news integration
- ✅ Risk manager with crypto limits
- ✅ All configuration options

## 📊 Performance

- **Scan Time**: 2-5 minutes for full universe (185 tickers)
- **Analysis**: Top 30 candidates selected automatically
- **News**: Cached for 1 hour to minimize API calls
- **Benchmark**: MSCI World (URTH ETF) for performance comparison

## ⚠️ Disclaimer

**PAPER TRADING ONLY** - This system does not use real money. It is for educational and research purposes only. Do not use this as financial advice. Cryptocurrency and stock trading involve significant risk.

## 🔮 Advanced Features

### Multi-Stage Filtering
The scanner uses intelligent filtering to efficiently process large universes:
1. **Pre-filter**: Market cap and volume screening
2. **Technical**: Momentum and trend analysis (different for crypto)
3. **Ranking**: Score-based selection of top opportunities

### Crypto-Specific Features
- Higher volatility expectations
- Smaller position sizes (3% vs 5%)
- Portfolio allocation limit (20% max)
- Different AI analysis prompts
- 24/7 trading capability

### News-Driven Decisions
- Company/crypto-specific news
- Sentiment analysis (positive/negative/neutral)
- Integrated into AI prompts
- Recent headlines influence trading signals

## 🛡️ Risk Management

The system includes multiple layers of risk control:
- Daily trade limits
- Position size limits (different for crypto)
- Maximum crypto allocation (20%)
- Prevents re-buying recently sold positions
- Benchmark tracking (goal: outperform MSCI World)

## 🌐 Data Sources

- **Price Data**: Yahoo Finance (yfinance)
- **News** (Optional): NewsAPI
- **Benchmark**: MSCI World ETF (URTH)

## 📝 Logs & Monitoring

Each agent logs its actions:
- Market Scanner: Tickers scanned and candidates found
- Analyst: Technical metrics calculated
- AI Strategy: Trading signals with confidence
- Risk Manager: Trade approvals/rejections
- Portfolio Manager: Strategy guidance
- Execution: Trades executed

## 🤝 Contributing

This is an educational project. Feel free to fork and enhance!

## 📄 License

MIT License - Use at your own risk

---

**Version**: 2.0  
**Last Updated**: December 2025  
**Status**: Production-ready for paper trading
