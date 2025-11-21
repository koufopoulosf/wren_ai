#!/usr/bin/env python3
"""
Generate comprehensive 2-year cryptocurrency seed data
Generates realistic OHLCV data, volumes, transactions, holdings, etc.
"""

from datetime import datetime, timedelta
import random
import math

# Date range: 2 years from today
END_DATE = datetime.now().date()
START_DATE = END_DATE - timedelta(days=730)

# Token starting prices (realistic as of late 2023)
TOKEN_PRICES = {
    1: 30000.0,    # BTC
    2: 1800.0,     # ETH
    3: 1.0,        # USDT
    4: 250.0,      # BNB
    5: 25.0,       # SOL
    6: 1.0,        # USDC
    7: 0.35,       # ADA
    8: 12.0,       # AVAX
    9: 4.5,        # DOT
    10: 0.60,      # MATIC
    11: 30000.0,   # WBTC
    12: 7.0,       # LINK
    13: 5.0,       # UNI
    14: 80.0,      # AAVE
    15: 1.0,       # DAI
    16: 0.80,      # ARB
    17: 1.20,      # OP
    18: 1800.0,    # WETH
    19: 0.000008,  # SHIB
    20: 1.80,      # APE
}

# Volatility factors (higher = more volatile)
VOLATILITY = {
    1: 0.02, 2: 0.025, 3: 0.0001, 4: 0.03, 5: 0.05,
    6: 0.0001, 7: 0.04, 8: 0.045, 9: 0.035, 10: 0.04,
    11: 0.02, 12: 0.04, 13: 0.045, 14: 0.05, 15: 0.0001,
    16: 0.06, 17: 0.055, 18: 0.025, 19: 0.08, 20: 0.07,
}

# Trading volumes (24h in tokens)
BASE_VOLUMES = {
    1: 30000, 2: 5000000, 3: 80000000000, 4: 2000000, 5: 8000000,
    6: 30000000000, 7: 1000000000, 8: 5000000, 9: 200000000, 10: 400000000,
    11: 2000, 12: 20000000, 13: 30000000, 14: 1000000, 15: 4000000000,
    16: 300000000, 17: 200000000, 18: 400000, 19: 8000000000000, 20: 100000000,
}

# Token metadata mapping
TOKEN_INFO = {
    1: ('BTC', 'Bitcoin', 'native', 1, 21000000, 19500000, 21000000, 8, '2009-01-03'),
    2: ('ETH', 'Ethereum', 'native', 1, None, 120000000, None, 18, '2015-07-30'),
    3: ('USDT', 'Tether', 'erc20', 1, None, 95000000000, None, 6, '2014-10-06'),
    4: ('BNB', 'Binance Coin', 'bep20', 2, 200000000, 150000000, 200000000, 18, '2017-07-01'),
    5: ('SOL', 'Solana', 'native', 3, None, 400000000, None, 9, '2020-03-16'),
    6: ('USDC', 'USD Coin', 'erc20', 1, None, 35000000000, None, 6, '2018-09-26'),
    7: ('ADA', 'Cardano', 'native', 4, 45000000000, 35000000000, 45000000000, 6, '2017-09-29'),
    8: ('AVAX', 'Avalanche', 'native', 5, 720000000, 350000000, 720000000, 18, '2020-09-21'),
    9: ('DOT', 'Polkadot', 'native', 6, None, 1200000000, None, 10, '2020-05-26'),
    10: ('MATIC', 'Polygon', 'erc20', 1, 10000000000, 9000000000, 10000000000, 18, '2019-05-31'),
    11: ('WBTC', 'Wrapped Bitcoin', 'erc20', 1, None, 150000, None, 8, '2019-01-31'),
    12: ('LINK', 'Chainlink', 'erc20', 1, 1000000000, 550000000, 1000000000, 18, '2017-09-19'),
    13: ('UNI', 'Uniswap', 'erc20', 1, 1000000000, 750000000, 1000000000, 18, '2020-09-17'),
    14: ('AAVE', 'Aave', 'erc20', 1, 16000000, 14500000, 16000000, 18, '2020-10-02'),
    15: ('DAI', 'Dai', 'erc20', 1, None, 4000000000, None, 18, '2017-12-27'),
    16: ('ARB', 'Arbitrum', 'native', 7, 10000000000, 1250000000, 10000000000, 18, '2023-03-23'),
    17: ('OP', 'Optimism', 'native', 8, 4294967296, 650000000, 4294967296, 18, '2022-05-31'),
    18: ('WETH', 'Wrapped Ether', 'erc20', 1, None, 3000000, None, 18, '2017-12-18'),
    19: ('SHIB', 'Shiba Inu', 'erc20', 1, 1000000000000000, 589000000000000, 1000000000000000, 18, '2020-08-01'),
    20: ('APE', 'ApeCoin', 'erc20', 1, 1000000000, 350000000, 1000000000, 18, '2022-03-17'),
}

# Blockchain information
BLOCKCHAINS = [
    (1, 'Ethereum', 'ETH', 1, 'PoS', 12, 'ETH', '2015-07-30'),
    (2, 'Binance Smart Chain', 'BNB', 56, 'PoSA', 3, 'BNB', '2020-09-01'),
    (3, 'Solana', 'SOL', None, 'PoH', 0.4, 'SOL', '2020-03-16'),
    (4, 'Cardano', 'ADA', None, 'PoS', 20, 'ADA', '2017-09-29'),
    (5, 'Avalanche', 'AVAX', 43114, 'PoS', 2, 'AVAX', '2020-09-21'),
    (6, 'Polkadot', 'DOT', None, 'NPoS', 6, 'DOT', '2020-05-26'),
    (7, 'Arbitrum', 'ARB', 42161, 'PoS', 0.25, 'ETH', '2021-08-31'),
    (8, 'Optimism', 'OP', 10, 'PoS', 2, 'ETH', '2021-12-16'),
]

# User information
USERS = [
    (1, 'whale_trader', 'whale@example.com', 'verified', 'institutional', 'US', 52000, 150000000.00),
    (2, 'hodl_master', 'hodl@example.com', 'verified', 'premium', 'GB', 850, 25000000.00),
    (3, 'defi_enthusiast', 'defi@example.com', 'verified', 'premium', 'DE', 12500, 8000000.00),
    (4, 'btc_maximalist', 'btc@example.com', 'verified', 'basic', 'CA', 320, 12000000.00),
    (5, 'eth_dev', 'eth@example.com', 'verified', 'premium', 'SG', 4200, 6000000.00),
    (6, 'altcoin_hunter', 'altcoin@example.com', 'verified', 'basic', 'AU', 8900, 2500000.00),
    (7, 'day_trader_pro', 'daytrader@example.com', 'verified', 'institutional', 'JP', 45000, 95000000.00),
    (8, 'staking_rewards', 'staking@example.com', 'verified', 'basic', 'NL', 1200, 850000.00),
]

def generate_blockchains_sql():
    """Generate blockchain base data"""
    print("-- =====================================================")
    print("-- BLOCKCHAINS (Base blockchain data)")
    print("-- =====================================================")
    print()
    print("INSERT INTO blockchains (blockchain_id, name, symbol, chain_id, consensus_mechanism, block_time_seconds, native_token, launched_date) VALUES")

    rows = []
    for blockchain_id, name, symbol, chain_id, consensus, block_time, native_token, launch_date in BLOCKCHAINS:
        chain_id_str = str(chain_id) if chain_id is not None else 'NULL'
        rows.append(f"({blockchain_id}, '{name}', '{symbol}', {chain_id_str}, '{consensus}', {block_time}, '{native_token}', '{launch_date}')")

    print(",\n".join(rows) + ";")
    print()

def generate_users_sql():
    """Generate user base data"""
    print("-- =====================================================")
    print("-- USERS (Platform users)")
    print("-- =====================================================")
    print()
    print("INSERT INTO users (user_id, username, email, kyc_status, account_tier, country_code, total_trades, total_volume_usd) VALUES")

    rows = []
    for user_id, username, email, kyc_status, account_tier, country, total_trades, total_volume in USERS:
        rows.append(f"({user_id}, '{username}', '{email}', '{kyc_status}', '{account_tier}', '{country}', {total_trades}, {total_volume})")

    print(",\n".join(rows) + ";")
    print()

def generate_tokens_sql():
    """Generate token base data"""
    print("-- =====================================================")
    print("-- TOKENS (20 major cryptocurrencies)")
    print("-- =====================================================")
    print()
    print("INSERT INTO tokens (token_id, code, name, ticker, blockchain_id, token_type, total_supply, circulating_supply, max_supply, decimals, launch_date) VALUES")

    rows = []
    for token_id in range(1, 21):
        ticker, name, token_type, blockchain_id, total_supply, circulating_supply, max_supply, decimals, launch_date = TOKEN_INFO[token_id]

        # Handle NULL values for unlimited supply
        total_supply_str = str(total_supply) if total_supply is not None else 'NULL'
        max_supply_str = str(max_supply) if max_supply is not None else 'NULL'

        rows.append(f"({token_id}, '{ticker.upper()}', '{name}', '{ticker.upper()}', {blockchain_id}, '{token_type}', {total_supply_str}, {circulating_supply}, {max_supply_str}, {decimals}, '{launch_date}')")

    print(",\n".join(rows) + ";")
    print()

def generate_ohlcv(token_id, date, prev_close):
    """Generate OHLCV data for a single day"""
    volatility = VOLATILITY[token_id]

    # Generate daily change (-vol to +vol)
    change = random.uniform(-volatility, volatility)
    close = prev_close * (1 + change)

    # Generate intraday high/low
    intraday_range = abs(change) * random.uniform(1.2, 2.0)
    high = close * (1 + intraday_range)
    low = close * (1 - intraday_range)
    open_price = prev_close * (1 + random.uniform(-volatility/2, volatility/2))

    # Ensure OHLC makes sense
    high = max(high, open_price, close)
    low = min(low, open_price, close)

    # Volume with some randomness
    base_vol = BASE_VOLUMES[token_id]
    volume = base_vol * random.uniform(0.7, 1.5)
    volume_usd = volume * close

    # Market cap (simplified)
    if token_id == 1:  # BTC
        market_cap = close * 19500000
    elif token_id == 2:  # ETH
        market_cap = close * 120000000
    elif token_id == 3:  # USDT
        market_cap = 95000000000
    elif token_id == 6:  # USDC
        market_cap = 35000000000
    else:
        market_cap = close * BASE_VOLUMES[token_id] * 10

    price_change_24h = (close - prev_close) / prev_close * 100

    return {
        'open': round(open_price, 8),
        'high': round(high, 8),
        'low': round(low, 8),
        'close': round(close, 8),
        'volume': round(volume, 2),
        'volume_usd': round(volume_usd, 2),
        'market_cap': round(market_cap, 2),
        'price_change_24h': round(price_change_24h, 4)
    }

def generate_price_history_sql():
    """Generate 2 years of daily OHLCV data for all tokens"""
    print("-- =====================================================")
    print("-- TOKEN PRICE HISTORY (2 years of daily data)")
    print("-- =====================================================")
    print()

    for token_id in range(1, 21):
        print(f"-- {['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'USDC', 'ADA', 'AVAX', 'DOT', 'MATIC', 'WBTC', 'LINK', 'UNI', 'AAVE', 'DAI', 'ARB', 'OP', 'WETH', 'SHIB', 'APE'][token_id-1]} price history")
        print(f"INSERT INTO token_price_history (token_id, timestamp, open_price, high_price, low_price, close_price, volume_24h, volume_24h_usd, market_cap, price_change_24h, interval) VALUES")

        current_price = TOKEN_PRICES[token_id]
        date = START_DATE
        rows = []

        while date <= END_DATE:
            data = generate_ohlcv(token_id, date, current_price)
            current_price = data['close']

            timestamp = date.strftime('%Y-%m-%d 00:00:00')
            row = f"({token_id}, '{timestamp}', {data['open']}, {data['high']}, {data['low']}, {data['close']}, {data['volume']}, {data['volume_usd']}, {data['market_cap']}, {data['price_change_24h']}, '1d')"
            rows.append(row)

            date += timedelta(days=1)

        # Print in batches of 100 to avoid too long lines
        for i in range(0, len(rows), 100):
            batch = rows[i:i+100]
            if i == 0:
                print(",\n".join(batch), end="")
            else:
                print(";\n")
                print(f"INSERT INTO token_price_history (token_id, timestamp, open_price, high_price, low_price, close_price, volume_24h, volume_24h_usd, market_cap, price_change_24h, interval) VALUES")
                print(",\n".join(batch), end="")
        print(";")
        print()

def generate_volume_data_sql():
    """Generate daily volume aggregates"""
    print("-- =====================================================")
    print("-- TOKEN VOLUME (2 years of daily volumes)")
    print("-- =====================================================")
    print()
    print("INSERT INTO token_volume (token_id, date, total_volume, total_volume_usd, buy_volume, sell_volume, trade_count, unique_traders, average_trade_size) VALUES")

    rows = []
    for token_id in range(1, 21):  # All tokens (1-20)
        date = START_DATE
        while date <= END_DATE:
            volume = BASE_VOLUMES[token_id] * random.uniform(0.8, 1.3)
            price = TOKEN_PRICES[token_id] * random.uniform(0.9, 1.1)
            volume_usd = volume * price
            buy_volume = volume * random.uniform(0.48, 0.52)
            sell_volume = volume - buy_volume
            trade_count = int(random.uniform(20000, 100000))
            unique_traders = int(trade_count * random.uniform(0.15, 0.25))
            avg_trade = volume / trade_count

            row = f"({token_id}, '{date}', {round(volume, 2)}, {round(volume_usd, 2)}, {round(buy_volume, 2)}, {round(sell_volume, 2)}, {trade_count}, {unique_traders}, {round(avg_trade, 4)})"
            rows.append(row)

            date += timedelta(days=1)

    print(",\n".join(rows) + ";")
    print()

def generate_revenue_data_sql():
    """Generate monthly revenue data"""
    print("-- =====================================================")
    print("-- TOKEN REVENUE (Monthly aggregates)")
    print("-- =====================================================")
    print()
    print("INSERT INTO token_revenue (token_id, date, revenue_type, amount, amount_usd, source, description) VALUES")

    rows = []
    date = START_DATE
    while date <= END_DATE:
        # Monthly data only (1st of each month)
        if date.day == 1:
            # ETH trading fees
            eth_amount = random.uniform(10000, 15000)
            eth_price = TOKEN_PRICES[2] * random.uniform(0.9, 1.1)
            rows.append(f"(2, '{date}', 'trading_fees', {round(eth_amount, 4)}, {round(eth_amount * eth_price, 2)}, 'Uniswap', 'Monthly trading fees from ETH pairs')")

            # ADA staking rewards
            ada_amount = random.uniform(800000, 1200000)
            ada_price = TOKEN_PRICES[7] * random.uniform(0.9, 1.1)
            rows.append(f"(7, '{date}', 'staking_rewards', {round(ada_amount, 2)}, {round(ada_amount * ada_price, 2)}, 'Cardano Network', 'Monthly ADA staking rewards')")

            # BNB burns (quarterly)
            if date.month in [1, 4, 7, 10]:
                bnb_amount = random.uniform(200, 300)
                bnb_price = TOKEN_PRICES[4] * random.uniform(0.9, 1.1)
                rows.append(f"(4, '{date}', 'burn', {round(bnb_amount, 4)}, {round(bnb_amount * bnb_price, 2)}, 'Binance', 'Quarterly BNB token burn')")

        date += timedelta(days=1)

    print(",\n".join(rows) + ";")
    print()

def generate_holdings_snapshots_sql():
    """Generate monthly holdings snapshots"""
    print("-- =====================================================")
    print("-- TOKEN HOLDINGS (Monthly snapshots)")
    print("-- =====================================================")
    print()
    print("INSERT INTO token_holdings (user_id, token_id, snapshot_date, total_balance, balance_usd, average_buy_price, unrealized_pnl, realized_pnl) VALUES")

    rows = []
    users = [1, 2, 3, 4, 5, 6, 7, 8]
    user_tokens = {
        1: [(2, 5234.56789012, 3500.00)],  # Whale - ETH
        2: [(1, 8.56789012, 82000.00)],     # HODL - BTC
        3: [(2, 890.12345678, 3600.00)],    # DeFi - ETH
        4: [(1, 3.45678901, 85000.00)],     # BTC Max - BTC
        5: [(2, 456.78901234, 3700.00)],    # ETH enthusiast
        6: [(5, 850.12345678, 135.00)],     # Altcoin - SOL
        7: [(2, 1234.56789012, 3500.00)],   # Day trader - ETH
        8: [(7, 95000.00, 0.50)],           # Staking - ADA
    }

    date = START_DATE
    while date <= END_DATE:
        if date.day == 1:  # Monthly snapshots
            for user_id in users:
                for token_id, balance, avg_buy in user_tokens[user_id]:
                    current_price = TOKEN_PRICES[token_id] * random.uniform(0.8, 2.0)  # Price varies over time
                    balance_usd = balance * current_price
                    unrealized_pnl = balance * (current_price - avg_buy)
                    realized_pnl = random.uniform(0, 50000)

                    rows.append(f"({user_id}, {token_id}, '{date}', {balance}, {round(balance_usd, 2)}, {avg_buy}, {round(unrealized_pnl, 2)}, {round(realized_pnl, 2)})")

        date += timedelta(days=1)

    print(",\n".join(rows) + ";")
    print()

if __name__ == "__main__":
    print("-- Cryptocurrency Database - 2 Year Historical Data")
    print("-- Generated:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("-- Date Range:", START_DATE, "to", END_DATE)
    print()

    # Generate base data first (required for foreign key constraints)
    generate_blockchains_sql()
    generate_users_sql()
    generate_tokens_sql()

    # Generate dependent data
    generate_price_history_sql()
    generate_volume_data_sql()
    generate_revenue_data_sql()
    generate_holdings_snapshots_sql()

    print("-- Data generation complete!")
    print(f"-- Total records: ~{8 + 8 + 20 + 730 * 20 + 730 * 20 + 24 * 3 + 24 * 8:,} (blockchains, users, tokens, price history, volume, revenue, holdings)")
