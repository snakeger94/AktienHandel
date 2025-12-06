"""
Universe Manager - Manages the expanded trading universe of stocks and cryptocurrencies.
"""

# Top S&P 500 stocks (representative sample of 100 most liquid)
SP500_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ',
    'XOM', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'LLY', 'ABBV', 'MRK',
    'AVGO', 'PEP', 'KO', 'COST', 'WMT', 'TMO', 'MCD', 'CSCO', 'ACN', 'ABT',
    'DHR', 'VZ', 'NEE', 'ADBE', 'CRM', 'NKE', 'TXN', 'PM', 'LIN', 'CMCSA',
    'UPS', 'RTX', 'HON', 'ORCL', 'INTC', 'QCOM', 'AMD', 'INTU', 'AMGN', 'COP',
    'UNP', 'BMY', 'LOW', 'BA', 'SBUX', 'GE', 'CAT', 'T', 'DE', 'SPGI',
    'AXP', 'BLK', 'IBM', 'GILD', 'MMM', 'ADI', 'MDLZ', 'ADP', 'TJX', 'SYK',
    'CVS', 'AMT', 'ISRG', 'BKNG', 'VRTX', 'CI', 'ZTS', 'PLD', 'C', 'TMUS',
    'MO', 'REGN', 'DUK', 'SO', 'MS', 'MMC', 'BDX', 'PNC', 'GS', 'CB',
    'EOG', 'SLB', 'USB', 'NOC', 'SCHW', 'FIS', 'ITW', 'EL', 'HCA', 'CL'
]

# NASDAQ-100 stocks (tech-heavy)
NASDAQ100_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST',
    'ASML', 'PEP', 'AZN', 'CSCO', 'ADBE', 'TMUS', 'CMCSA', 'AMD', 'NFLX', 'INTC',
    'TXN', 'INTU', 'QCOM', 'HON', 'AMGN', 'SBUX', 'AMAT', 'ISRG', 'BKNG', 'ADP',
    'GILD', 'ADI', 'VRTX', 'REGN', 'MDLZ', 'LRCX', 'MU', 'PYPL', 'PANW', 'CSX',
    'SNPS', 'CDNS', 'CHTR', 'MELI', 'KLAC', 'MAR', 'ABNB', 'ORLY', 'MNST', 'CRWD',
    'FTNT', 'ADSK', 'NXPI', 'AEP', 'WDAY', 'MRVL', 'DASH', 'KDP', 'CTAS', 'PAYX',
    'ROST', 'ODFL', 'PCAR', 'CPRT', 'FAST', 'KHC', 'EA', 'DXCM', 'CEG', 'GEHC',
    'CTSH', 'EXC', 'VRSK', 'LULU', 'XEL', 'IDXX', 'TEAM', 'CCEP', 'TTD', 'FANG',
    'CSGP', 'ANSS', 'ZS', 'DDOG', 'ON', 'TTWO', 'BIIB', 'WBD', 'ILMN', 'MDB',
    'GFS', 'CDW', 'MRNA', 'WBA', 'ARM', 'SMCI', 'DLTR', 'ZM', 'ALGN', 'RIVN'
]

# Major European stocks (DAX, FTSE)
EUROPEAN_STOCKS = [
    'SAP', 'ASML', 'SIE.DE', 'OR.PA', 'MC.PA', 'RMS.PA', 'ALV.DE', 'AI.PA',
    'SAN.PA', 'ITX.MC', 'IBE.MC', 'ABI.BR', 'SHEL', 'BP', 'VOD', 'GSK',
    'AZN', 'HSBA.L', 'RIO', 'ULVR.L', 'DGE.L', 'NG.L', 'BARC.L', 'LLOY.L'
]

# Major Cryptocurrencies (yfinance format with -USD suffix)
CRYPTOCURRENCIES = [
    'BTC-USD',   # Bitcoin
    'ETH-USD',   # Ethereum
    'BNB-USD',   # Binance Coin
    'XRP-USD',   # Ripple
    'ADA-USD',   # Cardano
    'SOL-USD',   # Solana
    'DOGE-USD',  # Dogecoin
    'MATIC-USD', # Polygon
    'DOT-USD',   # Polkadot
    'AVAX-USD',  # Avalanche
    'LINK-USD',  # Chainlink
    'UNI-USD',   # Uniswap
    'ATOM-USD',  # Cosmos
    'LTC-USD',   # Litecoin
    'XLM-USD',   # Stellar
]


class UniverseManager:
    """
    Manages the trading universe - stocks and cryptocurrencies.
    Provides filtering and categorization capabilities.
    """
    
    def __init__(self):
        self.sp500 = SP500_STOCKS
        self.nasdaq100 = NASDAQ100_STOCKS
        self.european = EUROPEAN_STOCKS
        self.crypto = CRYPTOCURRENCIES
    
    def get_universe(self, mode='all', enable_crypto=True, custom_list=None):
        """
        Get the trading universe based on configuration.
        
        Args:
            mode (str): Universe mode - 'all', 'sp500', 'nasdaq100', 'europe', 
                       'crypto', 'us_stocks', 'custom'
            enable_crypto (bool): Whether to include cryptocurrencies
            custom_list (list): Custom ticker list (used when mode='custom')
            
        Returns:
            dict: Dictionary with 'stocks' and 'crypto' lists
        """
        stocks = []
        crypto = []
        
        if mode == 'custom' and custom_list:
            # Use custom list
            stocks = [t for t in custom_list if not t.endswith('-USD')]
            crypto = [t for t in custom_list if t.endswith('-USD')]
        elif mode == 'sp500':
            stocks = self.sp500
        elif mode == 'nasdaq100':
            stocks = self.nasdaq100
        elif mode == 'europe':
            stocks = self.european
        elif mode == 'crypto':
            crypto = self.crypto if enable_crypto else []
        elif mode == 'us_stocks':
            # Combine SP500 and NASDAQ100, remove duplicates
            stocks = list(set(self.sp500 + self.nasdaq100))
        elif mode == 'all':
            # All stocks across all regions
            stocks = list(set(self.sp500 + self.nasdaq100 + self.european))
            crypto = self.crypto if enable_crypto else []
        else:
            # Default to US stocks
            stocks = list(set(self.sp500 + self.nasdaq100))
        
        # Add crypto if not already added and enabled
        if enable_crypto and not crypto and mode != 'crypto':
            crypto = self.crypto
        
        return {
            'stocks': sorted(stocks),
            'crypto': sorted(crypto) if enable_crypto else []
        }
    
    def get_total_count(self, mode='all', enable_crypto=True):
        """Get total count of tickers in the universe."""
        universe = self.get_universe(mode, enable_crypto)
        return len(universe['stocks']) + len(universe['crypto'])
    
    def is_crypto(self, ticker):
        """Check if a ticker is a cryptocurrency."""
        return ticker.endswith('-USD') or ticker in self.crypto
    
    def get_asset_type(self, ticker):
        """
        Determine asset type.
        
        Returns:
            str: 'crypto' or 'stock'
        """
        return 'crypto' if self.is_crypto(ticker) else 'stock'
