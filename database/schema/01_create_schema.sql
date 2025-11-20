-- Cryptocurrency Analytics Database Schema
-- Comprehensive schema for crypto trading platform with token data, holdings, volume, and revenue
-- Supports OHLCV data, wallet management, trading pairs, and advanced analytics

-- Drop all existing tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS token_revenue CASCADE;
DROP TABLE IF EXISTS token_holdings CASCADE;
DROP TABLE IF EXISTS token_volume CASCADE;
DROP TABLE IF EXISTS token_price_history CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS wallet_balances CASCADE;
DROP TABLE IF EXISTS wallets CASCADE;
DROP TABLE IF EXISTS trading_pairs CASCADE;
DROP TABLE IF EXISTS exchange_listings CASCADE;
DROP TABLE IF EXISTS exchanges CASCADE;
DROP TABLE IF EXISTS staking_records CASCADE;
DROP TABLE IF EXISTS liquidity_pools CASCADE;
DROP TABLE IF EXISTS token_metadata CASCADE;
DROP TABLE IF EXISTS tokens CASCADE;
DROP TABLE IF EXISTS blockchains CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =====================================================
-- CORE INFRASTRUCTURE TABLES
-- =====================================================

-- Blockchains table
CREATE TABLE blockchains (
    blockchain_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    symbol VARCHAR(20) NOT NULL,
    chain_id INTEGER UNIQUE,
    consensus_mechanism VARCHAR(50), -- PoW, PoS, DPoS, etc.
    block_time_seconds INTEGER,
    native_token VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active', -- active, deprecated, testnet
    launched_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE blockchains IS 'Blockchain networks where tokens exist';

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(200) UNIQUE NOT NULL,
    kyc_status VARCHAR(20) DEFAULT 'pending', -- pending, verified, rejected
    account_tier VARCHAR(20) DEFAULT 'basic', -- basic, premium, institutional
    country_code CHAR(2),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    total_trades INTEGER DEFAULT 0,
    total_volume_usd DECIMAL(20, 2) DEFAULT 0
);

COMMENT ON TABLE users IS 'Platform users and traders';

-- Tokens table (Main token information)
CREATE TABLE tokens (
    token_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE, -- Contract address or unique identifier
    name VARCHAR(200) NOT NULL,
    ticker VARCHAR(20) NOT NULL, -- BTC, ETH, USDT, etc.
    blockchain_id INTEGER REFERENCES blockchains(blockchain_id),
    token_type VARCHAR(50), -- native, erc20, erc721, bep20, spl, etc.
    total_supply DECIMAL(30, 8),
    circulating_supply DECIMAL(30, 8),
    max_supply DECIMAL(30, 8),
    decimals INTEGER DEFAULT 18,
    contract_address VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active', -- active, delisted, deprecated
    launch_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tokens IS 'Core token/cryptocurrency information';
COMMENT ON COLUMN tokens.code IS 'Unique token identifier or contract address';
COMMENT ON COLUMN tokens.ticker IS 'Trading symbol (BTC, ETH, etc.)';

-- Token metadata (additional info)
CREATE TABLE token_metadata (
    metadata_id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    description TEXT,
    website_url VARCHAR(500),
    whitepaper_url VARCHAR(500),
    github_url VARCHAR(500),
    twitter_handle VARCHAR(100),
    telegram_url VARCHAR(500),
    category VARCHAR(100), -- DeFi, NFT, Gaming, Infrastructure, etc.
    market_cap_rank INTEGER,
    coingecko_id VARCHAR(200),
    coinmarketcap_id VARCHAR(200),
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE token_metadata IS 'Extended token metadata and social links';

-- =====================================================
-- PRICE AND MARKET DATA TABLES
-- =====================================================

-- Token price history (OHLCV data)
CREATE TABLE token_price_history (
    price_history_id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(30, 8),
    volume_24h_usd DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4), -- Percentage
    interval VARCHAR(10) DEFAULT '1d', -- 1m, 5m, 15m, 1h, 4h, 1d, 1w
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_id, timestamp, interval)
);

COMMENT ON TABLE token_price_history IS 'Historical OHLCV (Open, High, Low, Close, Volume) price data';
COMMENT ON COLUMN token_price_history.interval IS 'Time interval: 1m, 5m, 15m, 1h, 4h, 1d, 1w';

-- Token volume (aggregated by exchange/date)
CREATE TABLE token_volume (
    volume_id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_volume DECIMAL(30, 8) NOT NULL,
    total_volume_usd DECIMAL(20, 2) NOT NULL,
    buy_volume DECIMAL(30, 8),
    sell_volume DECIMAL(30, 8),
    trade_count INTEGER DEFAULT 0,
    unique_traders INTEGER DEFAULT 0,
    average_trade_size DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(token_id, date)
);

COMMENT ON TABLE token_volume IS 'Daily aggregated trading volume by token';
COMMENT ON COLUMN token_volume.trade_count IS 'Number of trades executed';
COMMENT ON COLUMN token_volume.unique_traders IS 'Number of unique traders';

-- Token revenue (fees, rewards, etc.)
CREATE TABLE token_revenue (
    revenue_id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    revenue_type VARCHAR(50) NOT NULL, -- trading_fees, staking_rewards, transaction_fees, burn
    amount DECIMAL(30, 8) NOT NULL,
    amount_usd DECIMAL(20, 2),
    source VARCHAR(100), -- exchange name, protocol name, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE token_revenue IS 'Revenue generated from various token activities';
COMMENT ON COLUMN token_revenue.revenue_type IS 'Type: trading_fees, staking_rewards, transaction_fees, burn';

-- =====================================================
-- WALLET AND HOLDINGS TABLES
-- =====================================================

-- Wallets table
CREATE TABLE wallets (
    wallet_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    wallet_address VARCHAR(200) NOT NULL UNIQUE,
    blockchain_id INTEGER REFERENCES blockchains(blockchain_id),
    wallet_type VARCHAR(50) DEFAULT 'custodial', -- custodial, non-custodial, hardware, exchange
    label VARCHAR(200), -- User-defined label
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE wallets IS 'User cryptocurrency wallets';

-- Wallet balances (current holdings)
CREATE TABLE wallet_balances (
    balance_id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    balance DECIMAL(30, 8) NOT NULL DEFAULT 0,
    available_balance DECIMAL(30, 8) NOT NULL DEFAULT 0, -- Not locked in orders
    locked_balance DECIMAL(30, 8) NOT NULL DEFAULT 0, -- Locked in orders/staking
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(wallet_id, token_id)
);

COMMENT ON TABLE wallet_balances IS 'Current token balances per wallet';
COMMENT ON COLUMN wallet_balances.available_balance IS 'Balance available for trading';
COMMENT ON COLUMN wallet_balances.locked_balance IS 'Balance locked in orders or staking';

-- Token holdings (snapshot history for analytics)
CREATE TABLE token_holdings (
    holding_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_balance DECIMAL(30, 8) NOT NULL,
    balance_usd DECIMAL(20, 2),
    average_buy_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 2), -- Profit and Loss
    realized_pnl DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, token_id, snapshot_date)
);

COMMENT ON TABLE token_holdings IS 'Historical snapshot of user token holdings for analytics';
COMMENT ON COLUMN token_holdings.unrealized_pnl IS 'Unrealized profit/loss';
COMMENT ON COLUMN token_holdings.realized_pnl IS 'Realized profit/loss from sales';

-- =====================================================
-- EXCHANGE AND TRADING TABLES
-- =====================================================

-- Exchanges table
CREATE TABLE exchanges (
    exchange_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    type VARCHAR(50), -- centralized, decentralized, hybrid
    country VARCHAR(100),
    website_url VARCHAR(500),
    api_available BOOLEAN DEFAULT false,
    trading_fee_percentage DECIMAL(5, 4) DEFAULT 0.1,
    volume_24h_usd DECIMAL(20, 2),
    trust_score INTEGER, -- 1-10
    status VARCHAR(20) DEFAULT 'active', -- active, maintenance, closed
    launched_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE exchanges IS 'Cryptocurrency exchanges';

-- Exchange listings
CREATE TABLE exchange_listings (
    listing_id SERIAL PRIMARY KEY,
    exchange_id INTEGER REFERENCES exchanges(exchange_id) ON DELETE CASCADE,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    listing_date DATE NOT NULL,
    delisting_date DATE,
    is_active BOOLEAN DEFAULT true,
    volume_24h DECIMAL(30, 8),
    volume_24h_usd DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exchange_id, token_id)
);

COMMENT ON TABLE exchange_listings IS 'Tokens listed on exchanges';

-- Trading pairs
CREATE TABLE trading_pairs (
    pair_id SERIAL PRIMARY KEY,
    exchange_id INTEGER REFERENCES exchanges(exchange_id) ON DELETE CASCADE,
    base_token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    quote_token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    pair_symbol VARCHAR(50) NOT NULL, -- BTC/USDT, ETH/BTC, etc.
    current_price DECIMAL(20, 8),
    volume_24h DECIMAL(30, 8),
    volume_24h_usd DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4),
    bid_price DECIMAL(20, 8),
    ask_price DECIMAL(20, 8),
    spread_percentage DECIMAL(5, 4),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exchange_id, base_token_id, quote_token_id)
);

COMMENT ON TABLE trading_pairs IS 'Trading pairs available on exchanges';
COMMENT ON COLUMN trading_pairs.spread_percentage IS 'Bid-ask spread percentage';

-- Transactions table
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    from_wallet_id INTEGER REFERENCES wallets(wallet_id) ON DELETE SET NULL,
    to_wallet_id INTEGER REFERENCES wallets(wallet_id) ON DELETE SET NULL,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- buy, sell, transfer, swap, stake, unstake
    amount DECIMAL(30, 8) NOT NULL,
    price_per_token DECIMAL(20, 8),
    total_value_usd DECIMAL(20, 2),
    fee DECIMAL(20, 8),
    fee_usd DECIMAL(20, 2),
    transaction_hash VARCHAR(200) UNIQUE,
    blockchain_id INTEGER REFERENCES blockchains(blockchain_id),
    exchange_id INTEGER REFERENCES exchanges(exchange_id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'completed', -- pending, completed, failed, cancelled
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE transactions IS 'All cryptocurrency transactions';
COMMENT ON COLUMN transactions.transaction_type IS 'Type: buy, sell, transfer, swap, stake, unstake';

-- =====================================================
-- DEFI AND STAKING TABLES
-- =====================================================

-- Staking records
CREATE TABLE staking_records (
    staking_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    token_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    staked_amount DECIMAL(30, 8) NOT NULL,
    staking_period_days INTEGER, -- NULL for flexible staking
    apr_percentage DECIMAL(10, 4), -- Annual Percentage Rate
    rewards_earned DECIMAL(30, 8) DEFAULT 0,
    rewards_earned_usd DECIMAL(20, 2) DEFAULT 0,
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, withdrawn
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE staking_records IS 'Token staking records and rewards';
COMMENT ON COLUMN staking_records.apr_percentage IS 'Annual percentage rate for staking rewards';

-- Liquidity pools
CREATE TABLE liquidity_pools (
    pool_id SERIAL PRIMARY KEY,
    pool_name VARCHAR(200) NOT NULL,
    protocol VARCHAR(100), -- Uniswap, PancakeSwap, SushiSwap, etc.
    blockchain_id INTEGER REFERENCES blockchains(blockchain_id),
    token_a_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    token_b_id INTEGER REFERENCES tokens(token_id) ON DELETE CASCADE,
    token_a_reserve DECIMAL(30, 8),
    token_b_reserve DECIMAL(30, 8),
    total_liquidity_usd DECIMAL(20, 2),
    volume_24h_usd DECIMAL(20, 2),
    fee_percentage DECIMAL(5, 4) DEFAULT 0.3,
    apy_percentage DECIMAL(10, 4), -- Annual Percentage Yield
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE liquidity_pools IS 'DeFi liquidity pools';
COMMENT ON COLUMN liquidity_pools.apy_percentage IS 'Annual percentage yield';

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Token indexes
CREATE INDEX idx_tokens_ticker ON tokens(ticker);
CREATE INDEX idx_tokens_blockchain ON tokens(blockchain_id);
CREATE INDEX idx_tokens_status ON tokens(status);

-- Price history indexes
CREATE INDEX idx_price_history_token_timestamp ON token_price_history(token_id, timestamp DESC);
CREATE INDEX idx_price_history_timestamp ON token_price_history(timestamp DESC);
CREATE INDEX idx_price_history_interval ON token_price_history(interval);

-- Volume indexes
CREATE INDEX idx_volume_token_date ON token_volume(token_id, date DESC);
CREATE INDEX idx_volume_date ON token_volume(date DESC);

-- Holdings indexes
CREATE INDEX idx_holdings_user_token ON token_holdings(user_id, token_id);
CREATE INDEX idx_holdings_date ON token_holdings(snapshot_date DESC);

-- Transaction indexes
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_token ON transactions(token_id);
CREATE INDEX idx_transactions_hash ON transactions(transaction_hash);

-- Wallet indexes
CREATE INDEX idx_wallets_user ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(wallet_address);
CREATE INDEX idx_wallet_balances_wallet ON wallet_balances(wallet_id);

-- Trading pair indexes
CREATE INDEX idx_trading_pairs_exchange ON trading_pairs(exchange_id);
CREATE INDEX idx_trading_pairs_base_token ON trading_pairs(base_token_id);
CREATE INDEX idx_trading_pairs_active ON trading_pairs(is_active);

-- Staking indexes
CREATE INDEX idx_staking_user_token ON staking_records(user_id, token_id);
CREATE INDEX idx_staking_status ON staking_records(status);

-- =====================================================
-- ANALYTICAL VIEWS
-- =====================================================

-- Daily market summary view
CREATE OR REPLACE VIEW daily_market_summary AS
SELECT
    t.token_id,
    t.name,
    t.ticker,
    tph.timestamp::date as date,
    tph.open_price,
    tph.close_price,
    tph.high_price,
    tph.low_price,
    tph.volume_24h,
    tph.volume_24h_usd,
    tph.market_cap,
    tph.price_change_24h
FROM tokens t
JOIN token_price_history tph ON t.token_id = tph.token_id
WHERE tph.interval = '1d'
ORDER BY tph.timestamp DESC;

-- Token performance metrics
CREATE OR REPLACE VIEW token_performance_metrics AS
SELECT
    t.token_id,
    t.name,
    t.ticker,
    COUNT(DISTINCT tv.date) as trading_days,
    SUM(tv.total_volume_usd) as total_volume_usd,
    AVG(tv.total_volume_usd) as avg_daily_volume_usd,
    SUM(tv.trade_count) as total_trades,
    COUNT(DISTINCT th.user_id) as total_holders
FROM tokens t
LEFT JOIN token_volume tv ON t.token_id = tv.token_id
LEFT JOIN token_holdings th ON t.token_id = th.token_id
GROUP BY t.token_id, t.name, t.ticker;

-- User portfolio summary
CREATE OR REPLACE VIEW user_portfolio_summary AS
SELECT
    u.user_id,
    u.username,
    COUNT(DISTINCT th.token_id) as tokens_held,
    SUM(th.balance_usd) as total_portfolio_value_usd,
    SUM(th.unrealized_pnl) as total_unrealized_pnl,
    SUM(th.realized_pnl) as total_realized_pnl
FROM users u
LEFT JOIN token_holdings th ON u.user_id = th.user_id
WHERE th.snapshot_date = CURRENT_DATE
GROUP BY u.user_id, u.username;

-- Exchange trading volume
CREATE OR REPLACE VIEW exchange_volume_summary AS
SELECT
    e.exchange_id,
    e.name as exchange_name,
    e.type as exchange_type,
    COUNT(DISTINCT tp.pair_id) as trading_pairs_count,
    SUM(tp.volume_24h_usd) as total_volume_24h_usd,
    AVG(tp.spread_percentage) as avg_spread_percentage
FROM exchanges e
LEFT JOIN trading_pairs tp ON e.exchange_id = tp.exchange_id
WHERE tp.is_active = true
GROUP BY e.exchange_id, e.name, e.type;

-- Top tokens by market cap
CREATE OR REPLACE VIEW top_tokens_by_market_cap AS
SELECT
    t.token_id,
    t.name,
    t.ticker,
    t.circulating_supply,
    tph.close_price as current_price,
    tph.market_cap,
    tph.volume_24h_usd,
    tm.category,
    tm.market_cap_rank
FROM tokens t
JOIN token_price_history tph ON t.token_id = tph.token_id
LEFT JOIN token_metadata tm ON t.token_id = tm.token_id
WHERE tph.timestamp = (
    SELECT MAX(timestamp)
    FROM token_price_history
    WHERE token_id = t.token_id AND interval = '1d'
)
ORDER BY tph.market_cap DESC NULLS LAST;

COMMENT ON VIEW daily_market_summary IS 'Daily OHLCV summary for all tokens';
COMMENT ON VIEW token_performance_metrics IS 'Aggregated performance metrics per token';
COMMENT ON VIEW user_portfolio_summary IS 'User portfolio values and P&L';
COMMENT ON VIEW exchange_volume_summary IS 'Trading volume summary by exchange';
COMMENT ON VIEW top_tokens_by_market_cap IS 'Tokens ranked by market capitalization';
