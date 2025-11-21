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

    generate_price_history_sql()
    generate_volume_data_sql()
    generate_revenue_data_sql()
    generate_holdings_snapshots_sql()

    print("-- Data generation complete!")
    print(f"-- Total records generated: ~{730 * 20 + 730 * 20 + 24 * 3 + 24 * 8:,}")
